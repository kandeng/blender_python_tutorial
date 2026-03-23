# Openclaw Skill and Plugin

## 1. Objective

This chapter is a step-by-step tutorial on how to install openclaw in a local Ubuntu laptop, 
and how to build custom skills, executing a python script directly, and indirectly in a docker sandbox.  


&nbsp;
## 2. Install Openclaw in local Ubuntu

### 2.1 Install nvm, node, npm and pnpm 

~~~
robot@robot-test:~$ pwd
/home/robot

robot@robot-test:~$ sudo apt update && sudo apt install -y curl wget

robot@robot-test:~$ curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash

robot@robot-test:~$ nvm install 24

robot@robot-test:~$ node -v 
  v24.14.0
robot@robot-test:~$ npm -v
  11.9.0
  
# Install pnpm
robot@robot-test:~$ curl -fsSL https://get.pnpm.io/install.sh | sh -
  
robot@robot-test:~$ which pnpm
  /home/claw_team/.local/share/pnpm/pnpm
~~~

&nbsp;
### 2.2 Install openclaw

Following [the official installation guide of openclaw](https://docs.openclaw.ai/install#npm-or-pnpm),
we use `npm` to install openclaw. 

Look into [the snapshot of the installation and configuration of `openclaw onboard --install-daemon`](./src/openclaw_onboard_daemon.txt) for details. 

Notice that after the installation and configuration, 
openclaw automatically created a system daemon service in user session for itself. 

The systemd service definition file is `/home/robot/.config/systemd/user/openclaw-gateway.service`.

The usage of this systemd service refers to the next section, including `start`, `stop`, `status`, and `reload`. 

~~~
robot@robot-test:~$ pwd
/home/robot

robot@robot-test:~$ npm install -g openclaw@latest
npm warn deprecated node-domexception@1.0.0: Use your platform's native DOMException instead
added 540 packages in 1m
89 packages are looking for funding
  run `npm fund` for details


robot@robot-test:~$ openclaw onboard --install-daemon
# Look into the snapshot of the installation for the installation details.
# The --user systemd service is stored at:
# /home/robot/.config/systemd/user/openclaw-gateway.service
~~~

In case openclaw has been installed and uninstalled beforehand, 
there may be multiple `openclaw` executable files. 

In the following case, previously we executed the command `curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard`, 
to install `openclaw`. 

Consequently, the previous openclaw executable is 
`/home/robot/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/openclaw.mjs`. 
  
And now we use `npm` to install `openclaw`, `npm install -g openclaw@latest`. 

Consequently, the current executable is `/home/linuxbrew/.linuxbrew/lib/node_modules/openclaw/openclaw.mjs`. 

~~~
robot@robot-test:~$ which openclaw
/home/linuxbrew/.linuxbrew/bin/openclaw

robot@robot-test:~$ ls -l /home/robot/.nvm/versions/node/v24.14.0/bin/openclaw
lrwxrwxrwx 1 robot robot 41 Mar 20 22:17 /home/robot/.nvm/versions/node/v24.14.0/bin/openclaw -> ../lib/node_modules/openclaw/openclaw.mjs

robot@robot-test:~$ ls -l /home/linuxbrew/.linuxbrew/bin/openclaw
lrwxrwxrwx 1 robot robot 41 Mar 23 00:36 /home/linuxbrew/.linuxbrew/bin/openclaw -> ../lib/node_modules/openclaw/openclaw.mjs
~~~

&nbsp;
### 2.3 Per-user instance of systemd manager

1. Edit [/home/robot/.config/systemd/user/openclaw-gateway.service](./src/openclaw-gateway.service#L8-L9),
   to comment off Restart and RestartSec.

2. Use `systemctl --user daemon-reload` to reload the systemd service.

3. User `systemctl --user {start, stop, status} openclaw-gateway.service` to `start`, `stop`, or look into the `status` of the systemd service.

Notice that `--user` flag is mandatory for the `openclaw-gateway.service`, because it is a *user* instance, instead of a *system-wide* instance. 

If using `sudo systemctl status openclaw-gateway.service`, the system will complain that `openclaw-gateway.service` cannot be found.

~~~
robot@robot-test:~/.openclaw$ systemctl --user stop openclaw-gateway.service
robot@robot-test:~/.openclaw$ pkill -f node
robot@robot-test:~/.openclaw$ pkill -f openclaw

robot@robot-test:~/.openclaw$ systemctl --user daemon-reload

robot@robot-test:~/.openclaw$ systemctl --user start openclaw-gateway.service

robot@robot-test:~/.openclaw$ systemctl --user status openclaw-gateway.service
● openclaw-gateway.service - OpenClaw Gateway (v2026.3.13)
     Loaded: loaded (/home/robot/.config/systemd/user/openclaw-gateway.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2026-03-23 10:59:01 CST; 2s ago
   Main PID: 576267 (openclaw-gatewa)
      Tasks: 31 (limit: 38029)
     Memory: 477.9M
        CPU: 3.947s
     CGroup: /user.slice/user-1000.slice/user@1000.service/app.slice/openclaw-gateway.service
             └─576267 openclaw-gateway "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" >

Mar 23 10:59:01 robot-test systemd[979]: Started OpenClaw Gateway (v2026.3.13).
lines 1-11/11 (END)


robot@robot-test:~/.openclaw$ sudo systemctl status openclaw-gateway.service
[sudo] password for robot: 
Unit openclaw-gateway.service could not be found.

robot@robot-test:~/.openclaw$ sudo systemctl --user status openclaw-gateway.service
Failed to connect to bus: $DBUS_SESSION_BUS_ADDRESS and $XDG_RUNTIME_DIR not defined (consider using --machine=<user>@.host --user to connect to bus of other user)

~~~

Open a chrome browser in the local ubuntu laptop, and visit `http://127.0.0.1:18789/`.

Following is a snapshot of the webchat, illustrating the successful outlook of the openclaw.

  <p align="center" vertical-align="top">
    <img alt="Openclaw has been successfully installed" src="./asset/openclaw_webchat.png" width="95%">
  </p>  


&nbsp;
## 3. Build managed local skill

In this section, we built a shared skills that runs a python script. 

This shared skill is named as *managed/local skill* in [Openclaw official document](https://docs.openclaw.ai/tools/skills#locations-and-precedence). 
It lives in a fixed directory, `~/.openclaw/skills`, and serves all agents on the same machine.


### 3.1 SKILL.md

In directory `~/.openclaw/skills`, we created a sub-directory [`hello-python`](./src/skills/hello-python) as following,

~~~
robot@robot-test:~/.openclaw$ pwd
/home/robot/.openclaw

robot@robot-test:~/.openclaw$ tree skills/
skills/
└── hello-python
    ├── scripts
    │   └── hello.py
    └── SKILL.md

2 directories, 2 files
~~~

Look into the content of [`SKILL.md`](./src/skills/hello-python/SKILL.md), there are several points worth noting.

* Following [Openclaw's official guide](https://docs.openclaw.ai/tools/skills#format-agentskills-+-pi-compatible),
   the [`metadata`](https://raw.githubusercontent.com/kandeng/blender_python_tutorial/refs/heads/main/chapter_16/src/skills/hello-python/SKILL.md#:~:text=metadata%3A%20%7B%22openclaw%22%3A%20%7B%22requires%22%3A%20%7B%22bins%22%3A%20%5B%22python3%22%5D%7D%7D%7D)
   should be a single-line JSON object.

* To support slash command, `user-invocable` must be set to `true`.

* To make sure that openclaw can find the `scripts/hello.py`, we must add the [`### Notes`](https://raw.githubusercontent.com/kandeng/blender_python_tutorial/refs/heads/main/chapter_16/src/skills/hello-python/SKILL.md#:~:text=%23%23%23%20Notes%3A%0A%2D%20Ensure%20that%20%60%7B%7BskillDir%7D%7D%60%20is%20correctly%20resolved%20to%20the%20absolute%20path%20of%20the%20skill%20directory.%0A%2D%20The%20script%20%60hello.py%60%20should%20be%20placed%20in%20the%20%60scripts%60%20sub%2Ddirectory%20within%20the%20skill%20directory.) in the `SKILL.md`.

* `skillDir` is a reserved word in Openclaw, referring to `/home/robot/.openclaw/skills/hello-python` in this case. 

  
~~~
---
name: hello-python
description: "Prints hello world using a Python script in a sub-directory."
metadata: {"openclaw": {"requires": {"bins": ["python3"]}}}
user-invocable: true
---

# Hello Python

When the user wants to run the hello world test:
1. Use `python3` to execute the script.
2. The script is located at: `{{skillDir}}/scripts/hello.py`
3. Pass the user's name as an argument.

### Usage Example:

- "Run the hello python skill"
- "Greet Kanbo using the python script"

### Command:
`python3 {{skillDir}}/scripts/hello.py "{{name}}"`

### Notes:
- Ensure that `{{skillDir}}` is correctly resolved to the absolute path of the skill directory.
- The script `hello.py` should be placed in the `scripts` sub-directory within the skill directory.
~~~


&nbsp;
### 3.2 openclaw.json

Look into the content of [`openclaw.json`](./src/openclaw.json), there are several points worth noting.

* For a single agent, use [`agents.defaults`](https://raw.githubusercontent.com/kandeng/blender_python_tutorial/refs/heads/main/chapter_16/src/openclaw.json#:~:text=%22agents%22,%22%3A%C2%A0%7B), instead of `agents.list[0].defaults`.  

* Since we don't use docker sandbox, [`agents.sandbox.mode` is set to `off`](https://raw.githubusercontent.com/kandeng/blender_python_tutorial/refs/heads/main/chapter_16/src/openclaw.json#:~:text=%22sandbox%22,%7D).

  Notice that `sandbox` is configured inside `agents`.

* Refer to [the official documentation of Openclaw](https://docs.openclaw.ai/tools/skills#locations-and-precedence),
  ~~~
  <workspace>/skills (highest) → ~/.openclaw/skills → bundled skills (lowest)
  ~~~
  the `workspace/skills` and `~/.openclaw/skills` directories are pre-defined, so that we don't need to configure them in [`skills.load`](https://raw.githubusercontent.com/kandeng/blender_python_tutorial/refs/heads/main/chapter_16/src/openclaw.json#:~:text=%22load%22,%7D%2C) again. 

* When [`skills.entries.hello-python.enabled`](https://raw.githubusercontent.com/kandeng/blender_python_tutorial/refs/heads/main/chapter_16/src/openclaw.json#:~:text=%22hello%2Dpython,%7D) is set to `true`,
  `hello-python` skill will be registered by openclaw to be `ready` to use, referring to [the screenshot](./asset/openclaw_skill_list.png) of the result of running command `openclaw skills list`.
  ~~~
   ✓ ready    │ 📦 hello-python    │ Prints hello world using a Python script in a sub-directory.  │ openclaw-managed 
  ~~~

  
~~~
{
  ...
  "agents": {
    "defaults": {
      "model": {
        "primary": "custom-dashscope-aliyuncs-com/qwen-max"
      },
      "models": {
        "custom-dashscope-aliyuncs-com/qwen-max": {
          "alias": "qwen-max"
        }
      },
      "workspace": "/home/robot/.openclaw/workspace",
      "sandbox": {
        "mode": "off",
        "scope": "agent"
      }
    }
  },
  "skills": {
    "load": {
      "watch": true,
      "watchDebounceMs": 250      
    },
    "entries": {
      "hello-python": {
        "enabled": true
      }
    }
  },
  ...
}
~~~

  <p align="center" vertical-align="top">
    <img alt="Openclaw skills list" src="./asset/openclaw_skill_list.png" width="95%">
  </p>  


&nbsp;
### 3.3 Test

To test the slash command, we can input "/hello-python 邓侃_2026.03.23.11:06" in the input box of the Openclaw's webchat. 

Interestingly, Openclaw automatically deleted the timestamp "2026.03.23.11:06" from the input argument. 

  <p align="center" vertical-align="top">
    <img alt="Openclaw skills list" src="./asset/openclaw_slash_skill.png" width="95%">
  </p>  


To test the intent usage of a skill, we can send a message "请用 hello-python skill，向邓侃问个好" in the Openclaw's webchat. 

Notice that if missing "请用 hello-python skill", simply say "向邓侃问个好", the `hello-python` skill will not be invoked. 

  <p align="center" vertical-align="top">
    <img alt="Openclaw skills list" src="./asset/openclaw_intent_skill.png" width="95%">
  </p>  
