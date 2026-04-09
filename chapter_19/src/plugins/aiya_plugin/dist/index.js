// src/index.ts
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";

// src/transport/websocket_client.ts
import WebSocket from "ws";
import { EventEmitter } from "events";
var AiyaWebSocketClient = class extends EventEmitter {
  ws = null;
  config;
  reconnectAttempts = 0;
  isHandshaked = false;
  connectionTimeout = null;
  constructor(config) {
    super();
    this.config = {
      reconnect_attempts: 10,
      reconnect_interval: 5e3,
      ...config
    };
  }
  /**
   * Initialize connection with dynamic URL construction
   */
  connect() {
    const fullUrl = this.buildConnectionUrl();
    console.log(`[AiyaWebSocket] Connecting to: ${fullUrl}`);
    this.ws = new WebSocket(fullUrl);
    this.setupEventHandlers();
  }
  /**
   * Build connection URL with query parameters
   */
  buildConnectionUrl() {
    const baseUrl = this.config.robot_url;
    const separator = baseUrl.includes("?") ? "&" : "?";
    return `${baseUrl}${separator}device-id=${encodeURIComponent(this.config.device_id)}&client-id=${encodeURIComponent(this.config.client_id)}`;
  }
  /**
   * Setup WebSocket event handlers
   */
  setupEventHandlers() {
    if (!this.ws) return;
    this.ws.on("open", () => {
      console.log("[AiyaWebSocket] Connection established");
      this.reconnectAttempts = 0;
      this.emit("connected");
      this.performHandshake();
    });
    this.ws.on("message", (data, isBinary) => {
      try {
        const text = data.toString();
        if (text.startsWith("{") || text.startsWith("[")) {
          const message = JSON.parse(text);
          this.handleMessage(message);
          return;
        }
      } catch {
      }
      const dataBuffer = Buffer.isBuffer(data) ? data : Buffer.from(data);
      if (isBinary || dataBuffer.length > 0 && dataBuffer[0] === 73) {
        this.emit("audio", dataBuffer);
        return;
      }
    });
    this.ws.on("close", (code, reason) => {
      console.log(`[AiyaWebSocket] Connection closed: code=${code}, reason=${reason.toString()}`);
      this.isHandshaked = false;
      this.emit("disconnected", { code, reason: reason.toString() });
      this.attemptReconnect();
    });
    this.ws.on("error", (error) => {
      console.error("[AiyaWebSocket] Connection error:", error.message);
      this.emit("error", error);
    });
    this.connectionTimeout = setTimeout(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) {
        console.error("[AiyaWebSocket] Connection timeout");
        this.ws?.terminate();
      }
    }, 1e4);
  }
  /**
   * Perform the Hello Handshake (Step 2)
   * Robot will not accept commands until this is received
   */
  performHandshake() {
    const handshakePayload = {
      type: "hello",
      version: 2,
      transport: "websocket",
      wake_up: "voice",
      source: "app",
      play_voice: true,
      features: {
        mcp: true
      },
      audio_params: {
        format: "mp3",
        sample_rate: 16e3,
        channels: 1,
        frame_duration: 60
      }
    };
    this.send(handshakePayload);
    console.log("[AiyaWebSocket] Hello handshake sent");
  }
  /**
   * Handle incoming messages from robot
   */
  handleMessage(message) {
    console.log("[AiyaWebSocket] Received:", JSON.stringify(message));
    switch (message.type) {
      case "hello":
        this.isHandshaked = true;
        console.log("[AiyaWebSocket] Handshake acknowledged by robot");
        this.emit("ready");
        break;
      case "hello_ack":
        this.isHandshaked = true;
        console.log("[AiyaWebSocket] Handshake acknowledged by robot");
        this.emit("ready");
        break;
      case "error":
        console.error("[AiyaWebSocket] Robot error:", message.error);
        this.emit("robot_error", message);
        break;
      case "response":
        this.emit("response", message);
        break;
      default:
        this.emit("message", message);
    }
  }
  /**
   * Send Listen command to robot (Step 3)
   */
  sendListenCommand(text) {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error("WebSocket not connected or handshake not complete"));
        return;
      }
      const payload = {
        type: "listen",
        mode: "manual",
        state: "detect",
        text
      };
      try {
        this.send(payload);
        console.log(`[AiyaWebSocket] Listen command sent: "${text}"`);
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }
  /**
   * Generic send method
   */
  send(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket not connected");
    }
    this.ws.send(JSON.stringify(data));
  }
  /**
   * Check if connected and handshaked
   */
  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN && this.isHandshaked;
  }
  /**
   * Attempt reconnection with exponential backoff
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.config.reconnect_attempts) {
      console.error("[AiyaWebSocket] Max reconnection attempts reached");
      this.emit("max_reconnect_attempts");
      return;
    }
    this.reconnectAttempts++;
    const delay = this.config.reconnect_interval * Math.pow(1.5, this.reconnectAttempts - 1);
    console.log(`[AiyaWebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.reconnect_attempts})`);
    setTimeout(() => {
      this.connect();
    }, Math.min(delay, 3e4));
  }
  /**
   * Gracefully close connection
   */
  disconnect() {
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
    }
    this.isHandshaked = false;
    this.ws?.close();
  }
};

// src/index.ts
var index_default = definePluginEntry({
  id: "aiya_plugin",
  name: "Aiya Robot Gateway Plugin",
  description: "Production-ready WebSocket gateway for Aiya physical robot",
  register(api) {
    const config = {
      robot_url: api.pluginConfig?.robot_url || "wss://test.e-inv.net.cn/aiya/v1/",
      device_id: api.pluginConfig?.device_id || "c8:5f:c1:31:c6:6d",
      client_id: api.pluginConfig?.client_id || "123456",
      reconnect_attempts: api.pluginConfig?.reconnect_attempts || 10,
      reconnect_interval: api.pluginConfig?.reconnect_interval || 5e3
    };
    const client = new AiyaWebSocketClient(config);
    let isReady = false;
    client.on("connected", () => {
      api.logger.info("[AiyaPlugin] WebSocket connected");
    });
    client.on("ready", () => {
      isReady = true;
      api.logger.info("[AiyaPlugin] Robot ready - handshake complete");
    });
    client.on("disconnected", (data) => {
      isReady = false;
      api.logger.warn(`[AiyaPlugin] Disconnected: ${data.reason} (code: ${data.code})`);
    });
    client.on("error", (error) => {
      api.logger.error(`[AiyaPlugin] WebSocket error: ${error.message}`);
    });
    client.on("robot_error", (error) => {
      api.logger.error(`[AiyaPlugin] Robot error: ${JSON.stringify(error)}`);
    });
    client.on("max_reconnect_attempts", () => {
      api.logger.error("[AiyaPlugin] Max reconnection attempts reached");
    });
    client.connect();
    const sendRobotCommandTool = {
      name: "send_robot_command",
      label: "Send Robot Command",
      description: "Sends a command to the Aiya physical robot via WebSocket. This tool allows the LLM to control the robot's movements and speech.",
      parameters: Type.Object({
        text: Type.String({
          description: "The instruction for the robot (e.g., 'Move forward', 'Wave your hand', 'Say hello')"
        })
      }),
      async execute(id, params) {
        console.log(`[AiyaPlugin] Command requested: "${params.text}"`);
        try {
          if (!isReady) {
            throw new Error("Robot is not connected or handshake not complete. Please try again in a moment.");
          }
          await client.sendListenCommand(params.text);
          console.log(`[AiyaPlugin] Command sent successfully: "${params.text}"`);
          return {
            content: [{
              type: "text",
              text: `Command "${params.text}" sent to Aiya robot successfully.`
            }],
            isError: false
          };
        } catch (error) {
          console.error(`[AiyaPlugin] Error sending command:`, error);
          return {
            content: [{
              type: "text",
              text: `Failed to send command: ${error.message}`
            }],
            isError: true
          };
        }
      }
    };
    api.registerTool(sendRobotCommandTool);
    api.logger.info(`[AiyaPlugin] Initialized with device_id=${config.device_id}, client_id=${config.client_id}`);
    api.logger.info('[AiyaPlugin] Tool "send_robot_command" registered');
    return {
      async destroy() {
        api.logger.info("[AiyaPlugin] Shutting down...");
        client.disconnect();
      }
    };
  }
});
export {
  index_default as default
};
//# sourceMappingURL=index.js.map