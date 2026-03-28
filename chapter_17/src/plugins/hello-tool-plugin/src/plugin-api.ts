/**
 * Type declarations matching the real OpenClaw plugin SDK.
 * These types mirror openclaw/plugin-sdk so that the plugin compiles
 * without importing the SDK at build time (it is provided at runtime).
 */

import type { TSchema } from "@sinclair/typebox";

// --- Logger ---
export interface PluginLogger {
  info(msg: string): void;
  warn(msg: string): void;
  error(msg: string): void;
}

// --- Config ---
export interface TransportConfig {
  mode: string;
  config: unknown;
}

export interface WebsocketConfig {
  url: string;
  reconnect: boolean;
  reconnectInterval: number;
}

// --- Services ---

export interface ServiceContext {
  config: Record<string, unknown>;
  stateDir: string;
  logger: PluginLogger;
}

export interface PluginService {
  id: string;
  start(ctx: ServiceContext): Promise<void>;
  stop?(ctx: ServiceContext): Promise<void>;
}


// --- Hooks ---

export type BeforeAgentStartHandler = (
  event: BeforeAgentStartEvent,
  ctx: BeforeAgentStartContext,
) => Promise<BeforeAgentStartResult | void> | BeforeAgentStartResult | void;

export interface BeforeToolCallEvent {
  toolName: string;
  params: Record<string, unknown>;
}


// --- Plugin API ---
export interface OpenclawPluginApi {
  pluginConfig?: Record<string, unknown>;
  logger: PluginLogger;

  registerService(service: PluginService): void;

  on(hookName: "[hello-tool-plugin] before_agent_start", handler: BeforeAgentStartHandler): void;
  on(hookName: "[hello-tool-plugin] before_tool_call", handler: BeforeToolCallHandler): void;
}


// --- Connection ---

export type ConnectionStatus = "disconnected" | "connecting" | "connected";

export type MessageHandler = (msg: Record<string, unknown>) => void;

export type ConnectionHandler = (status: ConnectionStatus) => void;

export interface RosTransport {
  /** Establish the transport connection. */
  connect(): Promise<void>;

  /** Gracefully close the transport connection. */
  disconnect(): Promise<void>;

  /** Get current connection status. */
  getStatus(): ConnectionStatus;

  /** Register a connection status change handler. Returns a cleanup function. */
  onConnection(handler: ConnectionHandler): () => void;
}