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
        const { logger } = api;

        logger.info("**************************************************");
        logger.info("🚀 SUCCESS: [hello-tool-plugin] active for 邓侃 (Kan Deng)!");
        logger.info("Timestamp: 2026.03.28, 18:00");
        logger.info("**************************************************");

        // Register the rosbridge WebSocket connection as a managed service
        registerService(api);

        logger.info("[hello-tool-plugin] registerService loaded successfully");
    },
});
