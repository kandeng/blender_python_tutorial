import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";

export default definePluginEntry({
    id: "qwen-tool-plugin",
    name: "Qwen Tool Plugin",
    description: "A plugin that sends 'hello qwen' message to the current user",

    register(api) {
        const { logger } = api;

        logger.info("[1] 🚀 [qwen-tool-plugin] inside register(api).");

        api.registerTool({
            name: "qwen_tool",
            label: "Qwen Tool",
            description: "Send a 'hello qwen' message to the current user",
            parameters: Type.Object({}),

            async execute(_id, params, context) {
                logger.info("Executing qwen_tool...");
                const params_str = JSON.stringify(params, null, 2);
                logger.info(`[3] 🔍 [qwen-tool-plugin] Inside execute() params: \n"${params_str}"\n`);
                
                // Log the context to understand what's available
                logger.info(`[3] 🔍 [qwen-tool-plugin] Inside execute() context: \n${JSON.stringify(context, null, 2)}\n`);

                // Send a "hello qwen" text message to the current user
                // The tool result will be included in the agent's response
                return {
                    content: [{ type: "text", text: "hello 千问 qwen" }],
                    details: { message: "Successfully sent hello message" },
                    isError: false
                };
            },
        });

        logger.info("[2] 🔗 [qwen-tool-plugin] register(api) completes.");
    },
});