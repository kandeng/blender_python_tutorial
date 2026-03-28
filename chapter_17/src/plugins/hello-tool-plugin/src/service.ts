import { createTransport } from "./transport/factory.js";
import type { OpenclawPluginApi, PluginLogger } from "./plugin-api.js";
import type { TransportConfig, WebsocketConfig, TransportOps } from "../plugin-api.ts";

/** Shared transport instance for all tools. */
let transport: TransportOps | null = null;

/**
 * The service handles connection lifecycle (connect on start, disconnect on stop).
 */
export function registerService(api: OpenclawPluginApi): void {
    // Define websocket configuration with default values
    const wsconfig: WebsocketConfig = {
        url: "ws://localhost:9090",
        reconnect: true,
        reconnectInterval: 3000
    };

    api.registerService({
        id: "ros2-transport",

        async start(_ctx) {
            let transportCfg: TransportConfig;
            transportCfg = { "mode": "websocket", "config": wsconfig };

            api.logger.info(`[hello-tool-plugin] Connecting to Node via ${transportCfg.mode} transport...`);

            transport = await createTransport(transportCfg);

            /*
            transport.onConnection((status: string) => {
                api.logger.info(`[hello-tool-plugin] transport status: ${status}`);
            });

            await transport.connect();
            */

            api.logger.info(`[hello-tool-plugin] transport connected (mode: ${transportCfg.mode})`);
        },

        async stop(_ctx) {
            if (transport) {
                await transport.disconnect();
                transport = null;
                api.logger.info("[hello-tool-plugin] transport disconnected");
            }
        },
    });
}