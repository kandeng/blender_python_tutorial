# Nodes

This directory contains the core node scripts for the OpenClaw project.

## WebSocket Server

The `websocket-server.ts` file implements a mock robot WebSocket server that simulates communication with a robot. It listens for robot_action messages and sends back simulated responses.

### Installation

To install dependencies using pnpm:

```bash
pnpm install
```

### Building

To build the TypeScript files:

```bash
pnpm run build
```

This will compile the `websocket-server.ts` file to both CommonJS and ES Module formats in the `dist/` directory.

### Running

To run the WebSocket server directly:

```bash
node nodes/websocket-server.ts
```

Or using tsx:

```bash
npx tsx nodes/websocket-server.ts
```

The server will listen on port 8080 for incoming WebSocket connections.