import WebSocket from 'ws';
import { EventEmitter } from 'events';

export interface SignalingMessage {
  type: string;
  payload: any;
  to?: string;
  from?: string;
}

export class SignalingClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private robotId: string;

  constructor(url: string, robotId: string) {
    super();
    this.url = url;
    this.robotId = robotId;
    this.connect();
  }

  private connect() {
    console.log(`Connecting to signaling server: ${this.url} for robot: ${this.robotId}`);
    
    this.ws = new WebSocket(this.url);

    this.ws.on('open', () => {
      console.log('Signaling connection established');
      // Register this client with the signaling server
      this.register();
    });

    this.ws.on('message', (data) => {
      try {
        const message: SignalingMessage = JSON.parse(data.toString());
        console.log('Received signaling message:', message);
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing signaling message:', error);
      }
    });

    this.ws.on('close', () => {
      console.log('Signaling connection closed');
      // Attempt to reconnect
      setTimeout(() => this.connect(), 5000);
    });

    this.ws.on('error', (error) => {
      console.error('Signaling connection error:', error);
    });
  }

  private register() {
    const registerMsg: SignalingMessage = {
      type: 'register',
      payload: { robotId: this.robotId },
      from: this.robotId
    };
    this.send(registerMsg);
  }

  private handleMessage(message: SignalingMessage) {
    switch (message.type) {
      case 'offer':
      case 'answer':
      case 'candidate':
        this.emit(message.type, message.payload);
        break;
      case 'registered':
        console.log('Successfully registered with signaling server');
        break;
      case 'error':
        console.error('Signaling server error:', message.payload);
        break;
      default:
        console.warn('Unknown signaling message type:', message.type);
    }
  }

  send(message: SignalingMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('Signaling connection not ready');
    }
  }
}