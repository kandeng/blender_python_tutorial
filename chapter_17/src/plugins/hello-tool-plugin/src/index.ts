// index.ts
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { Type } from "@sinclair/typebox";
import type { OpenclawPluginApi } from "./plugin-api";
import { registerService } from "./service";

export default definePluginEntry({
    id: "hello-tool-plugin",
    name: "Hello Tool Plugin",
    description: "A demo custom tool plugin of openclaw, to be called on intention.",

    register(api) {
        const { logger, config, pluginConfig } = api;

        // console.log("Following is the content of api.config from 'openclaw.json': ")
        // console.log(JSON.stringify(config, null, 2)); 

        // console.log("Following is the content of api.config from 'openclaw.plugin.json': ")
        // console.log(JSON.stringify(pluginConfig, null, 2));  

        logger.info("\n**************************************************");
        logger.info("🚀 [hello-tool-plugin] the content of config.plugins.load");
        const plugin_load_str = JSON.stringify(config.plugins.load, null, 2)
        logger.info(` "openclaw.json" config.plugins.load: '${plugin_load_str}' `);
        logger.info("\n");
        
        logger.info("\n**************************************************");
        logger.info("⚠️ [hello-tool-plugin] the content of pluginConfig.nodeUrl");
        const plugin_nodeurl_str = JSON.stringify(pluginConfig.nodeUrl, null, 2)
        logger.info(` "openclaw.plugin.json" pluginConfig.nodeUrl: '${plugin_nodeurl_str}' `);
        logger.info("\n");
        
 
        // Register the rosbridge WebSocket connection as a manageind service
        registerService(api);

        logger.info("[hello-tool-plugin] registerService loaded successfully");
    },
});
