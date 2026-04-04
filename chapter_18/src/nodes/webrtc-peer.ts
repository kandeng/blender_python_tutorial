import * as nodeDataChannel from 'node-datachannel';

// Simple signaling server for WebRTC negotiation
import WebSocket, { WebSocketServer } from 'ws';

// Map to store connected peers
const peers: Map<string, WebSocket> = new Map();
const wss = new WebSocketServer({ port: 3000 });

console.log('WebRTC Signaling Server running on port 3000');

wss.on('connection', (ws) => {
  console.log('New signaling client connected');

  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data.toString());
      console.log('Signaling message received:', message);

      // Handle registration
      if (message.type === 'register') {
        const robotId = message.payload.robotId;
        peers.set(robotId, ws);
        console.log(`Robot ${robotId} registered`);

        // Send confirmation back
        ws.send(JSON.stringify({ type: 'registered', payload: { robotId } }));
      }
      // Forward messages between clients
      else if (message.to) {
        const targetPeer = peers.get(message.to);
        if (targetPeer) {
          // Add sender info to message
          const forwardMsg = { ...message, from: message.from || 'unknown' };
          targetPeer.send(JSON.stringify(forwardMsg));
          console.log(`Forwarded message to ${message.to}`);
        } else {
          console.error(`Target peer ${message.to} not found`);
          // Send error back to sender
          ws.send(JSON.stringify({ 
            type: 'error', 
            payload: { message: `Target peer ${message.to} not found` } 
          }));
        }
      }
    } catch (error) {
      console.error('Error processing signaling message:', error);
    }
  });

  ws.on('close', () => {
    console.log('Signaling client disconnected');
    // Remove from peers map if it was registered
    for (const [id, peer] of peers.entries()) {
      if (peer === ws) {
        peers.delete(id);
        console.log(`Removed robot ${id} from registry`);
        break;
      }
    }
  });
});

// Create a mock robot peer that can receive WebRTC data
console.log('Starting mock WebRTC robot peer...');

// Note: In a real implementation, this would be a full WebRTC peer
// For this mock, we'll just simulate the data channel portion