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

&nbsp;
## 4. Use Openclaw in Dingtalk
