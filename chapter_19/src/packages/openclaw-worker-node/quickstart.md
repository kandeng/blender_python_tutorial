# OpenClaw Worker Node SDK - Quick Start

A TypeScript SDK for creating OpenClaw worker nodes that execute tools.

## Installation

```bash
npm install openclaw-worker-node
```

For Node.js 20-21, also install the WebSocket polyfill:

```bash
npm install openclaw-worker-node ws
```

## Prerequisites

1. **OpenClaw Gateway** must be running:

```bash
npm install -g openclaw
openclaw gateway start
```

2. **Device Identity** must be set up:

```bash
openclaw setup
```

This generates Ed25519 keys at `~/.openclaw/identity/device.json`.

3. **Gateway Token** - Get a pre-approved token:

```bash
openclaw gateway token
```

## Quick Example

```typescript
import { OpenclawWorkerNode, NodeResult } from "openclaw-worker-node";

// Create the worker node
const worker = new OpenclawWorkerNode({
  token: process.env.OPENCLAW_GATEWAY_TOKEN!,
  name: "my-worker",
  capabilities: ["custom"],
  commands: ["mytool.execute"],
});

// Handle tool execution requests
worker.on("tool.execute", async (payload) => {
  console.log("Received task:", payload.taskId);
  
  // Do your work here
  const result: NodeResult = {
    success: true,
    data: "processed",
  };
  
  // Send result back to gateway
  await worker.sendResult(payload.taskId!, result);
});

// Handle connection events
worker.on("connected", (info) => {
  console.log(`Connected to gateway (protocol v${info.protocol})`);
});

worker.on("error", (err) => {
  console.error("Worker error:", err.message);
});

// Connect and start
await worker.connect();
console.log("Worker ready!");
```

## Configuration Options

```typescript
const worker = new OpenclawWorkerNode({
  // Required
  token: string;              // Gateway auth token
  
  // Optional
  gatewayUrl?: string;        // Default: "ws://localhost:18789"
  name?: string;              // Worker name for logging (default: "worker")
  capabilities?: string[];    // Capabilities this worker provides
  commands?: string[];        // Commands this worker can execute
  identityPath?: string;      // Custom device identity path
  requestTimeout?: number;    // Request timeout in ms (default: 30000)
  autoReconnect?: boolean;    // Auto-reconnect on disconnect (default: true)
  maxReconnectAttempts?: number; // Max reconnect attempts (default: 10)
});
```

## Events

| Event | Handler | Description |
|-------|---------|-------------|
| `connected` | `(info: { protocol: number; methods: string[] }) => void` | Connected to gateway |
| `disconnected` | `(reason: { code: number; message: string }) => void` | Disconnected from gateway |
| `error` | `(error: Error) => void` | Connection error |
| `tool.execute` | `(payload: ToolExecutePayload) => void` | Tool execution request |
| `reconnecting` | `(attempt: number, maxAttempts: number) => void` | Reconnecting |

## Methods

| Method | Description |
|--------|-------------|
| `connect()` | Connect to the gateway |
| `disconnect()` | Disconnect from gateway |
| `sendResult(taskId, result)` | Send tool execution result |
| `sendEvent(event, payload)` | Send custom event |
| `sendRequest(method, params)` | Send raw protocol request |

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `isConnected` | `boolean` | Check if connected |
| `info` | `WorkerInfo` | Get worker info |

## Running a Worker

```bash
# Set environment variables
export OPENCLAW_GATEWAY_TOKEN=$(openclaw gateway token)

# Run the worker
npx tsx my-worker.ts
```

## Complete Example: Build123d Worker

See [examples/build123d-worker.ts](./examples/build123d-worker.ts) for a complete working example.

## Comparison with openclaw-node

| Feature | openclaw-node | openclaw-worker-node |
|---------|---------------|----------------------|
| Role | Client | Worker/Node |
| Purpose | Chat with agents | Execute tools |
| Authentication | Token only | Ed25519 signature + token |
| Receives | Agent responses | Tool execution requests |
| Use case | Apps that talk to AI | Backend workers |

## TypeScript Support

Full TypeScript types are included:

```typescript
import type {
  NodeResult,
  WorkerConfig,
  WorkerInfo,
  ToolExecutePayload,
  DeviceIdentity,
} from "openclaw-worker-node";
```

## License

MIT
