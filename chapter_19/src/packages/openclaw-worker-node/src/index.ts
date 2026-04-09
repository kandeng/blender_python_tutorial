/**
 * OpenClaw Worker Node SDK
 * 
 * A TypeScript SDK for creating OpenClaw worker nodes that execute tools.
 * 
 * @packageDocumentation
 */

// Types
export type {
  DeviceIdentity,
  DeviceAuth,
  WSRequest,
  WSResponse,
  WSEvent,
  WSMessage,
  ToolExecutePayload,
  NodeResult,
  WorkerConfig,
  WorkerInfo,
  WorkerEvents,
  WorkerEventHandler,
} from "./types.js";

// Auth utilities
export {
  loadDeviceIdentity,
  loadDeviceAuth,
  signWithPrivateKey,
  getPublicKeyRaw,
  buildDeviceAuthPayloadV3,
  getDefaultIdentityPath,
  getDefaultAuthPath,
} from "./auth.js";

// Main client
export { OpenclawWorkerNode } from "./client.js";
