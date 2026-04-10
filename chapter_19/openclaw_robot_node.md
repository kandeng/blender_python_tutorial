# Openclaw Robot Node 

## 1. robot-plugin

[`robot-plugin`](./src/plugins/robot-plugin) is to route a user query to a custom websocket server. 

To verify the dataflow, we create [a fake node](./src/nodes/robot_websocket/README.md) 
that is actually a custom websocket server for testing purpose. 


&nbsp;
## 2. aiya_plugin

Based on `robot-plugin`, we have created a real plugin called [`aiya_plugin`](./src/plugins/aiya_plugin) 
for the Aiya robot, a Labubu-like robotic toy.

Aiya robots rely on their own online server to communicate with users and other Aiya robots.

The `aiya_plugin` connects the openclaw gateway to the aiya server via websocket.
The Aiya server URL can be configured in [`openclaw.plugin.json`](./src/plugins/aiya_plugin/openclaw.plugin.json#L21).


&nbsp;
## 3. build123d_plugin

The most coherent way to communicate between the openclaw gateway and robots is by using openclaw nodes and plugins.

Openclaw nodes handle their own authentication with the gateway,
while plugins take charge of routing tool invocations to the appropriate authenticated node.

In addition, we want to explore the full potential of the OpenClaw node and plugin pair.

Using CAD tools to generate 3D objects is a heavy-lift, easily crashed task.

The best way to handle such unstable, resource-intensive jobs is to isolate them from the openclaw gateway using an MCP server.
For additional robustness, you can optionally run the CAD tool inside a Docker sandbox hosted by the MCP server.

The openclaw node and plugin are also capable of handling these heavy-lift, unstable jobs.
[`build123d_plugin`](./src/plugins/build123d_plugin) serves as one example.

However, MCP servers are generally preferred, as they can serve openclaw, claude code, and many other agents.
In contrast, the openclaw node and plugin solution is dedicated exclusively to openclaw.


&nbsp;
## 4. openclaw_node_package

Based on the implementation of `build123d_plugin`, 
we have created an open‑source package named [`openclaw_node_package`](https://github.com/kandeng/openclaw_node_package). 

This package greatly simplifies implementing communication between the openclaw gateway and devices or robots.

