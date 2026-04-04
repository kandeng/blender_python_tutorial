import { TransportInterface } from '../types';
import { WebSocketClient } from './websocket/client';

export class TransportFactory {
  static createTransport(config: any = {}): TransportInterface {
    // Read the configuration to determine which transport to use
    const transportType = config.transport_type || 'ws'; // Default to WebSocket
    
    console.log(`Initializing transport: ${transportType}`);
    
    switch (transportType.toLowerCase()) {
      case 'ws':
      case 'websocket':
        return new WebSocketClient(config.robot_url || 'ws://localhost:8080');
      case 'webrtc':
        // WebRTC requires native module compilation (wrtc/node-datachannel)
        // which is not currently available. Falling back to WebSocket.
        console.warn('WebRTC transport not available, falling back to WebSocket');
        return new WebSocketClient(config.robot_url || 'ws://localhost:8080');
      default:
        throw new Error(`Unsupported transport type: ${transportType}`);
    }
  }
}