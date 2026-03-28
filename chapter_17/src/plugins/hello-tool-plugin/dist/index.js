import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';

var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __esm = (fn, res) => function __init() {
  return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// src/transport/websocket_client.ts
var websocket_client_exports = {};
__export(websocket_client_exports, {
  WebsocketClient: () => WebsocketClient
});
var WebsocketClient;
var init_websocket_client = __esm({
  "src/transport/websocket_client.ts"() {
    WebsocketClient = class {
      ws = null;
      options;
      constructor(config) {
        switch (config.mode) {
          case "websocket": {
            this.options = config.config;
          }
        }
      }
    };
  }
});

// src/transport/factory.ts
async function createTransport(config) {
  switch (config.mode) {
    case "websocket": {
      const { WebsocketClient: WebsocketClient2 } = await Promise.resolve().then(() => (init_websocket_client(), websocket_client_exports));
      return new WebsocketClient2(config);
    }
  }
}

// src/service.ts
var transport = null;
function registerService(api) {
  const wsconfig = {
    url: "ws://localhost:9090",
    reconnect: true,
    reconnectInterval: 3e3
  };
  api.registerService({
    id: "ros2-transport",
    async start(_ctx) {
      let transportCfg;
      transportCfg = { "mode": "websocket", "config": wsconfig };
      api.logger.info(`[hello-tool-plugin] Connecting to Node via ${transportCfg.mode} transport...`);
      transport = await createTransport(transportCfg);
      api.logger.info(`[hello-tool-plugin] transport connected (mode: ${transportCfg.mode})`);
    },
    async stop(_ctx) {
      if (transport) {
        await transport.disconnect();
        transport = null;
        api.logger.info("[hello-tool-plugin] transport disconnected");
      }
    }
  });
}

// src/index.ts
var index_default = definePluginEntry({
  id: "hello-tool-plugin",
  name: "Hello Tool Plugin",
  description: "A demo custom tool plugin of openclaw, to be called on intention.",
  register(api) {
    const { logger } = api;
    logger.info("**************************************************");
    logger.info("\u{1F680} SUCCESS: [hello-tool-plugin] active for \u9093\u4F83 (Kan Deng)!");
    logger.info("Timestamp: 2026.03.28, 18:00");
    logger.info("**************************************************");
    registerService(api);
    logger.info("[hello-tool-plugin] registerService loaded successfully");
  }
});

export { index_default as default };
//# sourceMappingURL=index.js.map
//# sourceMappingURL=index.js.map