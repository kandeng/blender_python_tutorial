---
name: hello-docker
description: "Invokes a Python 'Hello World' script inside a Docker container."
metadata: {"openclaw": {"requires": {"bins": ["docker"]}}}
user-invocable: true
---

# Hello Docker Skill

When the user asks for a containerized greeting:
1. Ensure the docker image `openclaw-skill-hello:latest` is built.
2. Run the container using the following command.
3. Pass the user's name as an argument.

### Implementation Command:
`docker run --rm openclaw-skill-hello:latest "{{name}}"`

### Security Note:
The `--rm` flag ensures the container is deleted immediately after printing the message to keep the robot's system clean.