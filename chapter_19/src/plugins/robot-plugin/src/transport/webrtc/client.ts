// import * as nodeDataChannel from 'node-datachannel';
import * as wrtc from 'wrtc';
import { TransportInterface, RobotActionParams } from '../../types';
import { SignalingClient, SignalingMessage } from './signaling';

export class WebRTCClient implements TransportInterface {
  private signalingClient: SignalingClient;
  private dataChannel: nodeDataChannel.DataChannel | null = null;
  private peerConnection: nodeDataChannel.PeerConnection | null = null;
  private signalingUrl: string;
  private robotId: string;

  constructor(signalingUrl: string, robotId: string) {
    this.signalingUrl = signalingUrl;
    this.robotId = robotId;
    
    // Initialize signaling client
    this.signalingClient = new SignalingClient(signalingUrl, robotId);
    
    // Set up event listeners for WebRTC signaling
    this.setupSignalingHandlers();
  }

  private setupSignalingHandlers() {
    // Handle incoming WebRTC offers
    this.signalingClient.on('offer', async (offer) => {
      await this.handleOffer(offer);
    });

    // Handle incoming ICE candidates
    this.signalingClient.on('candidate', (candidate) => {
      this.handleCandidate(candidate);
    });
  }

  private async handleOffer(offer: RTCSessionDescriptionInit) {
    console.log('Received offer from signaling server');

    // Create a new peer connection
    this.peerConnection = nodeDataChannel.PeerConnection('robot-' + this.robotId, {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }, // Public STUN server
        // Additional STUN/TURN servers would go here
      ]
    });

    // Set up data channel when the connection is established
    this.peerConnection.onDataChannel((dc) => {
      console.log('Data channel created');
      this.dataChannel = dc;
      
      dc.onOpen(() => {
        console.log('Data channel opened');
      });

      dc.onMessage((msg) => {
        console.log('Received message from robot via WebRTC:', msg);
      });
    });

    // Set the remote description
    await this.peerConnection.setRemoteDescription(offer);

    // Create an answer
    const answer = await this.peerConnection.createAnswer();
    await this.peerConnection.setLocalDescription(answer);

    // Send the answer back to the signaling server
    const answerMsg: SignalingMessage = {
      type: 'answer',
      payload: this.peerConnection.localDescription(),
      to: 'client' // Assuming the client initiated the connection
    };
    this.signalingClient.send(answerMsg);

    // Send any ICE candidates to the signaling server
    this.peerConnection.onIceCandidate((candidate) => {
      if (candidate) {
        const candidateMsg: SignalingMessage = {
          type: 'candidate',
          payload: candidate,
          to: 'client'
        };
        this.signalingClient.send(candidateMsg);
      }
    });
  }

  private handleCandidate(candidate: RTCIceCandidateInit) {
    if (this.peerConnection) {
      this.peerConnection.addIceCandidate(candidate);
    }
  }

  async sendAction(params: RobotActionParams): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.dataChannel) {
        reject(new Error('WebRTC data channel is not established'));
        return;
      }

      try {
        const message = {
          type: 'robot_action',
          data: params.action,
          timestamp: new Date().toISOString(),
          original_query: params.message_query
        };

        // Send the message via the WebRTC data channel
        this.dataChannel.send(JSON.stringify(message));

        console.log('Message sent to robot via WebRTC:', message);
        
        // For now, we'll just resolve immediately
        // In a real scenario, you'd wait for a response from the robot
        resolve({ success: true, sentAt: new Date().toISOString() });
      } catch (error) {
        console.error('Error sending message via WebRTC:', error);
        reject(error);
      }
    });
  }

  // Cleanup resources when the client is destroyed
  destroy() {
    if (this.dataChannel) {
      this.dataChannel.close();
    }
    if (this.peerConnection) {
      this.peerConnection.close();
    }
    if (this.signalingClient) {
      // Disconnect from signaling server
    }
  }
}