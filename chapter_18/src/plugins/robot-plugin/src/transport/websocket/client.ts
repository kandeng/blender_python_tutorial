import WebSocket from 'ws';
import { TransportInterface, RobotActionParams } from '../../types';

export class WebSocketClient implements TransportInterface {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectInterval = 5000; // 5 seconds
  private connectionTimeout: NodeJS.Timeout | null = null;

  constructor(url: string) {
    this.url = url;
    this.connect();
  }

  private connect() {
    console.log(`Connecting to WebSocket server: ${this.url}`);
    
    this.ws = new WebSocket(this.url);

    this.ws.on('open', () => {
      console.log('WebSocket connection established');
      this.reconnectAttempts = 0; // Reset attempts on successful connection
    });

    this.ws.on('message', (data) => {
      console.log('Received message from robot:', data.toString());
    });

    this.ws.on('close', () => {
      console.log('WebSocket connection closed');
      this.attemptReconnect();
    });

    this.ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached. Giving up.');
    }
  }

  async sendAction(params: RobotActionParams): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        reject(new Error('WebSocket is not connected'));
        return;
      }

      try {
        const message = {
          type: 'robot_action',
          data: params.action,
          timestamp: new Date().toISOString(),
          original_query: params.message_query
        };

        this.ws.send(JSON.stringify(message), (error) => {
          if (error) {
            console.error('Error sending message via WebSocket:', error);
            reject(error);
          } else {
            console.log('Message sent to robot via WebSocket:', message);
            // For now, we'll just resolve immediately
            // In a real scenario, you'd wait for a response from the robot
            resolve({ success: true, sentAt: new Date().toISOString() });
          }
        });
      } catch (error) {
        console.error('Error preparing WebSocket message:', error);
        reject(error);
      }
    });
  }
}