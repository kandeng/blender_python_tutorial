"use strict";
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/index.ts
var index_exports = {};
__export(index_exports, {
  default: () => index_default
});
module.exports = __toCommonJS(index_exports);
var import_plugin_entry = require("openclaw/plugin-sdk/plugin-entry");
var import_typebox = require("@sinclair/typebox");

// src/transport/websocket/client.ts
var import_ws = __toESM(require("ws"), 1);
var WebSocketClient = class {
  constructor(url) {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectInterval = 5e3;
    // 5 seconds
    this.connectionTimeout = null;
    this.url = url;
    this.connect();
  }
  connect() {
    console.log(`Connecting to WebSocket server: ${this.url}`);
    this.ws = new import_ws.default(this.url);
    this.ws.on("open", () => {
      console.log("WebSocket connection established");
      this.reconnectAttempts = 0;
    });
    this.ws.on("message", (data) => {
      console.log("Received message from robot:", data.toString());
    });
    this.ws.on("close", () => {
      console.log("WebSocket connection closed");
      this.attemptReconnect();
    });
    this.ws.on("error", (error) => {
      console.error("WebSocket error:", error);
    });
  }
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error("Max reconnection attempts reached. Giving up.");
    }
  }
  async sendAction(params) {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== import_ws.default.OPEN) {
        reject(new Error("WebSocket is not connected"));
        return;
      }
      try {
        const message = {
          type: "robot_action",
          data: params.action,
          timestamp: (/* @__PURE__ */ new Date()).toISOString(),
          original_query: params.message_query
        };
        this.ws.send(JSON.stringify(message), (error) => {
          if (error) {
            console.error("Error sending message via WebSocket:", error);
            reject(error);
          } else {
            console.log("Message sent to robot via WebSocket:", message);
            resolve({ success: true, sentAt: (/* @__PURE__ */ new Date()).toISOString() });
          }
        });
      } catch (error) {
        console.error("Error preparing WebSocket message:", error);
        reject(error);
      }
    });
  }
};

// src/transport/factory.ts
var TransportFactory = class {
  static createTransport(config = {}) {
    const transportType = config.transport_type || "ws";
    console.log(`Initializing transport: ${transportType}`);
    switch (transportType.toLowerCase()) {
      case "ws":
      case "websocket":
        return new WebSocketClient(config.robot_url || "ws://localhost:8080");
      case "webrtc":
        console.warn("WebRTC transport not available, falling back to WebSocket");
        return new WebSocketClient(config.robot_url || "ws://localhost:8080");
      default:
        throw new Error(`Unsupported transport type: ${transportType}`);
    }
  }
};

// src/service.ts
var RobotService = class {
  constructor(config = {}) {
    this.transport = TransportFactory.createTransport(config);
  }
  async executeAction(params) {
    try {
      const result = await this.transport.sendAction(params);
      return result;
    } catch (error) {
      console.error("Error sending action to robot:", error);
      throw error;
    }
  }
};

// src/index.ts
var index_default = (0, import_plugin_entry.definePluginEntry)({
  id: "robot-plugin",
  name: "Robot Gateway Plugin",
  description: "Protocol-Agnostic Robot Gateway supporting WebSocket and WebRTC transports",
  register(api) {
    const robotService = new RobotService(api.config);
    const robotActionTool = {
      name: "robot_action",
      label: "Robot Controller",
      description: "Sends a command to the physical robot and returns a message to the user.",
      parameters: import_typebox.Type.Object({
        action: import_typebox.Type.Record(import_typebox.Type.String(), import_typebox.Type.Any()),
        // e.g., {"move": {"direction": "forward"}}
        message_query: import_typebox.Type.String(),
        // The raw user intent
        message_reply: import_typebox.Type.String()
        // The LLM's suggested response to the user
      }),
      async execute(id, params) {
        console.log(`[${(/* @__PURE__ */ new Date()).toISOString()}] Robot action requested:`, params);
        try {
          const result = await robotService.executeAction(params);
          console.log(`[${(/* @__PURE__ */ new Date()).toISOString()}] Action executed successfully:`, params.message_query);
          return {
            success: true,
            message: params.message_reply,
            details: { action: params.action, query: params.message_query },
            isError: false
          };
        } catch (error) {
          console.error(`[${(/* @__PURE__ */ new Date()).toISOString()}] Error executing robot action:`, error);
          return {
            success: false,
            message: `Failed to execute robot action: ${error.message}`,
            details: { action: params.action, query: params.message_query, error: error.message },
            isError: true
          };
        }
      }
    };
    api.registerTool(robotActionTool);
    api.logger.info(`[${(/* @__PURE__ */ new Date()).toISOString()}] Robot plugin initialized and registered`);
  }
});
//# sourceMappingURL=index.cjs.map