export interface RobotActionParams {
  action: Record<string, any>;
  message_query: string;
  message_reply: string;
}

export interface TransportInterface {
  sendAction(params: RobotActionParams): Promise<any>;
}