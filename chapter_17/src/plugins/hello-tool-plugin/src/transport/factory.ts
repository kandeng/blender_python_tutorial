import type { TransportConfig, TransportOps } from "../plugin-api.ts";

export async function createTransport(config: TransportConfig): Promise<TransportOps> {
    switch (config.mode) {
        case "websocket": {
            const { WebsocketClient } = await import("./websocket_client.ts");

            console.log("**********************************************************");
            console.log("[hello-tool-plugin] in factory.ts createTransport() ")
            console.log("**********************************************************");

            return new WebsocketClient(config);
        }
    }
}