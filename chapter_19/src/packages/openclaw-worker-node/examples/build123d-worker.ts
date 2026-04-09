#!/usr/bin/env node
/**
 * Build123d Worker Node - Using openclaw-worker-node SDK
 * 
 * This is a simplified version of the build123d_node using the SDK.
 * Compare this ~80 lines to the original ~530 lines!
 */

import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs/promises";
import * as path from "path";
import * as crypto from "crypto";
import { OpenclawWorkerNode, NodeResult } from "openclaw-worker-node";

const execAsync = promisify(exec);

const DATA_DIR = "/tmp/build123d/data";
const CONTAINER_IMAGE = "gumyr/build123d:latest";

interface Build123dTask {
  script: string;
  outputName: string;
}

async function ensureDataDir(): Promise<void> {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function executeBuild123d(task: Build123dTask): Promise<NodeResult> {
  const taskId = crypto.randomUUID();
  const scriptPath = path.join(DATA_DIR, `script_${taskId}.py`);
  const outputPath = path.join(DATA_DIR, task.outputName);

  try {
    let script = task.script;
    if (!script.includes("export_step")) {
      script += `\n\nfrom build123d import export_step\nexport_step(part, "/data/${task.outputName}")\n`;
    }

    await fs.writeFile(scriptPath, script, "utf-8");

    const dockerCmd = [
      "docker run --rm",
      `-v ${DATA_DIR}:/data`,
      `--name build123d_${taskId}`,
      CONTAINER_IMAGE,
      `python3 /data/script_${taskId}.py`
    ].join(" ");

    const { stdout, stderr } = await execAsync(dockerCmd, {
      timeout: 120000,
      maxBuffer: 10 * 1024 * 1024
    });

    let outputExists = false;
    try {
      await fs.access(outputPath);
      outputExists = true;
    } catch {}

    await fs.unlink(scriptPath).catch(() => {});
    return { success: true, outputPath: outputExists ? outputPath : undefined, stdout, stderr };
  } catch (err: any) {
    await fs.unlink(scriptPath).catch(() => {});
    return { success: false, error: err.message, stderr: err.stderr };
  }
}

async function main(): Promise<void> {
  const token = process.env.OPENCLAW_GATEWAY_TOKEN;
  if (!token) {
    console.error("Error: OPENCLAW_GATEWAY_TOKEN is required");
    process.exit(1);
  }

  await ensureDataDir();

  // Create worker using SDK - all the protocol complexity is handled!
  const worker = new OpenclawWorkerNode({
    token,
    name: "build123d-worker",
    capabilities: ["docker", "build123d"],
    commands: ["build123d.execute"],
  });

  // Handle tool execution requests
  worker.on("tool.execute", async (payload: any) => {
    const task: Build123dTask = payload?.task || payload;
    if (task?.script && task?.outputName) {
      console.log(`Executing build123d task...`);
      const result = await executeBuild123d(task);
      await worker.sendResult(payload?.taskId || crypto.randomUUID(), result);
    }
  });

  worker.on("connected", (info) => {
    console.log(`Connected to gateway (protocol v${info.protocol})`);
  });

  worker.on("error", (err) => {
    console.error("Worker error:", err.message);
  });

  await worker.connect();

  process.on("SIGINT", () => {
    worker.disconnect();
    process.exit(0);
  });

  await new Promise(() => {});
}

main().catch(console.error);
