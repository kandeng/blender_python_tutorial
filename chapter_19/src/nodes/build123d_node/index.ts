#!/usr/bin/env node
/**
 * Build123d Worker Node
 * 
 * A distributed geometry generation worker that connects to the OpenClaw Gateway
 * and executes Build123d Python scripts inside Docker containers.
 * 
 * This node runs in an isolated process (optionally on a remote machine),
 * providing crash isolation for heavy CAD workloads.
 * 
 * Usage:
 *   OPENCLAW_GATEWAY_TOKEN=<token> npx tsx nodes/build123d_node/index.ts
 * 
 * Environment Variables:
 *   OPENCLAW_GATEWAY_TOKEN - Pre-approved token from gateway pairing
 *   OPENCLAW_GATEWAY_URL   - Gateway WebSocket URL (default: ws://localhost:18789)
 */

import { exec } from "child_process";
import { promisify } from "util";
import * as fs from "fs/promises";
import * as fsSync from "fs";
import * as path from "path";
import * as crypto from "crypto";
import { WebSocket } from "ws";

const execAsync = promisify(exec);

const DATA_DIR = "/tmp/build123d/data";
const CONTAINER_IMAGE = "gumyr/build123d:latest";

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
}

// Ed25519 key handling
interface DeviceIdentity {
  version: number;
  deviceId: string;
  publicKeyPem: string;
  privateKeyPem: string;
  createdAtMs: number;
}

interface DeviceAuth {
  version: number;
  deviceId: string;
  tokens: Record<string, { token: string; role: string; scopes: string[] }>;
}

// WebSocket protocol types
interface WSRequest {
  type: "req";
  id: string;
  method: string;
  params: Record<string, unknown>;
}

interface WSResponse {
  type: "res";
  id: string;
  ok: boolean;
  payload?: unknown;
  error?: { code: string; message: string };
}

interface WSEvent {
  type: "event";
  event: string;
  payload: unknown;
}

type WSMessage = WSRequest | WSResponse | WSEvent;

// Pending request tracking
const pendingRequests = new Map<string, {
  resolve: (response: WSResponse) => void;
  reject: (error: Error) => void;
  timeout: NodeJS.Timeout;
}>();

let requestCounter = 0;
let ws: WebSocket | null = null;
let deviceIdentity: DeviceIdentity | null = null;
let deviceAuth: DeviceAuth | null = null;

/**
 * Generate a unique request ID
 */
function generateRequestId(): string {
  return `${Date.now()}-${++requestCounter}`;
}

/**
 * Load device identity from disk
 */
async function loadDeviceIdentity(identityPath: string): Promise<DeviceIdentity | null> {
  try {
    const content = await fs.readFile(identityPath, "utf-8");
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * Load device auth from disk
 */
async function loadDeviceAuth(authPath: string): Promise<DeviceAuth | null> {
  try {
    const content = await fs.readFile(authPath, "utf-8");
    return JSON.parse(content);
  } catch {
    return null;
  }
}

/**
 * Sign a message with Ed25519 private key
 */
function signWithPrivateKey(privateKeyPem: string, message: string): string {
  const privateKey = crypto.createPrivateKey(privateKeyPem);
  const signature = crypto.sign(null, Buffer.from(message, "utf8"), privateKey);
  return signature.toString("base64url");
}

/**
 * Extract raw 32-byte Ed25519 public key from PEM
 */
function getPublicKeyRaw(publicKeyPem: string): string {
  const publicKey = crypto.createPublicKey({
    key: publicKeyPem,
    format: "pem",
    type: "spki"
  });
  
  // Export as DER and extract last 32 bytes (raw Ed25519 key)
  const der = publicKey.export({ format: "der", type: "spki" });
  const rawKey = der.slice(-32);
  return rawKey.toString("base64url");
}

/**
 * Build device auth payload v3 for signing
 * Format: v3|deviceId|clientId|clientMode|role|scopes|signedAtMs|token|nonce|platform|deviceFamily
 */
function buildDeviceAuthPayloadV3(params: {
  deviceId: string;
  clientId: string;
  clientMode: string;
  role: string;
  scopes: string[];
  signedAtMs: number;
  token: string;
  nonce: string;
  platform: string;
  deviceFamily?: string;
}): string {
  const scopes = params.scopes.join(",");
  const token = params.token ?? "";
  const platform = params.platform || "";
  const deviceFamily = params.deviceFamily || "";
  return [
    "v3",
    params.deviceId,
    params.clientId,
    params.clientMode,
    params.role,
    scopes,
    String(params.signedAtMs),
    token,
    params.nonce,
    platform,
    deviceFamily
  ].join("|");
}

/**
 * Send a request and wait for response
 */
function sendRequest(method: string, params: Record<string, unknown>, timeoutMs = 30000): Promise<WSResponse> {
  return new Promise((resolve, reject) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      reject(new Error("WebSocket not connected"));
      return;
    }

    const id = generateRequestId();
    const request: WSRequest = { type: "req", id, method, params };

    const timeout = setTimeout(() => {
      pendingRequests.delete(id);
      reject(new Error(`Request ${method} timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    pendingRequests.set(id, { resolve, reject, timeout });
    ws.send(JSON.stringify(request));
  });
}

/**
 * Handle incoming WebSocket message
 */
async function handleMessage(data: string): Promise<void> {
  let message: WSMessage;
  try {
    message = JSON.parse(data);
  } catch {
    console.error("Failed to parse message:", data);
    return;
  }

  if (message.type === "res") {
    const pending = pendingRequests.get(message.id);
    if (pending) {
      clearTimeout(pending.timeout);
      pendingRequests.delete(message.id);
      pending.resolve(message);
    }
  } else if (message.type === "event") {
    await handleEvent(message);
  }
}

/**
 * Handle incoming events
 */
async function handleEvent(event: WSEvent): Promise<void> {
  console.log(`Received event: ${event.event}`);

  // Handle tool execution requests from gateway
  if (event.event === "build123d.execute" || event.event === "tool.execute") {
    const payload = event.payload as any;
    const task: Build123dTask = payload?.task || payload;
    
    if (task?.script && task?.outputName) {
      console.log(`Executing build123d task`);
      
      const result = await executeBuild123d(task);
      
      // Send result back via tool.result
      try {
        await sendRequest("tool.result", {
          taskId: payload?.taskId || crypto.randomUUID(),
          result
        });
        console.log(`Task result sent to gateway`);
      } catch (err: any) {
        console.error(`Failed to send result:`, err.message);
      }
    }
  }
}

async function ensureDataDir(): Promise<void> {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function executeBuild123d(task: Build123dTask): Promise<Build123dResult> {
  const taskId = crypto.randomUUID();
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

    // Write script to file
    await fs.writeFile(scriptPath, script, "utf-8");
    console.log(`[${taskId}] Script written to: ${scriptPath}`);

    // Run Docker container
    const dockerCmd = [
      "docker run --rm",
      `-v ${DATA_DIR}:/data`,
      `--name build123d_${taskId}`,
      CONTAINER_IMAGE,
      `python3 /data/script_${taskId}.py`
    ].join(" ");

    console.log(`[${taskId}] Executing: ${dockerCmd}`);
    
    const { stdout, stderr } = await execAsync(dockerCmd, {
      timeout: 120000,
      maxBuffer: 10 * 1024 * 1024
    });

    console.log(`[${taskId}] Execution complete`);
    
    // Verify output file exists
    let outputExists = false;
    try {
      await fs.access(outputPath);
      outputExists = true;
      console.log(`[${taskId}] Output file created: ${outputPath}`);
    } catch {
      console.warn(`[${taskId}] Output file not found at: ${outputPath}`);
    }

    // Cleanup script file
    await fs.unlink(scriptPath).catch(() => {});

    return {
      success: true,
      outputPath: outputExists ? outputPath : undefined,
      stdout,
      stderr
    };
  } catch (err: any) {
    console.error(`[${taskId}] Execution failed:`, err.message);
    
    // Cleanup on error
    await fs.unlink(scriptPath).catch(() => {});

    return {
      success: false,
      error: err.message,
      stderr: err.stderr
    };
  }
}

/**
 * Connect to gateway with proper node authentication
 */
async function connectToGateway(url: string, token: string): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log(`Connecting to gateway: ${url}`);
    
    ws = new WebSocket(url);

    let challengeNonce: string | null = null;
    let challengeTs: number | null = null;

    ws.on("open", () => {
      console.log("WebSocket connection opened, waiting for challenge...");
    });

    ws.on("message", async (data: Buffer) => {
      try {
        const message = JSON.parse(data.toString());

        // Handle challenge event
        if (message.type === "event" && message.event === "connect.challenge") {
          challengeNonce = message.payload?.nonce;
          challengeTs = message.payload?.ts;
          console.log(`Received challenge, nonce: ${challengeNonce?.substring(0, 8)}...`);

          // Send connect request with node role
          if (!deviceIdentity) {
            reject(new Error("Device identity not loaded"));
            return;
          }

          // Build signed device auth payload
          const signedAtMs = Date.now();
          const clientId = "node-host";
          const clientMode = "node";
          const role = "node";
          const scopes: string[] = [];

          const payload = buildDeviceAuthPayloadV3({
            deviceId: deviceIdentity.deviceId,
            clientId,
            clientMode,
            role,
            scopes,
            signedAtMs,
            token,
            nonce: challengeNonce!,
            platform: process.platform
          });

          const signature = signWithPrivateKey(deviceIdentity.privateKeyPem, payload);
          const publicKeyRaw = getPublicKeyRaw(deviceIdentity.publicKeyPem);

          const connectParams = {
            minProtocol: 3,
            maxProtocol: 3,
            client: {
              id: clientId,
              version: "1.0.0",
              platform: process.platform,
              mode: clientMode
            },
            role,
            scopes,
            caps: ["docker", "build123d"],
            commands: ["build123d.execute"],
            permissions: {},
            auth: { token },
            locale: "en-US",
            userAgent: "build123d-node/1.0.0",
            device: {
              id: deviceIdentity.deviceId,
              publicKey: publicKeyRaw,
              signature,
              signedAt: signedAtMs,
              nonce: challengeNonce
            }
          };

          console.log(`Sending connect request as node...`);
          
          const response = await sendRequest("connect", connectParams, 10000);
          
          if (response.ok) {
            console.log("Connected to OpenClaw Gateway as node!");
            console.log(`Server protocol: ${(response.payload as any)?.protocol}`);
            const methods = (response.payload as any)?.features?.methods;
            if (methods) {
              console.log(`Available methods: ${methods.slice(0, 5).join(", ")}...`);
            }
            resolve();
          } else {
            console.error("Connect failed:", response.error);
            reject(new Error(`Connect failed: ${response.error?.message || "Unknown error"}`));
          }
          return;
        }

        // Handle other messages
        await handleMessage(data.toString());
        
      } catch (err: any) {
        console.error("Error handling message:", err.message);
      }
    });

    ws.on("error", (err) => {
      console.error("WebSocket error:", err.message);
      reject(err);
    });

    ws.on("close", (code, reason) => {
      console.log(`WebSocket closed: code=${code}, reason=${reason.toString()}`);
      ws = null;
    });

    // Timeout for initial connection
    setTimeout(() => {
      if (!challengeNonce) {
        reject(new Error("Timeout waiting for gateway challenge"));
      }
    }, 10000);
  });
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
  const gatewayUrl = process.env.OPENCLAW_GATEWAY_URL || "ws://localhost:18789";
  const token = process.env.OPENCLAW_GATEWAY_TOKEN;

  if (!token) {
    console.error("Error: OPENCLAW_GATEWAY_TOKEN environment variable is required");
    console.error("Get a pre-approved token from the gateway or use: openclaw gateway token");
    process.exit(1);
  }

  // Ensure data directory exists
  await ensureDataDir();

  // Load device identity
  const identityPath = path.join(process.env.HOME || "/root", ".openclaw/identity/device.json");
  deviceIdentity = await loadDeviceIdentity(identityPath);
  
  if (!deviceIdentity) {
    console.error("Error: Device identity not found at", identityPath);
    console.error("Run 'openclaw setup' first to generate device identity");
    process.exit(1);
  }

  console.log(`Build123d Worker Node starting...`);
  console.log(`Gateway URL: ${gatewayUrl}`);
  console.log(`Data directory: ${DATA_DIR}`);
  console.log(`Device ID: ${deviceIdentity.deviceId.substring(0, 16)}...`);

  try {
    await connectToGateway(gatewayUrl, token);
    console.log(`Build123d Worker Node is ready`);
    console.log(`Invoke via: openclaw nodes invoke --node build123d-generator --command build123d.execute`);

    // Keep the process running
    process.on("SIGINT", async () => {
      console.log("\nShutting down...");
      if (ws) ws.close();
      process.exit(0);
    });

    process.on("SIGTERM", async () => {
      console.log("\nShutting down...");
      if (ws) ws.close();
      process.exit(0);
    });

    // Keep alive
    await new Promise(() => {});

  } catch (err: any) {
    console.error("Failed to connect to gateway:", err.message);
    process.exit(1);
  }
}

// Run if executed directly (not imported)
const isMainModule = process.argv[1]?.includes("build123d_node");
if (isMainModule) {
  main().catch(console.error);
}

// Export for programmatic use
export { executeBuild123d, connectToGateway };
