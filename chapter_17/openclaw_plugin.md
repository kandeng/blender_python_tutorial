# Openclaw Plugin and Hook

## 1. Objective

This chapter is a step-by-step tutorial on how to build a custom plugin in a local Ubuntu laptop.  


&nbsp;
## 2. Build custom openclaw plugin

In this section, we built a custom agent plugin `hello-plugin`. 
If successful, the plugin name `hello-plugin` will be displayed in the openclaw plugin list, 
in addition, the running result of this plugin will also be displayed.

~~~
robot@robot-test:~/.openclaw$ openclaw plugins list
23:27:12 [plugins] **************************************************
23:27:12 [plugins] 🤖 邓侃: `hello-plugin` is now ACTIVE! 成功上线！
23:27:12 [plugins] Successfully bypassed SDK with named export.
23:27:12 [plugins] **************************************************

🦞 OpenClaw 2026.3.13 (61d171a) — I can't fix your code taste, but I can fix your build and your backlog.

Plugins (2/42 loaded)
Source roots:
  stock: /home/linuxbrew/.linuxbrew/lib/node_modules/openclaw/extensions

┌──────────────┬──────────┬──────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┬───────────┐
│ Name         │ ID       │ Status   │ Source                                                                                                                        │ Version   │
├──────────────┼──────────┼──────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┼───────────┤
│ @robot-test/ │ hello-   │ loaded   │ ~/.openclaw/plugins/hello-plugin/src/index.js                                                                                 │ 1.0.0     │
...
└──────────────┴──────────┴──────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┴───────────┘
23:27:12 [plugins] **************************************************
23:27:12 [plugins] 🤖 邓侃: `hello-plugin` is now ACTIVE! 成功上线！
23:27:12 [plugins] Successfully bypassed SDK with named export.
23:27:12 [plugins] **************************************************
~~~

The file structure is displayed as following. 

There are 4 files involved in this plugin, 
1. `openclaw.json`
2. `plugins/package.json`
3. `plugins/openclaw.plugin.json`
4. `plugins/src/index.js`

~~~
robot@robot-test:~$ pwd
/home/robot

robot@robot-test:~$ tree -L 1 .openclaw/
.openclaw/
├── agents
├── canvas
├── completions
├── cron
├── devices
├── identity
├── logs
├── openclaw.json
├── plugins
├── skills
├── update-check.json
└── workspace
10 directories, 2 files

robot@robot-test:~$ cd .openclaw/

robot@robot-test:~/.openclaw$ tree plugins/
plugins/
└── hello-plugin
    ├── openclaw.plugin.json
    ├── package.json
    └── src
        └── index.js

2 directories, 3 files
~~~


&nbsp;
### 2.1 package.json

Referring to [the openclaw official guide on `package.json`](https://docs.openclaw.ai/plugins/sdk-setup#package-metadata),
notice that

* `openclaw.extensions` specifies the filepath of `index.js`,

* the value of `type` must be `module`. 

~~~
{
  "name": "@robot-test/hello-plugin",
  "version": "1.0.0",
  "description": "A demo openclaw plugin",
  "license": "MIT",
  "author": "Kan Deng",
  "type": "module",
  "main": "src/index.js",
  "scripts": {
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "openclaw": {
    "extensions": [
      "./src/index.js"
    ]
  }
}
~~~


&nbsp;
### 2.2 openclaw.plugin.json

Referring to [the openclaw official guide on `package.json`](https://docs.openclaw.ai/plugins/sdk-setup#plugin-manifest),
notice that

* the value `id`, `hello-plugin` must be identical to the name of the subdirectory where the plugin package is stored,

  In this case, the full filepath of the plugin is `~/.openclaw/plugins/hello-plugin`

* `configSchema` is mandatory.

~~~
{
  "id": "hello-plugin",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {}
  }
}
~~~


&nbsp;
### 2.3 src/index.js

The first line of [the sample `index.js` script](https://docs.openclaw.ai/plugins/building-plugins#quick-start-tool-plugin) 
in the openclaw official documentation, is 
~~~
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
~~~

We tried to install the openclaw plugin package, by running `npm install @openclaw/sdk` and `npm install @openclaw/plugin-sdk`. 

However, both commands failed. 

~~~
robot@robot-test:~/.openclaw/plugins/hello-plugin$ npm install @openclaw/sdk
npm error code E404
npm error 404 Not Found - GET https://registry.npmjs.org/@openclaw%2fsdk - Not found
npm error 404
npm error 404  The requested resource '@openclaw/sdk@*' could not be found or you do not have permission to access it.
npm error 404
npm error 404 Note that you can also install from a
npm error 404 tarball, folder, http url, or git url.
npm error A complete log of this run can be found in: /home/robot/.npm/_logs/2026-03-24T16_32_33_113Z-debug-0.log


robot@robot-test:~/.openclaw/plugins/hello-plugin$ npm install @openclaw/plugin-sdk
npm error code E404
npm error 404 Not Found - GET https://registry.npmjs.org/@openclaw%2fplugin-sdk - Not found
npm error 404
npm error 404  The requested resource '@openclaw/plugin-sdk@*' could not be found or you do not have permission to access it.
npm error 404
npm error 404 Note that you can also install from a
npm error 404 tarball, folder, http url, or git url.
npm error A complete log of this run can be found in: /home/robot/.npm/_logs/2026-03-24T16_32_57_631Z-debug-0.log
~~~

One possible root cause is that, openclaw 2026.3 uses a *virtual SDK injection system*.

When the openclaw gateway starts, it creates a *virtual environment* for the plugins. 
We do not need to have the SDK files physically inside our `node_modules` directory for the plugin to run, 
because the openclaw gateway will provide the library for our plugin at the moment the gateway loads the plugin.

In addition, the `404` error code when installing the `@openclaw/plugin-sdk` package 
confirms that `@openclaw/plugin-sdk` is a private internal dependency that is bundled inside the openclaw gateway itself,
and `@openclaw/plugin-sdk` will be injected into the `node.js` process by the openclaw gateway at runtime.

Therefore, we remove the `import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry"` from our `index.js`. 

And explicitly name our exported function, 
so that the openclaw gateway knows how to *wake up* our plugin. 

~~~
// import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

export const activate = async (context) => {
    const { logger } = context;
    
    logger.info("**************************************************");
    logger.info("🤖 邓侃: `hello-plugin` is now ACTIVE! 成功上线！");
    logger.info("Successfully bypassed SDK with named export.");
    logger.info("**************************************************");
};

/**
 * Some internal versions of the gateway use 'register' as a fallback.
 * We export both to be 100% safe.
 */
export const register = activate;

// We also keep a default export just in case
export default { activate };
~~~


&nbsp;
### 2.4 openclaw.json

Referring to the openclaw 2026.3's official reference of 
[the plugin configuration in openclaw.json](https://docs.openclaw.ai/gateway/configuration-reference#plugins), 
we configured `hello-plugin` in `openclaw.json` as following. 

Notice that, we can also set `plugins.load.paths` as `["~/.openclaw/plugins"]`. 

Here, `~` refers to the home directory of the user, i.e. `/home/robot`. 

~~~
{
  ...
  "plugins": {
    "enabled": true,
    "allow": ["hello-plugin"],
    "load": { "paths": ["/home/robot/.openclaw/plugins"] },    
    "entries": {
      "hello-plugin": {
        "enabled": true
      }
    }
  },
  ...
}
~~~


&nbsp;
### 2.5 Test

./asset/openclaw_hello_plugin_follow.png
