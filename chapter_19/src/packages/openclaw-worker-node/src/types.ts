/**
 * OpenClaw Worker Node SDK - Protocol Types
 * 
 * Type definitions for the OpenClaw Gateway node/worker protocol.
 */

// ============================================================================
// Device Identity & Authentication
// ============================================================================

export interface DeviceIdentity {
  version: number;
  deviceId: string;
  publicKeyPem: string;
  privateKeyPem: string;
  createdAtMs: number;
}

export interface DeviceAuth {
  version: number;
  deviceId: string;
  tokens: Record<string, { token: string; role: string; scopes: string[] }>;
}

// ============================================================================
// WebSocket Protocol Messages
// ============================================================================

export interface WSRequest {
  type: "req";
  id: string;
  method: string;
  params: Record<string, unknown>;
}

export interface WSResponse {
  type: "res";
  id: string;
  ok: boolean;
  payload?: unknown;
  error?: { code: string; message: string };
}

export interface WSEvent {
  type: "event";
  event: string;
  payload: unknown;
}

export type WSMessage = WSRequest | WSResponse | WSEvent;

// ============================================================================
// Tool Execution
// ============================================================================

export interface ToolExecutePayload {
  taskId?: string;
  task?: unknown;
  params?: Record<string, unknown>;
}

/**
 * Result returned from a node tool execution
 */
export interface NodeResult {
  success: boolean;
  [key: string]: unknown;
}

// ============================================================================
// Worker Configuration
// ============================================================================

export interface WorkerConfig {
  /** Gateway WebSocket URL (default: ws://localhost:18789) */
  gatewayUrl?: string;
  
  /** Pre-approved gateway token (from OPENCLAW_GATEWAY_TOKEN) */
  token: string;
  
  /** Worker name for logging */
  name?: string;
  
  /** Capabilities this worker provides */
  capabilities?: string[];
  
  /** Commands this worker can execute */
  commands?: string[];
  
  /** Custom identity file path */
  identityPath?: string;
  
  /** Request timeout in ms (default: 30000) */
  requestTimeout?: number;
  
  /** Reconnect on disconnect (default: true) */
  autoReconnect?: boolean;
  
  /** Max reconnection attempts (default: 10) */
  maxReconnectAttempts?: number;
}

export interface WorkerInfo {
  deviceId: string;
  connected: boolean;
  capabilities: string[];
  commands: string[];
}

// ============================================================================
// Event Types
// ============================================================================

export interface WorkerEvents {
  /** Connected to gateway */
  connected: (info: { protocol: number; methods: string[] }) => void;
  
  /** Disconnected from gateway */
  disconnected: (reason: { code: number; message: string }) => void;
  
  /** Connection error */
  error: (error: Error) => void;
  
  /** Tool execution request */
  'tool.execute': (payload: ToolExecutePayload) => void;
  
  /** Reconnecting */
  reconnecting: (attempt: number, maxAttempts: number) => void;
}

export type WorkerEventHandler<K extends keyof WorkerEvents> = WorkerEvents[K];
