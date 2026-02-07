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
including `Qwen-turbo` and `Kimi Coding`,
via `DashScope` AI model provider. 
This allows us to simplify the billing process by paying in RMB.


&nbsp;
## 2. Outline

We took the following steps, and successfully installed Openclaw on an Alibaba's ECS instance. 

1. Create a regular user

   While it is possible to install OpenClaw as the root user,
   Alibaba Cloud disables root password authentication by default for security reasons. 
  
   This restriction prevents direct SSH access from a local machine.

   Furthermore, managing OpenClaw requires establishing a reverse SSH tunnel
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
