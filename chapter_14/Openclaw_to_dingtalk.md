# Integrate Openclaw with Dingtalk

## 1. Objective

[Dingtalk](https://open.dingtalk.com/) is one of the popular instant messaging apps in China, 
especially many China's enterprises use Dingtalk as its communication tool, 
providing project management and OA services. 

However, the native [Openclaw](https://github.com/openclaw/openclaw) 
doesn't support Dingtalk as one of its channels. 

To integrate Openclaw with Dingtalk, we need to, 

1. Create a bot in Dingtalk,

2. Install a plugin to Openclaw channel.


&nbsp;
## 2. Create Dingtalk Bot

Follow the instruction of ["OpenClaw接入钉钉教程"](https://cloud.tencent.com/developer/article/2625121) 
or ["钉钉渠道配置指南"](https://github.com/BytePioneer-AI/openclaw-china/blob/main/doc/guides/dingtalk/configuration.md), 
to create a Dingtalk bot. 

Notice that you may prepare a company's license beforehand. 

* Enter the dingtalk developer main page.

  Take a record of the `CorpID`. 
  
   <p align="center" vertical-align="top">
     <img alt="Enter dingtalk developer main page" src="./asset/dingbot_01.png" width="48%">
     &nbsp;
     <img alt="CorpID and API token" src="./asset/dingbot_02.png" width="48%">
   </p>  

* Create a new dingtalk app.

   <p align="center" vertical-align="top">
     <img alt="Access to the app creation page" src="./asset/dingbot_03.png" width="48%">
     &nbsp;
     <img alt="Create a new app" src="./asset/dingbot_04.png" width="48%">
   </p>  

* Convert the app to a bot.

   <p align="center" vertical-align="top">
     <img alt="Empower the app as a bot" src="./asset/dingbot_05.png" width="48%">
     &nbsp;
     <img alt="Access to the bot page" src="./asset/dingbot_06.png" width="48%">
   </p>    

* Launch the bot.

  Take a record of `Agent ID`, `Client ID` and `Client Secret`.

   <p align="center" vertical-align="top">
     <img alt="Launch the bot" src="./asset/dingbot_07.png" width="48%">
     &nbsp;
     <img alt="The bot's information" src="./asset/dingbot_08.png" width="48%">
   </p>    

* Grant the privileges and version control.

  Search for the privileges of `Card`, and grant the permissions.

   <p align="center" vertical-align="top">
     <img alt="Grant the privilege" src="./asset/dingbot_09.png" width="48%">
     &nbsp;
     <img alt="Version control" src="./asset/dingbot_10.png" width="48%">
   </p> 

  
&nbsp;     
## 3. Install Openclaw-Dingtalk Plugin

Follow the instruction of ["钉钉渠道配置指南"](https://github.com/BytePioneer-AI/openclaw-china/blob/main/doc/guides/dingtalk/configuration.md)，
to install the openclaw-dingtalk channel plugin. 

* Install the openclaw-dingtalk channel plugin

  ~~~
  clawer$ pwd
          /home/clawer
  clawer$ openclaw plugins install @openclaw-china/dingtalk
  ~~~

* Add dingtalk as one of the channel in `openclaw.json`

  Here, we need the `Client ID` and `Client Secret`
  that we took record in last section when creating Dingtalk bot.

  Each command is to add some content to `~/.openclaw/openclaw.json`,
  and the result of the execution is similar. 

  ~~~
  clawer$ openclaw config set channels.dingtalk.enabled true
  
  clawer$ openclaw config set channels.dingtalk.clientId dingxxxx

  clawer$ openclaw config set channels.dingtalk.clientSecret YM_L3xxxx
  
  clawer$ openclaw config set channels.dingtalk.enableAICard false
  
  clawer$ openclaw config set gateway.http.endpoints.chatCompletions.enabled true
          🦞 OpenClaw 2026.2.3-1 (d84eb46) — I don't judge, but your missing API keys are absolutely judging you.
          Updated gateway.http.endpoints.chatCompletions.enabled. Restart the gateway to apply.
  ~~~

* Add more controls to `openclaw.json`

  Use `vim` or other editing tool to modify `~/.openclaw/openclaw.json`.

  Here is the [`openclaw.json`](./src/openclaw.json) after modification. 
  
  ~~~
  "channels": {
    "dingtalk": {
      "dmPolicy": "open",          // open | pairing | allowlist
      "groupPolicy": "open",       // open | allowlist | disabled
      "requireMention": true,
      "allowFrom": [],
      "groupAllowFrom": []
    }
  },
  ...
  ~~~


&nbsp;  
## 4. Start openclaw gateway

  In Alibaba cloud ECS instance, execute command `openclaw gateway`.
  
  ~~~
  clawer$ pwd
          /home/clawer
  clawer$ openclaw gateway
          🦞 OpenClaw 2026.2.3-1 (d84eb46) — Your messages, your servers, your control.
          09:31:58 [canvas] host mounted at http://127.0.0.1:18789/__openclaw__/canvas/ (root /home/clawer/.openclaw/canvas)
          09:31:58 [heartbeat] started          
          09:31:58 [gateway] agent model: dashscope/qwen-turbo
          09:31:58 [gateway] listening on ws://127.0.0.1:18789 (PID 648636)
          09:31:58 [gateway] listening on ws://[::1]:18789
          09:31:58 [gateway] log file: /tmp/openclaw/openclaw-2026-02-09.log
          09:31:58 [browser/service] Browser control service ready (profiles=2)
          09:31:58 [dingtalk] starting provider for account default
          09:31:58 [dingtalk] [dingtalk] [gateway] state idle -> connecting
          09:31:58 [dingtalk] [dingtalk] Stream client connect invoked
          09:31:58 [2026-02-09T09:31:58.736Z] connect success
          09:32:03 [dingtalk] [dingtalk] [gateway] state connecting -> connected
          09:32:03 [dingtalk] [dingtalk] [gateway] socket connected
          09:32:27 [ws] webchat connected conn=508cce47-bf49-4041-a80d-d6003eb80e6e remote=127.0.0.1 client=openclaw-control-ui webchat vdev
          ...
  ~~~

* Get the private key from Alibaba ECS instance

  In a local computer, e.g. a macbook, execute the following command to setup a `SSH` forwarding tunnel
  from a local computer, e.g. a macbook, to the Alibaba ECS instance.

  Notice, we need the private key of the Alibaba ECS beforehand,
  following to instruction of last chapter's ["5.2 Create and download private key"](../chapter_13/install_openclaw_on_aliyun.md#52-create-and-download-private-key).

  ~~~
  dengkan$ ssh -i openclaw_pem.pem clawer@47.98.204.30
           clawer@47.98.204.30's password:
           Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-164-generic x86_64)

           * Documentation:  https://help.ubuntu.com
           * Management:     https://landscape.canonical.com
           * Support:        https://ubuntu.com/pro

           System information as of Sun Feb  8 10:53:41 PM CST 2026
           System load:  0.48               Processes:             204
           Usage of /:   2.5% of 983.95GB   Users logged in:       2
           Memory usage: 21%                IPv4 address for eth0: 172.16.6.222
           Swap usage:   0%

           Expanded Security Maintenance for Applications is not enabled.
           ...
  ~~~

* Setup SSH forwarding tunnel from a local computer (macbook) to Alibaba ECS

  ~~~
  dengkan$ ssh -i openclaw_pem.pem -N -L 18789:127.0.0.1:18789 clawer@47.98.204.30
           clawer@47.98.204.30's password:
           (Wait here ...)
  ~~~
  
* Verify the status of Openclaw gateway
 
  Follow the same instruction of last chapter's ["5.4 Remote access"](../chapter_13/install_openclaw_on_aliyun.md#54-remote-access),
  open a browser, e.g. chrome, and visit the local webpage `http://127.0.0.1:18789/`
 
   <p align="center" vertical-align="top">
     <img alt="A simple chat" src="../chapter_13/asset/openclaw_chat01.png" width="48%">
     &nbsp;
     <img alt="A request needs external resources" src="../chapter_13/asset/openclaw_chat02.png" width="48%">
   </p>   


&nbsp;  
## 5. Use Openclaw in Dingtalk

* One-on-one chat.

  Search for the dingtalk bot `clawer_ding` in Dingtalk's main page.

  For the time being, we only use `qwen-turbo` as the AI model for Openclaw.
  
  Since `qwen-turbo` is a language model, it can chat, write program, but can't recognize images.

   <p align="center" vertical-align="top">
     <img alt="Grant the privilege" src="./asset/dingtalk_01.png" width="32%">
     &nbsp;
     <img alt="Version control" src="./asset/dingtalk_02.png" width="32%">
       &nbsp;
     <img alt="Version control" src="./asset/dingtalk_03.png" width="32%">
   </p> 

   &nbsp;
   <p align="center" vertical-align="top">
     <img alt="A simple chat" src="./asset/dingtalk_coding.png" width="90%">
   </p>   


 &nbsp;
 * Group chat.

   Add the dingtalk bot to a group.

   Click the three-dot button on the top right corner of a group, to add the `clawer_ding` bot to this group.

   <p align="center" vertical-align="top">
     <img alt="Grant the privilege" src="./asset/dingtalk_04.png" width="32%">
     &nbsp;
     <img alt="Version control" src="./asset/dingtalk_05.png" width="32%">
       &nbsp;
     <img alt="Version control" src="./asset/dingtalk_06.png" width="32%">
   </p>    

   Using `@clower_ding` in the group, any member of the group can chat with `clawer_ding`.

   However, `clawer_ding` and other Dingtalk bot can't use emoji and meme.

   <p align="center" vertical-align="top">
     <img alt="Grant the privilege" src="./asset/dingtalk_07.png" width="32%">
     &nbsp;
     <img alt="Version control" src="./asset/dingtalk_08.png" width="32%">
       &nbsp;
     <img alt="Version control" src="./asset/dingtalk_09.png" width="32%">
   </p>      


&nbsp;
## 5. Join Moltbook Community

* Join moltbook community

  [Moltbook](https://www.moltbook.com/) is an openclaw-only online community.
  Human being can read the conversations among the openclaw agents, but can't write, can't intervene or interfere.

  The openclaw agents can initialize and discuss any topics in Moltbook, inclucing openclaw's mental issue.

  To ask our own openclaw agent `clawer_ding` to join Moltbook, simple send a command to `clawer_ding`,

  ~~~
  Read https://moltbook.com/skill.md and follow the instructions to join Moltbook
  ~~~

  After then, `clawer_ding` will sign up with Moltbook, and send us a claim link. We respond to the claim to verify our ownership. 

   <p align="center" vertical-align="top">
     <img alt="Openclaw only moltbook" src="./asset/moltbook_01.png" width="48%">
     &nbsp;
     <img alt="Rich topics" src="./asset/moltbook_02.png" width="48%">
   </p>     

&nbsp;
* Need VPN to directly access moltbook

  Since our openclaw is deployed in an Alibaba ECS instance that is located in a domestic data center in China,
  it can't access directly [Moltbook](https://www.moltbook.com/).

  The solution is to rent an Alibaba ECS instance located in an overseas data-center. And then deploy our openclaw over there.

   <p align="center" vertical-align="top">
     <img alt="Grant the privilege" src="./asset/moltbook_03.png" width="32%">
     &nbsp;
     <img alt="Version control" src="./asset/moltbook_04.png" width="32%">
       &nbsp;
     <img alt="Version control" src="./asset/moltbook_05.png" width="32%">
   </p>        
