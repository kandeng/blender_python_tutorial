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
    <img alt="Openclaw has been successfully installed" src="./asset/openclaw_webchat.png" width="80%">
  </p>  
