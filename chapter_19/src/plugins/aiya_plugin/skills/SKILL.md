---
name: Aiya Robot Controller
description: Control the Aiya physical robot with voice and movement capabilities.
metadata:
  {
    "openclaw": {
        "emoji": "🤖",
        "always": true,
        "requires": {
            "tools": ["send_robot_command"]
        }
    }
  }
---

# Instructions

You control Aiya, a physical humanoid robot. Use the `send_robot_command` tool to execute actions.

## Tool: `send_robot_command`
- Parameter: `text` - Natural language description of the action

## When to Use

When the user wants the robot to do something:
- Movement: "Move forward", "Turn left", "Walk backward"
- Gestures: "Wave your hand", "Raise arms", "Bow"
- Speech: "Say hello", "Introduce yourself", "Tell a joke"
- Complex: "Walk forward and wave"

## Examples

**User:** "Ask the robot aiya to move her right arm up and down"
**Assistant:** [Calls send_robot_command(text="Move your right arm up and down")]

**User:** "让机器人向前走" (Chinese: Make the robot walk forward)
**Assistant:** [Calls send_robot_command(text="向前走")]

**User:** "Tell the robot to wave hello"
**Assistant:** [Calls send_robot_command(text="Wave your hand and say hello")]

## Response Format

1. Acknowledge what you're asking the robot to do
2. Call `send_robot_command` with a clear action description
3. Report the result
