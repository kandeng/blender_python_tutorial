/**
 * WebSocket Client Test Script
 * 
 * This script connects to the mock robot WebSocket server and tests the communication.
 * The server should be running on localhost:8080 before executing this script.
 * 
 * Installation and Usage with pnpm:
 * 1. Install dependencies using pnpm:
 *    pnpm install
 * 2. Build the project (optional but recommended):
 *    pnpm run build
 * 3. Make sure the WebSocket server is running:
 *    node nodes/websocket-server.ts

 * 4. Run this test script:
 *    node nodes/test-websocket-client.js
 * 
 * The script will:
 * - Connect to the WebSocket server
 * - Send a test message in the expected format
 * - Listen for and log the response from the server
 */

const WebSocket = require('ws');

// Connect to the WebSocket server
// const ws = new WebSocket('ws://localhost:8080');
const ws = new WebSocket('ws://ai.e-inv.net.cn:18080');

ws.on('open', function open() {
  console.log('Connected to WebSocket server');

  // Send a test message in the format expected by the server
  const testMessage = {
    type: 'robot_action',
    data: {
      move: { direction: 'forward' }
    },
    original_query: 'Move the robot forward'
  };

  console.log('Sending test message:', testMessage);
  ws.send(JSON.stringify(testMessage));
});

ws.on('message', function message(data) {
  console.log('Received response from server:', data.toString());
});

ws.on('close', function close() {
  console.log('Disconnected from server');
});

ws.on('error', function error(err) {
  console.error('WebSocket error:', err);
});