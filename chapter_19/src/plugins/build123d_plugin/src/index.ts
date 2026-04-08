/**
 * Build123d Plugin for OpenClaw
 * 
 * This plugin registers a tool that generates 3D geometry using Build123d.
 * It operates in two modes:
 * 
 * 1. **worker** mode (recommended): Delegates Docker execution to a separate
 *    build123d_node process. This provides:
 *    - Process isolation: CAD crashes don't affect the gateway
 *    - Resource isolation: Heavy geometry work in separate process
 *    - Distribution: Node can run on a remote machine
 * 
 * 2. **direct** mode (fallback): Runs Docker directly in the gateway process.
 *    Use only for development or when node is unavailable.
 * 
 * Configuration (openclaw.json):
 * ```json
 * "build123d_plugin": {
 *   "enabled": true,
 *   "config": {
 *     "mode": "worker",
 *     "nodeId": "build123d-generator"
 *   }
 * }
 * ```
 */

import { definePluginEntry, emptyPluginConfigSchema } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";
import { spawn, ChildProcess } from "child_process";
import { promisify } from "util";
import { exec } from "child_process";
import fs from "fs/promises";
import path from "path";
import { randomUUID } from "crypto";

const execAsync = promisify(exec);

const DATA_DIR = "/tmp/build123d/data";
const CONTAINER_IMAGE = "gumyr/build123d:latest";
const DEFAULT_NODE_ID = "build123d-generator";

interface Build123dConfig {
  mode?: "direct" | "worker";
  nodeId?: string;
  workerPath?: string;
}

interface Build123dTask {
  script: string;
  outputName: string;
}

interface Build123dResult {
  success: boolean;
  outputPath?: string;
  stdout?: string;
  stderr?: string;
  error?: string;
  message?: string;
}

// Track spawned worker processes
const workerProcesses = new Map<string, ChildProcess>();

async function ensureDataDir(): Promise<void> {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

/**
 * Execute build123d task directly via Docker (fallback mode).
 * This runs in the gateway process - use only for development.
 */
async function executeDirectDocker(task: Build123dTask, logger: any): Promise<Build123dResult> {
  const taskId = randomUUID();
  const scriptPath = path.join(DATA_DIR, `script_${taskId}.py`);
  const outputPath = path.join(DATA_DIR, task.outputName);

  try {
    // Ensure script has export_step
    let script = task.script;
    if (!script.includes("export_step")) {
      script += `\n\n# Auto-added export\nfrom build123d import export_step\nexport_step(part, "/data/${task.outputName}")\n`;
    } else {
      script = script.replace(/export_step\([^,]+,\s*['"][^'"]+['"]\)/g,
        `export_step(part, "/data/${task.outputName}")`);
    }

    await fs.writeFile(scriptPath, script, "utf-8");
    logger.info(`[${taskId}] Script written to: ${scriptPath}`);

    const dockerCmd = [
      "docker run --rm",
      `-v ${DATA_DIR}:/data`,
      CONTAINER_IMAGE,
      `python3 /data/script_${taskId}.py`
    ].join(" ");

    logger.info(`[${taskId}] Executing Docker command`);
    
    const { stdout, stderr } = await execAsync(dockerCmd, {
      timeout: 120000,
      maxBuffer: 10 * 1024 * 1024
    });

    // Verify output
    let outputExists = false;
    try {
      await fs.access(outputPath);
      outputExists = true;
    } catch {
      logger.warn(`[${taskId}] Output file not found at: ${outputPath}`);
    }

    await fs.unlink(scriptPath).catch(() => {});

    return {
      success: true,
      outputPath: outputExists ? outputPath : undefined,
      stdout,
      stderr,
      message: outputExists 
        ? `3D model generated successfully: ${outputPath}` 
        : "Script executed but output file not found"
    };
  } catch (err: any) {
    await fs.unlink(scriptPath).catch(() => {});
    return {
      success: false,
      error: err.message,
      stderr: err.stderr,
      message: `Failed to generate 3D model: ${err.message}`
    };
  }
}

export default definePluginEntry({
  id: "build123d_plugin",
  name: "Build123d Geometry Generator",
  description: "Generates 3D CAD models using Build123d Python scripts in Docker (with isolated worker node support)",
  configSchema: emptyPluginConfigSchema(),

  register(api) {
    const config: Build123dConfig = (api.pluginConfig as Build123dConfig) || {};
    const mode = config.mode || "worker";  // Default to worker mode for safety
    const nodeId = config.nodeId || DEFAULT_NODE_ID;

    // Ensure data directory exists on startup
    ensureDataDir().catch(err => {
      api.logger.error(`Failed to create data directory: ${err.message}`);
    });

    // Register the geometry generation tool
    api.registerTool({
      name: "generate_3d_geometry",
      label: "Generate 3D Geometry",
      description: `Generates a 3D CAD model using Build123d Python scripts executed in Docker.

This tool runs Python build123d scripts to create parametric 3D models. The output is a STEP file (.step).

Requirements for the script:
- Must define a variable named 'part' containing the 3D geometry
- Use build123d CAD operations (Box, Cylinder, extrude, subtract, etc.)
- The export_step call is auto-added if not present

Example script:
\`\`\`python
from build123d import *

# Create a box with a hole
part = Box(50, 50, 20) - Cylinder(10, 30)
\`\`\`

Execution mode: ${mode === "worker" ? "Isolated worker node (recommended)" : "Direct Docker (fallback)"}
`,
      parameters: Type.Object({
        script: Type.String({
          description: "Full Python build123d script. Must define 'part' variable with the geometry."
        }),
        outputName: Type.String({
          description: "Output filename (e.g., 'bracket.step'). Must end with .step or .stp"
        })
      }),
      
      async execute(_id, params) {
        const { script, outputName } = params;
        const startTime = Date.now();

        api.logger.info(`Build123d execute: mode=${mode}, outputName=${outputName}`);

        // Validate output name
        if (!outputName.endsWith(".step") && !outputName.endsWith(".stp")) {
          return {
            content: [{
              type: "text",
              text: "Error: outputName must end with .step or .stp"
            }],
            details: { error: "Invalid output name" },
            isError: true
          };
        }

        // Validate script has 'part' variable
        if (!script.includes("part") && !script.includes("Part")) {
          return {
            content: [{
              type: "text", 
              text: "Error: Script must define a 'part' variable containing the 3D geometry"
            }],
            details: { error: "Missing part variable in script" },
            isError: true
          };
        }

        try {
          let result: Build123dResult;

          if (mode === "worker") {
            // Delegate to worker node via gateway's node.invoke
            api.logger.info(`Delegating to worker node: ${nodeId}`);
            
            try {
              // Use the gateway's internal API to invoke the node
              // The plugin SDK provides access to gateway methods
              const invokeResult = await (api as any).invokeNode?.({
                node: nodeId,
                command: "build123d.execute",
                params: { script, outputName },
                timeout: 120000
              });
              
              if (invokeResult && typeof invokeResult === "object") {
                result = invokeResult as Build123dResult;
              } else {
                // Fallback to direct execution if node invocation fails
                api.logger.warn(`Node invoke returned unexpected result, falling back to direct mode`);
                result = await executeDirectDocker({ script, outputName }, api.logger);
              }
            } catch (invokeErr: any) {
              // If node is not available, fall back to direct execution
              api.logger.warn(`Node invoke failed: ${invokeErr.message}, falling back to direct mode`);
              result = await executeDirectDocker({ script, outputName }, api.logger);
            }
          } else {
            // Direct Docker execution (fallback mode)
            result = await executeDirectDocker({ script, outputName }, api.logger);
          }

          const duration = Date.now() - startTime;
          api.logger.info(`Build123d completed in ${duration}ms, success=${result.success}`);

          if (result.success) {
            const contents: Array<{ type: "text"; text: string }> = [
              { type: "text", text: result.message || "3D model generated successfully" },
              { type: "text", text: `Output file: ${result.outputPath}` }
            ];
            if (result.stdout) {
              contents.push({ type: "text", text: `Stdout:\n${result.stdout}` });
            }
            return {
              content: contents,
              details: {
                outputPath: result.outputPath,
                duration,
                stdout: result.stdout,
                stderr: result.stderr,
                mode
              },
              isError: false
            };
          } else {
            const contents: Array<{ type: "text"; text: string }> = [
              { type: "text", text: result.message || "Failed to generate 3D model" }
            ];
            if (result.stderr) {
              contents.push({ type: "text", text: `Stderr:\n${result.stderr}` });
            }
            return {
              content: contents,
              details: {
                error: result.error,
                duration,
                mode
              },
              isError: true
            };
          }
        } catch (err: any) {
          api.logger.error(`Build123d execution failed: ${err.message}`);
          return {
            content: [{ type: "text" as const, text: `Error: ${err.message}` }],
            details: { error: err.message },
            isError: true
          };
        }
      }
    });

    // Gateway lifecycle hooks for worker mode
    if (mode === "worker") {
      api.on("gateway_start", async (_event, _ctx) => {
        api.logger.info(`Build123d plugin initialized in worker mode (node: ${nodeId})`);
        api.logger.info(`Ensure the build123d_node is running: OPENCLAW_GATEWAY_TOKEN=<token> npx tsx nodes/build123d_node/index.ts`);
      });

      api.on("gateway_stop", async (_event, _ctx) => {
        api.logger.info("Gateway stopping - cleaning up any spawned workers");
        for (const [id, proc] of workerProcesses) {
          api.logger.info(`Killing worker process: ${id}`);
          proc.kill("SIGTERM");
        }
        workerProcesses.clear();
      });
    }

    api.logger.info(`Build123d plugin registered successfully (mode: ${mode})`);
  }
});
