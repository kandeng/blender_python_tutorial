/**
 * OpenClaw Worker Node SDK - Worker Client
 * 
 * Main client class for connecting to OpenClaw Gateway as a worker node.
 */

import { EventEmitter } from "events";
import WebSocket from "ws";
import * as crypto from "crypto";
import {
  WorkerConfig,
  WorkerInfo,
  DeviceIdentity,
  WSRequest,
  WSResponse,
  WSEvent,
  ToolExecutePayload,
  NodeResult,
} from "./types.js";
import {
  loadDeviceIdentity,
  signWithPrivateKey,
  getPublicKeyRaw,
  buildDeviceAuthPayloadV3,
  getDefaultIdentityPath,
} from "./auth.js";

/**
 * OpenClaw Worker Node Client
 * 
 * Connects to an OpenClaw Gateway as a worker node that can execute tools.
 * 
 * @example
 * ```typescript
 * const worker = new OpenclawWorkerNode({
 *   token: process.env.OPENCLAW_GATEWAY_TOKEN,
 *   commands: ["mytool.execute"],
 * });
 * 
 * worker.on("tool.execute", async (payload) => {
 *   const result = await doWork(payload);
 *   await worker.sendResult(payload.taskId, result);
 * });
 * 
 * await worker.connect();
 * ```
 */
export class OpenclawWorkerNode extends EventEmitter {
  private config: Required<WorkerConfig>;
  private ws: WebSocket | null = null;
  private deviceIdentity: DeviceIdentity | null = null;
  private pendingRequests = new Map<string, {
    resolve: (response: WSResponse) => void;
    reject: (error: Error) => void;
    timeout: NodeJS.Timeout;
  }>();
  private requestCounter = 0;
  private reconnectAttempts = 0;
  private isConnecting = false;

  constructor(config: WorkerConfig) {
    super();
    this.config = {
      gatewayUrl: config.gatewayUrl || "ws://localhost:18789",
      token: config.token,
      name: config.name || "worker",
      capabilities: config.capabilities || [],
      commands: config.commands || [],
      identityPath: config.identityPath || getDefaultIdentityPath(),
      requestTimeout: config.requestTimeout || 30000,
      autoReconnect: config.autoReconnect ?? true,
      maxReconnectAttempts: config.maxReconnectAttempts || 10,
    };
  }

  /**
   * Get worker info
   */
  get info(): WorkerInfo {
    return {
      deviceId: this.deviceIdentity?.deviceId || "",
      connected: this.ws?.readyState === WebSocket.OPEN,
      capabilities: this.config.capabilities,
      commands: this.config.commands,
    };
  }

  /**
   * Check if connected to gateway
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Connect to the OpenClaw Gateway
   */
  async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    // Load device identity
    this.deviceIdentity = await loadDeviceIdentity(this.config.identityPath);
    if (!this.deviceIdentity) {
      throw new Error(
        `Device identity not found at ${this.config.identityPath}. ` +
        `Run 'openclaw setup' first to generate device identity.`
      );
    }

    this.isConnecting = true;
    this.reconnectAttempts = 0;

    return this.doConnect();
  }

  private async doConnect(): Promise<void> {
    return new Promise((resolve, reject) => {
      console.log(`[${this.config.name}] Connecting to gateway: ${this.config.gatewayUrl}`);

      this.ws = new WebSocket(this.config.gatewayUrl);

      let challengeNonce: string | null = null;
      const challengeTimeout = setTimeout(() => {
        if (!challengeNonce) {
          this.isConnecting = false;
          reject(new Error("Timeout waiting for gateway challenge"));
        }
      }, 10000);

      this.ws.on("open", () => {
        console.log(`[${this.config.name}] WebSocket opened, waiting for challenge...`);
      });

      this.ws.on("message", async (data: Buffer) => {
        try {
          const message = JSON.parse(data.toString());

          // Handle challenge event
          if (message.type === "event" && message.event === "connect.challenge") {
            clearTimeout(challengeTimeout);
            challengeNonce = message.payload?.nonce;
            console.log(`[${this.config.name}] Received challenge`);

            try {
              const connectResponse = await this.handleChallenge(challengeNonce!);
              
              if (connectResponse.ok) {
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                
                const payload = connectResponse.payload as any;
                this.emit("connected", {
                  protocol: payload?.protocol || 3,
                  methods: payload?.features?.methods || [],
                });
                
                console.log(`[${this.config.name}] Connected to gateway as node`);
                resolve();
              } else {
                this.isConnecting = false;
                reject(new Error(`Connect failed: ${connectResponse.error?.message}`));
              }
            } catch (err: any) {
              this.isConnecting = false;
              reject(err);
            }
            return;
          }

          // Handle other messages
          await this.handleMessage(data.toString());

        } catch (err: any) {
          console.error(`[${this.config.name}] Error handling message:`, err.message);
        }
      });

      this.ws.on("error", (err) => {
        clearTimeout(challengeTimeout);
        console.error(`[${this.config.name}] WebSocket error:`, err.message);
        this.emit("error", err);
        if (this.isConnecting) {
          this.isConnecting = false;
          reject(err);
        }
      });

      this.ws.on("close", (code, reason) => {
        clearTimeout(challengeTimeout);
        console.log(`[${this.config.name}] Disconnected: code=${code}, reason=${reason.toString()}`);
        this.emit("disconnected", { code, message: reason.toString() });
        this.ws = null;
        
        // Attempt reconnect if enabled
        if (this.config.autoReconnect && !this.isConnecting) {
          this.attemptReconnect();
        }
      });
    });
  }

  private async handleChallenge(nonce: string): Promise<WSResponse> {
    if (!this.deviceIdentity) {
      throw new Error("Device identity not loaded");
    }

    const signedAtMs = Date.now();
    const clientId = "node-host";  // Must be "node-host" for node connections
    const clientMode = "node";
    const role = "node";
    const scopes: string[] = [];

    // Build signed device auth payload
    const payload = buildDeviceAuthPayloadV3({
      deviceId: this.deviceIdentity.deviceId,
      clientId,
      clientMode,
      role,
      scopes,
      signedAtMs,
      token: this.config.token,
      nonce,
      platform: process.platform,
    });

    const signature = signWithPrivateKey(this.deviceIdentity.privateKeyPem, payload);
    const publicKeyRaw = getPublicKeyRaw(this.deviceIdentity.publicKeyPem);

    const connectParams = {
      minProtocol: 3,
      maxProtocol: 3,
      client: {
        id: clientId,
        version: "1.0.0",
        platform: process.platform,
        mode: clientMode,
      },
      role,
      scopes,
      caps: this.config.capabilities,
      commands: this.config.commands,
      permissions: {},
      auth: { token: this.config.token },
      locale: "en-US",
      userAgent: `${this.config.name}/1.0.0`,
      device: {
        id: this.deviceIdentity.deviceId,
        publicKey: publicKeyRaw,
        signature,
        signedAt: signedAtMs,
        nonce,
      },
    };

    return this.sendRequest("connect", connectParams, 10000);
  }

  private async handleMessage(data: string): Promise<void> {
    let message: WSRequest | WSResponse | WSEvent;
    try {
      message = JSON.parse(data);
    } catch {
      console.error(`[${this.config.name}] Failed to parse message:`, data);
      return;
    }

    if (message.type === "res") {
      const pending = this.pendingRequests.get(message.id);
      if (pending) {
        clearTimeout(pending.timeout);
        this.pendingRequests.delete(message.id);
        pending.resolve(message);
      }
    } else if (message.type === "event") {
      await this.handleEvent(message as WSEvent);
    }
  }

  private async handleEvent(event: WSEvent): Promise<void> {
    // Handle tool execution requests
    if (event.event === "tool.execute" || event.event.endsWith(".execute")) {
      const payload = event.payload as ToolExecutePayload;
      this.emit("tool.execute", payload);
    } else {
      // Emit other events for custom handling
      this.emit("event", event);
    }
  }

  /**
   * Send a request to the gateway and wait for response
   */
  sendRequest(method: string, params: Record<string, unknown>, timeoutMs?: number): Promise<WSResponse> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error("WebSocket not connected"));
        return;
      }

      const id = `${Date.now()}-${++this.requestCounter}`;
      const request: WSRequest = { type: "req", id, method, params };
      const timeout = timeoutMs ?? this.config.requestTimeout;

      const timer = setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error(`Request ${method} timed out after ${timeout}ms`));
      }, timeout);

      this.pendingRequests.set(id, { resolve, reject, timeout: timer });
      this.ws.send(JSON.stringify(request));
    });
  }

  /**
   * Send tool execution result back to gateway
   */
  async sendResult(taskId: string, result: NodeResult): Promise<void> {
    await this.sendRequest("tool.result", { taskId, result });
    console.log(`[${this.config.name}] Result sent for task ${taskId}`);
  }

  /**
   * Send a custom event to the gateway
   */
  async sendEvent(event: string, payload: unknown): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket not connected");
    }
    this.ws.send(JSON.stringify({ type: "event", event, payload }));
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error(`[${this.config.name}] Max reconnection attempts reached`);
      this.emit("error", new Error("Max reconnection attempts reached"));
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    
    console.log(`[${this.config.name}] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);
    this.emit("reconnecting", this.reconnectAttempts, this.config.maxReconnectAttempts);

    setTimeout(() => {
      this.doConnect().catch((err) => {
        console.error(`[${this.config.name}] Reconnect failed:`, err.message);
      });
    }, delay);
  }

  /**
   * Disconnect from gateway
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
