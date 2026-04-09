import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";
import { AiyaWebSocketClient, AiyaWebSocketConfig } from "./transport/websocket_client.js";

export default definePluginEntry({
  id: "aiya_plugin",
  name: "Aiya Robot Gateway Plugin",
  description: "Production-ready WebSocket gateway for Aiya physical robot",

  register(api: any) {
    // Extract configuration from plugin config
    const config: AiyaWebSocketConfig = {
      robot_url: api.pluginConfig?.robot_url || "wss://test.e-inv.net.cn/aiya/v1/",
      device_id: api.pluginConfig?.device_id || "c8:5f:c1:31:c6:6d",
      client_id: api.pluginConfig?.client_id || "123456",
      reconnect_attempts: api.pluginConfig?.reconnect_attempts || 10,
      reconnect_interval: api.pluginConfig?.reconnect_interval || 5000
    };

    // Initialize WebSocket client
    const client = new AiyaWebSocketClient(config);
    
    // Track connection state
    let isReady = false;

    // Setup event handlers
    client.on('connected', () => {
      api.logger.info('[AiyaPlugin] WebSocket connected');
    });

    client.on('ready', () => {
      isReady = true;
      api.logger.info('[AiyaPlugin] Robot ready - handshake complete');
    });

    client.on('disconnected', (data: { code: number; reason: string }) => {
      isReady = false;
      api.logger.warn(`[AiyaPlugin] Disconnected: ${data.reason} (code: ${data.code})`);
    });

    client.on('error', (error: Error) => {
      api.logger.error(`[AiyaPlugin] WebSocket error: ${error.message}`);
    });

    client.on('robot_error', (error: any) => {
      api.logger.error(`[AiyaPlugin] Robot error: ${JSON.stringify(error)}`);
    });

    client.on('max_reconnect_attempts', () => {
      api.logger.error('[AiyaPlugin] Max reconnection attempts reached');
    });

    // Start connection
    client.connect();

    // Register the send_robot_command tool
    const sendRobotCommandTool = {
      name: "send_robot_command",
      label: "Send Robot Command",
      description: "Sends a command to the Aiya physical robot via WebSocket. This tool allows the LLM to control the robot's movements and speech.",
      parameters: Type.Object({
        text: Type.String({ 
          description: "The instruction for the robot (e.g., 'Move forward', 'Wave your hand', 'Say hello')" 
        })
      }),
      async execute(id: string, params: { text: string }) {
        console.log(`[AiyaPlugin] Command requested: "${params.text}"`);

        try {
          // Check if robot is ready
          if (!isReady) {
            throw new Error('Robot is not connected or handshake not complete. Please try again in a moment.');
          }

          // Send the listen command to robot
          await client.sendListenCommand(params.text);

          console.log(`[AiyaPlugin] Command sent successfully: "${params.text}"`);

          return {
            content: [{
              type: "text" as const,
              text: `Command "${params.text}" sent to Aiya robot successfully.`
            }],
            isError: false
          };
        } catch (error: any) {
          console.error(`[AiyaPlugin] Error sending command:`, error);
          return {
            content: [{
              type: "text" as const,
              text: `Failed to send command: ${error.message}`
            }],
            isError: true
          };
        }
      }
    };

    // Register the tool
    api.registerTool(sendRobotCommandTool);

    // Log initialization
    api.logger.info(`[AiyaPlugin] Initialized with device_id=${config.device_id}, client_id=${config.client_id}`);
    api.logger.info('[AiyaPlugin] Tool "send_robot_command" registered');

    // Cleanup on plugin unload
    return {
      async destroy() {
        api.logger.info('[AiyaPlugin] Shutting down...');
        client.disconnect();
      }
    };
  }
});
