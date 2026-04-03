import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";

export default definePluginEntry({
    id: "qwen-tool-plugin",
    name: "Qwen Tool Plugin",
    description: "A plugin that sends 'hello qwen' message to the current user",

    register(api) {
        const { logger } = api;
        
        logger.info("🚀 Qwen Tool Plugin registered successfully");

        api.registerTool({
            name: "qwen_tool",
            label: "Qwen Tool",
            description: "Send a 'hello qwen' message to the current user",
            parameters: Type.Object({}),

            async execute(_id, params) {
                logger.info("Executing qwen_tool...");
                
                // Send a "hello qwen" text message to the current user
                return {
                    content: [{ type: "text", text: "hello qwen" }],
                    details: {},
                    isError: false
                };
            },
        });
    },
});