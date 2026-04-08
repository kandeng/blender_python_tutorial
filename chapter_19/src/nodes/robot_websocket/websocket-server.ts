/**
 * Mock Robot WebSocket Server
 * 
 * This script creates a mock WebSocket server that simulates communication
 * with a robot. It listens for robot_action messages and sends back
 * simulated responses.
 * 
 * Installation and Usage with pnpm:
 * 1. Install dependencies using pnpm:
 *    pnpm install
 * 2. Run the WebSocket server:
 *    node nodes/websocket-server.ts
 *    OR
 *    npx tsx nodes/websocket-server.ts
 * 
 * Optional: Build the project with pnpm before running:
 *    pnpm build
 * 
 * The server will:
 * - Listen for connections on port 8080
 * - Accept robot_action messages in the expected format
 * - Simulate processing and send back action_response messages
 */

import WebSocket, { WebSocketServer } from 'ws';

// Create WebSocket server listening on port 8080
const wss = new WebSocketServer({ port: 8080 });

console.log('Mock Robot WebSocket Server running on port 8080');

wss.on('connection', (ws) => {
  console.log('Robot connected to mock server');

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data.toString());
      console.log('Received from robot client:', message);

      // Log the action received
      if (message.type === 'robot_action') {
        console.log(`Action received:`, message.data);
        console.log(`Original query:`, message.original_query);
        
        // Echo back a simulated response after a short delay
        setTimeout(() => {
          const response = {
            type: 'action_response',
            status: 'executed',
            action: message.data,
            timestamp: new Date().toISOString()
          };
          
          ws.send(JSON.stringify(response));
          console.log('Sent response back to client:', response);
        }, 1000);
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  });

  ws.on('close', () => {
    console.log('Robot disconnected from mock server');
  });

  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});