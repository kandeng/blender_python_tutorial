import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';
import { Type } from '@sinclair/typebox';

// src/index.ts
var index_default = definePluginEntry({
  id: "qwen-tool-plugin",
  name: "Qwen Tool Plugin",
  description: "A plugin that sends 'hello qwen' message to the current user",
  register(api) {
    const { logger } = api;
    logger.info("[1] \u{1F680} [qwen-tool-plugin] inside register(api).");
    api.registerTool({
      name: "qwen_tool",
      label: "Qwen Tool",
      description: "Send a 'hello qwen' message to the current user",
      parameters: Type.Object({}),
      async execute(_id, params, context) {
        logger.info("Executing qwen_tool...");
        const params_str = JSON.stringify(params, null, 2);
        logger.info(`[3] \u{1F50D} [qwen-tool-plugin] Inside execute() params: 
"${params_str}"
`);
        logger.info(`[3] \u{1F50D} [qwen-tool-plugin] Inside execute() context: 
${JSON.stringify(context, null, 2)}
`);
        return {
          content: [{ type: "text", text: "hello \u5343\u95EE qwen" }],
          details: { message: "Successfully sent hello message" },
          isError: false
        };
      }
    });
    logger.info("[2] \u{1F517} [qwen-tool-plugin] register(api) completes.");
  }
});

export { index_default as default };
//# sourceMappingURL=index.js.map
//# sourceMappingURL=index.js.map