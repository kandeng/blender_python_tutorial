import WebSocket from 'ws';
import { EventEmitter } from 'events';

export interface AiyaWebSocketConfig {
  robot_url: string;
  device_id: string;
  client_id: string;
  reconnect_attempts?: number;
  reconnect_interval?: number;
}

export interface HelloHandshakePayload {
  type: "hello";
  version: number;
  transport: string;
  wake_up: string;
  source: string;
  play_voice: boolean;
  features: {
    mcp: boolean;
  };
  audio_params: {
    format: string;
    sample_rate: number;
    channels: number;
    frame_duration: number;
  };
}

export interface ListenCommandPayload {
  type: "listen";
  mode: string;
  state: string;
  text: string;
}

export class AiyaWebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: AiyaWebSocketConfig;
  private reconnectAttempts = 0;
  private isHandshaked = false;
  private connectionTimeout: NodeJS.Timeout | null = null;

  constructor(config: AiyaWebSocketConfig) {
    super();
    this.config = {
      reconnect_attempts: 10,
      reconnect_interval: 5000,
      ...config
    };
  }

  /**
   * Initialize connection with dynamic URL construction
   */
  connect(): void {
    const fullUrl = this.buildConnectionUrl();
    console.log(`[AiyaWebSocket] Connecting to: ${fullUrl}`);
    
    this.ws = new WebSocket(fullUrl);
    this.setupEventHandlers();
  }

  /**
   * Build connection URL with query parameters
   */
  private buildConnectionUrl(): string {
    const baseUrl = this.config.robot_url;
    const separator = baseUrl.includes('?') ? '&' : '?';
    return `${baseUrl}${separator}device-id=${encodeURIComponent(this.config.device_id)}&client-id=${encodeURIComponent(this.config.client_id)}`;
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.on('open', () => {
      console.log('[AiyaWebSocket] Connection established');
      this.reconnectAttempts = 0;
      this.emit('connected');
      this.performHandshake();
    });

    this.ws.on('message', (data: WebSocket.Data, isBinary: boolean) => {
      // Try to parse as JSON first (text messages)
      // If it's valid JSON, it's a control message, not audio
      try {
        const text = data.toString();
        // Quick check: JSON must start with { or [
        if (text.startsWith('{') || text.startsWith('[')) {
          const message = JSON.parse(text);
          this.handleMessage(message);
          return;
        }
      } catch {
        // Not valid JSON
      }
      
      // Binary audio data (MP3) - ID3 header indicates MP3 format
      const dataBuffer = Buffer.isBuffer(data) ? data : Buffer.from(data as string);
      if (isBinary || dataBuffer.length > 0 && dataBuffer[0] === 0x49) { // 'I' for ID3
        // Binary audio frame from robot - emit for audio processing if needed
        this.emit('audio', dataBuffer);
        return;
      }
    });

    this.ws.on('close', (code: number, reason: Buffer) => {
      console.log(`[AiyaWebSocket] Connection closed: code=${code}, reason=${reason.toString()}`);
      this.isHandshaked = false;
      this.emit('disconnected', { code, reason: reason.toString() });
      this.attemptReconnect();
    });

    this.ws.on('error', (error: Error) => {
      console.error('[AiyaWebSocket] Connection error:', error.message);
      this.emit('error', error);
    });

    // Connection timeout
    this.connectionTimeout = setTimeout(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) {
        console.error('[AiyaWebSocket] Connection timeout');
        this.ws?.terminate();
      }
    }, 10000);
  }

  /**
   * Perform the Hello Handshake (Step 2)
   * Robot will not accept commands until this is received
   */
  private performHandshake(): void {
    const handshakePayload: HelloHandshakePayload = {
      type: "hello",
      version: 2,
      transport: "websocket",
      wake_up: "voice",
      source: "app",
      play_voice: true,
      features: {
        mcp: true
      },
      audio_params: {
        format: "mp3",
        sample_rate: 16000,
        channels: 1,
        frame_duration: 60
      }
    };

    this.send(handshakePayload);
    console.log('[AiyaWebSocket] Hello handshake sent');
  }

  /**
   * Handle incoming messages from robot
   */
  private handleMessage(message: any): void {
    console.log('[AiyaWebSocket] Received:', JSON.stringify(message));

    switch (message.type) {
      case 'hello':
        // Server sends 'hello' back as acknowledgement
        this.isHandshaked = true;
        console.log('[AiyaWebSocket] Handshake acknowledged by robot');
        this.emit('ready');
        break;
      
      case 'hello_ack':
        // Alternative acknowledgement format
        this.isHandshaked = true;
        console.log('[AiyaWebSocket] Handshake acknowledged by robot');
        this.emit('ready');
        break;
      
      case 'error':
        console.error('[AiyaWebSocket] Robot error:', message.error);
        this.emit('robot_error', message);
        break;
      
      case 'response':
        this.emit('response', message);
        break;
      
      default:
        this.emit('message', message);
    }
  }

  /**
   * Send Listen command to robot (Step 3)
   */
  sendListenCommand(text: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.isConnected()) {
        reject(new Error('WebSocket not connected or handshake not complete'));
        return;
      }

      const payload: ListenCommandPayload = {
        type: "listen",
        mode: "manual",
        state: "detect",
        text: text
      };

      try {
        this.send(payload);
        console.log(`[AiyaWebSocket] Listen command sent: "${text}"`);
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Generic send method
   */
  private send(data: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }
    this.ws.send(JSON.stringify(data));
  }

  /**
   * Check if connected and handshaked
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN && this.isHandshaked;
  }

  /**
   * Attempt reconnection with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.reconnect_attempts!) {
      console.error('[AiyaWebSocket] Max reconnection attempts reached');
      this.emit('max_reconnect_attempts');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnect_interval! * Math.pow(1.5, this.reconnectAttempts - 1);
    
    console.log(`[AiyaWebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.config.reconnect_attempts})`);
    
    setTimeout(() => {
      this.connect();
    }, Math.min(delay, 30000)); // Cap at 30 seconds
  }

  /**
   * Gracefully close connection
   */
  disconnect(): void {
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
    }
    this.isHandshaked = false;
    this.ws?.close();
  }
}
