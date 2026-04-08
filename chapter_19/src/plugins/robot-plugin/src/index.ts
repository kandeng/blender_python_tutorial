import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";
import { RobotService } from './service';

export default definePluginEntry({
  id: "robot-plugin",
  name: "Robot Gateway Plugin",
  description: "Protocol-Agnostic Robot Gateway supporting WebSocket and WebRTC transports",

  register(api) {
    // Initialize the robot service with plugin config
    const robotService = new RobotService(api.config);

    // Define the tool configuration separately to avoid type issues during compilation
    const robotActionTool = {
      name: "robot_action",
      label: "Robot Controller",
      description: "Sends a command to the physical robot and returns a message to the user.",
      parameters: Type.Object({
        action: Type.Record(Type.String(), Type.Any()), // e.g., {"move": {"direction": "forward"}}
        message_query: Type.String(),                   // The raw user intent
        message_reply: Type.String()                    // The LLM's suggested response to the user
      }),
      async execute(id: string, params: any) {
        console.log(`[${new Date().toISOString()}] Robot action requested:`, params);

        try {
          // Pass params to service which handles transport selection
          const result = await robotService.executeAction(params);

          // Log the intent
          console.log(`[${new Date().toISOString()}] Action executed successfully:`, params.message_query);

          return {
            success: true,
            message: params.message_reply,
            details: { action: params.action, query: params.message_query },
            isError: false
          };
        } catch (error: any) {
          console.error(`[${new Date().toISOString()}] Error executing robot action:`, error);
          return {
            success: false,
            message: `Failed to execute robot action: ${error.message}`,
            details: { action: params.action, query: params.message_query, error: error.message },
            isError: true
          };
        }
      }
    };

    // Register the robot action tool using the api object
    api.registerTool(robotActionTool);
    
    // Log when the plugin becomes active
    api.logger.info(`[${new Date().toISOString()}] Robot plugin initialized and registered`);
  }
});
