import { TransportFactory } from './transport/factory';
import { RobotActionParams } from './types';

export class RobotService {
  private transport;

  constructor(config: any = {}) {
    // Initialize the transport based on configuration
    this.transport = TransportFactory.createTransport(config);
  }

  async executeAction(params: RobotActionParams) {
    try {
      // Send the action to the robot via the selected transport
      const result = await this.transport.sendAction(params);
      return result;
    } catch (error) {
      console.error('Error sending action to robot:', error);
      throw error;
    }
  }
}