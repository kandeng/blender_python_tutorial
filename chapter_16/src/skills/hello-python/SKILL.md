---
name: hello-python
description: "Prints hello world using a Python script in a sub-directory."
metadata: {"openclaw": {"requires": {"bins": ["python3"]}}}
user-invocable: true
---

# Hello Python

When the user wants to run the hello world test:
1. Use `python3` to execute the script.
2. The script is located at: `{{skillDir}}/scripts/hello.py`
3. Pass the user's name as an argument.

### Usage Example:

- "Run the hello python skill"
- "Greet Kanbo using the python script"

### Command:
`python3 {{skillDir}}/scripts/hello.py "{{name}}"`

### Notes:
- Ensure that `{{skillDir}}` is correctly resolved to the absolute path of the skill directory.
- The script `hello.py` should be placed in the `scripts` sub-directory within the skill directory.