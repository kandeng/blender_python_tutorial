import WebSocket from "ws";
import type { TransportConfig, WebsocketConfig, TransportOps } from "../plugin-api.ts";

/**
 * WebSocket client to handle connection lifecycle, reconnection, and message routing.
 */
export class WebsocketClient {
    private ws: WebSocket | null = null;
    private options: Required<WebsocketConfig>;

    constructor(config: TransportConfig) {
        if (config.mode === "websocket") {
            this.options = config.config;
            console.log("**********************************************************");
            console.log("[hello-tool-plugin] in websocket_client.ts constructor() ")
            console.log("**********************************************************");

        };
    };
}