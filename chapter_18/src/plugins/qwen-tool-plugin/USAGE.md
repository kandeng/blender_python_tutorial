# Qwen Tool Plugin Usage Instructions

## Overview
The `qwen-tool-plugin` contains a tool called `qwen_tool` that sends a "hello qwen" message to the current user.

## How to Trigger
To use this plugin, you would typically send a message in a channel that the system recognizes as a command to invoke the tool. 

Example message to send in a channel:
```
"please use 'qwen-tool-plugin' to send a message back to me"
```

Or use the direct tool command:
```
/qwen_tool
```

Once triggered, the plugin will execute and return the message "hello qwen" to the user who invoked it.