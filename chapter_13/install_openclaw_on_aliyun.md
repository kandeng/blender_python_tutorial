# Install Openclaw on Alibaba Cloud

## 1. Object

[Openclaw](https://github.com/openclaw/openclaw) is more than just a personal AI assistant, 
it’s a robust hub that seamlessly integrates powerful tools into a single ecosystem.

If you're looking to build a custom AI agent service, 
Openclaw serves as a versatile framework that can be deployed to any major cloud provider, 
such as AWS or Alibaba Cloud.

The most straightforward way to get Openclaw running on an Alibaba ECS instance 
is via their Simple Application Server (轻量应用服务器).

However, because the Simple Application Server is a tightly coupled environment, 
it may lack the flexibility required for extensive custom development.

The most robust solution to install Openclaw on an Alibaba ECS instance from scratch. 

Additionally, we plan to integrate Chinese LLMs with Openclaw, 
including `Qwen-turbo` and `Kimi-K2.5`, via `DashScope` AI model provider. 
This allows us to simplify the billing process by paying in RMB.


&nbsp;
## 2. Outline

We took the following steps, and successfully installed Openclaw on an Alibaba's ECS instance. 

1. Create a regular user

   While it is possible to install OpenClaw as the root user,
   Alibaba Cloud disables root password authentication by default for security reasons. 
  
   This restriction prevents direct SSH access from a local machine.

   Furthermore, managing OpenClaw requires establishing a SSH tunnel
   to access the web interface at "http://127.0.0.1:18789/" locally. 
  
   Since root-level restrictions interfere with setting up this tunnel, we recommend creating a standard user (e.g., clawer) with password. 
  
   Installing Openclaw under this regular user ensures a smoother deployment and remote management experience.
  
2. Setup github proxy

   Due to network restrictions, Alibaba Cloud ECS instances located in mainland China regions cannot access github directly.

   To ensure a smooth installation of Openclaw and its dependencies, we recommend configuring a github proxy.

3. Install node and npm

   Installation requires Node.js v22.0 or higher.

   Since we deploy Openclaw on an ECS instance within China, direct github access may be unreliable.

   Our solution is to use a Chinia mirror to download the necessary Node.js packages.
   
4. Install brew

   To ensure a smooth installation of Openclaw and its dependencies, it is better to install [`brew`](https://brew.sh/).

   Again, we need to use a Chinia mirror to download the `brew` package.

5. Install Openclaw

   Install Openclaw as a skeleton, without configuring the AI models that it uses,
   without configuring the Instant Messaging apps that it uses.

6. Get AI provider's apiKey

   We use Alibaba's `DashScope` that has been renamed to `BaiLian` recently as the AI model provider.

   In order to remotely use the AI model via `DashScope`, we need to get our dashscope's api-key.

7. Configure the AI models that Openclaw uses

   We will configure `Qwen-turbo` and `Kimi-K2.5`, via `DashScope` AI model provider.
   
   Additionally, we will set the authentication token for Openclaw gateway, e.g. `clawer_gateway_auth_token`.

   OpenClaw Gateway enables token-based authentication by default
   to restrict unauthorized access to your AI agent/gateway service running on `127.0.0.1:18789`.

   Once the token of the Openclaw's gateway has been configured,
   e.g. `clawer_gateway_auth_token`,
   we can use the token either in the URL or in the HTTP header.

   * URL example:

     ~~~
     http://127.0.0.1:18789/chat?session=main&token=clawer_gateway_auth_token
     ~~~

   * HTTP header example:
  
     ~~~
     Authorization: Bearer clawer_gateway_auth_token
     ~~~
   

8. Configure the Instant Messaging apps that Openclaw uses

   We will configure `Dingding` (钉钉) and `Feishu`（飞书),
   that are not in channel list supported by the Openclaw installation script.

9. Configure the network security group

   We will configure the network security group, so that the port `18789` of the Openclaw gateway can be accessed.
  
10. Set up the SSH tunnel
  
    We set up the SSH tunnel from the Alibaba cloud ECS instance to our local computer,
    so that we can visit the webpages of the Openclaw from the `localhost` of our local computer.

    Notice that even though we have openned the port `18789` of the Openclaw's gateway,
    we cannot visit the Openclaw's webpage directly via `http://<alibaba_ecs_public_ip>:18789/`.

11. Start and stop Openclaw gateway


&nbsp;
## 3. Preparation

### 3.1 Create a non-root user

Suppose we create a non-root user `clawer` with password `clawer_password`. 

~~~
root# useradd -m -s /usr/bin/bash clawer
root# passwd clawer    # clawer_password
root# usermod -aG sudo clawer
~~~

After creating the new user `clawer`, we switch from user `root` to user `clawer`. 

~~~
root# su - clawer
      To run a command as administrator (user "root"), use "sudo <command>".
      See "man sudo_root" for details.

clawer$
~~~

### 3.2 Setup github proxy

The github proxy may not always be functional. However, it doesn't hurt to set it up.

~~~
# Install nscd, and refresh DNS buffer.
clawer$ sudo apt install -y nscd

# Download the latest hosts of github520, and add them to the system's hosts.
clawer$ sudo curl -sSL https://raw.hellogithub.com/hosts >> /etc/hosts

# Refresh DNS buffer.
clawer$ sudo systemctl restart nscd
~~~

### 3.3 Install Nodejs, NPM and NVM

1. Update and install the tools:
   
   ~~~
   clawer$ sudo apt update && sudo apt install -y curl wget
   ~~~

2. Install the latest version of nodejs, plus npm and nvm:

   Follow the instruction in `https://nodejs.org/en/download`,
   to download and install the latest version of nodejs.

   In case you cannot access the official website of nodejs, 
   try the China's mirror site `https://nodejs.cn/`.

3. To verify if the installation is successful:

   ~~~
   clawer$ node -v 
           v24.13.0
   clawer$ npm -v 
           11.6.2
   ~~~

### 3.4 Install brew

1. Download brew install.sh

   1.1 Manually download the brew install.sh from github to our local computer.
       https://github.com/Homebrew/install/blob/main/install.sh

   1.2 Manually Upload brew install.sh to `brew-install.sh` to alibaba ECS instance.

   1.3 Copy the uploaded `brew-install.sh` to `/home/clawer` directory.
   
   ~~~
   clawer$ sudo cp /root/robot/brew-install.sh .
   clawer$ ls -l brew-install.sh 
           -rw-rw-r-- 1 clawer clawer 32814 Feb  5 22:14 brew-install.sh
   ~~~

2. Setup the environmental variables

   ~~~
   clawer$ export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/homebrew-core.git"
   
   clawer$ export HOMEBREW_BOTTLE_DOMAIN="https://mirrors.aliyun.com/homebrew-bottles"
   ~~~

3. Install brew

   ~~~
   clawer$ bash brew-install.sh
           ==> Checking for `sudo` access (which may request your password)...
           ==> This script will install:
               /home/linuxbrew/.linuxbrew/bin/brew
               ...
               /home/linuxbrew/.linuxbrew/Frameworks
           ==> HOMEBREW_CORE_GIT_REMOTE is set to a non-default URL:
           https://mirrors.aliyun.com/homebrew/homebrew-core.git will be used as the Homebrew/homebrew-core Git remote.

           Press RETURN/ENTER to continue or any other key to abort:
           ==> /usr/bin/sudo /usr/bin/install -d -o clawer -g clawer -m 0755 /home/linuxbrew/.linuxbrew
   ~~~

4. Add `brew` to system `PATH`

   ~~~
   clawer$ which brew   # So far, brew is not yet in PATH
   
   clawer$ echo >> /home/clawer/.bashrc
   
   clawer$ echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"' >> /home/clawer/.bashrc
   
   clawer$ eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv bash)"

   clawer$ which brew
           /home/linuxbrew/.linuxbrew/bin/brew
   ~~~

5. Add the non-default git remote for Homebrew/homebrew-core

   ~~~
   clawer$ echo '# Set non-default Git remote for Homebrew/homebrew-core.' >> /home/clawer/.bashrc

   clawer$ echo 'export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/homebrew-core.git"' >> /home/clawer/.bashrc

   clawer$ export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.aliyun.com/homebrew/homebrew-core.git"
   ~~~

6. Install Homebrew's dependencies

   ~~~
   clawer$ sudo apt-get install build-essential
           [sudo] password for clawer:  # W0rkT0gether
           Reading package lists... Done
           Building dependency tree... Done
           Reading state information... Done
           build-essential is already the newest version (12.9ubuntu3).
           The following package was automatically installed and is no longer required:
             libllvm14
           Use 'sudo apt autoremove' to remove it.
             0 upgraded, 0 newly installed, 0 to remove and 26 not upgraded.
   ~~~

7. Optionally, install `gcc`

   ~~~
   clawer$ brew install gcc
           ==> Fetching downloads for: gcc
           Warning: Bottle missing, falling back to the default domain...
           ==> Downloading https://ghcr.io/v2/homebrew/core/xz/manifests/5.8.2
           ...
           ==> Running `brew cleanup gcc`...
           Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
           Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
   ~~~
   
&nbsp;
## 4. Install and configure Openclaw

### 4.1 Install Openclaw 

Follow the instruction on [Openclaw's official website](https://docs.openclaw.ai/install) to install Openclaw,

~~~
clawer$ curl -fsSL https://openclaw.ai/install.sh | bash
~~~

Or, if `https://openclaw.ai/`, you can download `install.sh` first, 
rename it to `openclaw_install.sh`, and then run,

~~~
clawer$ bash openclaw_install.sh
~~~

When asked to choose AI model and its provider, you can choose "skip", or whatever model and provider, 
because we will change them later. 

When asked to choose channel, you can choose "skip", or whatever, e.g. "telegram", 
because we will change it later. 


### 4.2 Get AI provider's apiKey

We use Alibaba's `DashScope`, that has been renamed to `BaiLian` recently, as our AI provider.

1. Login to [Alibaba cloud platform](https://www.aliyun.com/),
  
   Use your master account to login, instead of RAM acccount. 

2. Creat `apiKey`,

* In "Alibaba cloud main page", click the left bar, and open the navigation panel,

  Click "AI model provider Bailian" -> Bailian main page,
  
  <p align="center" vertical-align="top">
    <img alt="Alibaba Cloud main page" src="./asset/bailian01.png" width="48%">
    &nbsp;
    <img alt="Entrance to Bailian page" src="./asset/bailian02.png" width="48%">
  </p>  

&nbsp;
* Click "Model service" on the top bar -> Model square page,
  
  Click "Private key management" on the left panel -> Private key management main page,

  <p align="center" vertical-align="top">
    <img alt="Bailian main page" src="./asset/bailian03.png" width="48%">
    &nbsp;
    <img alt="Bailian's model square page" src="./asset/bailian04.png" width="48%">
  </p>  

&nbsp;
* Click "Create API key" button.
  
  <p align="center" vertical-align="top">
    <img alt="Create apiKey" src="./asset/bailian05.png" width="48%">
  </p>  


&nbsp;
### 4.3 Set the authentication token for Openclaw gateway

1. Create `openclaw.json` configuration file

   Copy [`openclaw.json`](./src/openclaw.json) and upload it to the Alibaba cloud ECS instance.

   Move it to directory `~/.openclaw/openclaw.json`.

   Change its mode to 600.

   ~~~
   clawer$ pwd
           /home/clawer/.openclaw
   clawer$ chmod 600 openclaw.json
   clawer$ ls -l
           total 40
           drwxrwxr-x 3 clawer clawer 4096 Feb  7 00:03 agents
           drwxrwxr-x 2 clawer clawer 4096 Feb  7 00:07 canvas
           drwxrwxr-x 2 clawer clawer 4096 Feb  7 01:40 cron
           drwxrwxr-x 2 clawer clawer 4096 Feb  7 01:43 devices
           drwxrwxr-x 2 clawer clawer 4096 Feb  7 01:43 identity
           -rw------- 1 clawer clawer 1067 Feb  7 01:28 openclaw.json
           -rw-rw-r-- 1 clawer clawer   49 Feb  7 00:07 update-check.json
           drwxrwxr-x 3 clawer clawer 4096 Feb  7 00:03 workspace
   ~~~

&nbsp;
2. Set `Qwen-turbo` as our AI model, via `DashScope` AI model provider

   ~~~
   {
     "agents": {
        "defaults": {
           "model": {
              "primary": "dashscope/qwen-turbo"
           },
           "models": {
              "dashscope/qwen-turbo": {
                 "alias": "Qwen Turbo"
              }
           },
           ...
        }
     },
     "models": {
        "providers": {
           "dashscope": {
              "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
              "apiKey": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
              "api": "openai-completions",
              "models": [
                 {
                    "id": "qwen-turbo",
                    "name": "Qwen Turbo"
                 }
              ]
           }
        }
     },  
   }
   ~~~


&nbsp;
3. Set the authentication token for Openclaw gateway

   ~~~
   {
     "gateway": {
        "mode": "local",
        "auth": {
           "mode": "token",
           "token": "clawer_gateway_auth_token"
        }
     },
     ...
   }
   ~~~

   OpenClaw Gateway enables token-based authentication by default
   to restrict unauthorized access to your AI agent/gateway service running on `127.0.0.1:18789`.

   Once the token of the Openclaw's gateway has been configured,
   e.g. `clawer_gateway_auth_token`,
   we can use the token either in the URL or in the HTTP header.

   * URL example:

     ~~~
     http://127.0.0.1:18789/chat?session=main&token=clawer_gateway_auth_token
     ~~~

   * HTTP header example:
  
     ~~~
     Authorization: Bearer clawer_gateway_auth_token
     ~~~


&nbsp;
## 5. Run Openclaw


