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



### 2.1 package.json

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

~~~
// src/index.js

/**
 * OpenClaw 2026.3 looks for a named export called 'activate' 
 * if it doesn't find the SDK wrapper.
 */
export const activate = async (context) => {
    const { logger } = context;
    
    logger.info("**************************************************");
    logger.info("🤖 邓侃: `hello-plugin` is now ACTIVE! 成功上线！");
    logger.info("Successfully bypassed SDK with named export.");
    logger.info("**************************************************");

    // This is where you'd register tools or hooks later
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

