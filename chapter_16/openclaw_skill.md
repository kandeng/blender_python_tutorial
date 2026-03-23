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
double check if the executable files are identical. 

In the following case, the previous openclaw executable is 
`/home/robot/.nvm/versions/node/v24.14.0/bin/openclaw`,
  
and the current executable is 
`/home/linuxbrew/.linuxbrew/bin/openclaw`. 

However, both of these two executables are soft links, pointing to the same executable, 
`/home/robot/.nvm/versions/node/v24.14.0/lib/node_modules/openclaw/openclaw.mjs`. 

~~~
robot@robot-test:~$ which openclaw
/home/linuxbrew/.linuxbrew/bin/openclaw

robot@robot-test:~$ ls -l /home/robot/.nvm/versions/node/v24.14.0/bin/openclaw
lrwxrwxrwx 1 robot robot 41 Mar 20 22:17 /home/robot/.nvm/versions/node/v24.14.0/bin/openclaw -> ../lib/node_modules/openclaw/openclaw.mjs

robot@robot-test:~$ ls -l /home/linuxbrew/.linuxbrew/bin/openclaw
lrwxrwxrwx 1 robot robot 41 Mar 23 00:36 /home/linuxbrew/.linuxbrew/bin/openclaw -> ../lib/node_modules/openclaw/openclaw.mjs
~~~
