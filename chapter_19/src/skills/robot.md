---
name: Robot Pilot
metadata: { "openclaw": { "always": true, "requires": { "tools": ["robot_action"] } } }
---
# Instructions
When the user wants the robot to do something (e.g., "Move forward" or "Greet Kan Deng"):
1. **Action Extraction**: Convert the command into a JSON object (e.g., `{"move": "forward"}`).
2. **Context**: Put the user's original phrasing into `message_query`.
3. **Response**: Create a friendly, short confirmation (e.g., "Moving now, Kan Deng!") for `message_reply`.
4. **Invoke**: Call the `robot_action` tool with these parameters.

## Examples:
- User: "Make the robot move forward"
  - Action: `{"move": {"direction": "forward"}}`
  - Message Query: "Make the robot move forward"
  - Message Reply: "Moving forward now!"

- User: "Tell the robot to wave hello"
  - Action: `{"gesture": {"type": "wave", "action": "hello"}}`
  - Message Query: "Tell the robot to wave hello"
  - Message Reply: "Waving hello!"

- User: "Have the robot turn left"
  - Action: `{"turn": {"direction": "left", "degrees": 90}}`
  - Message Query: "Have the robot turn left"
  - Message Reply: "Turning left now!"