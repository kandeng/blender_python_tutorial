# Blender Agent Infrastructure

## 1. Objective

Following is the backend workflow,

1. The backend fastapi web server receives the request from the fronted client.
   Usually the client request consists of a text prompt, and optionally with one or multiple sketches or 2D images.  

2. The fastapi web server publishes the client request to the rabbit-mq message queue,
   and a `lead` agent subscribes to the rabbit-mq and receives the client request. 

3. The `lead` agent forwards the client request, via rabbit-mq,
   to a remote AI model `Qwen2-72B-Chat` to recognize the client intention.

4. If the client request is to create 3D model based on the text prompt and attached sketches/images,
   the lead agent re-writes the prompt, and sends the modified prompt with the attached sketches/images
   to a `sub-agent`, via rabbit-mq,
   that uses a remote AI model `Qwen3-VL-Plus` to generate the detailed requirements in json format.

5. When the lead agent receives the detailed requirements from the image recognition sub-agent,
   the lead agent writes a prompt based on the requirements,
   and sends the prompt to another sub-agent via rabbit-mq,
   and that sub-agent uses `Qwen3-Turbo` to generate Blender python script.

6. The coding sub-agent sends the Blender python script back to the lead agent,
   and the lead agent sends the script via rabbit-mq to a Blender executor,
   the Blender executor uses `asyncio.create_subprocess_exec()` to spawn an isolated process
   to run the Blender 3D app in a headless/background mode.
   Once the job is finished, the Blender process is terminated.

7. The Blender executor sends the generated `.blend` file, or `.fbx` or `.gltf` file,
   all the way back to the lead agent, to the fastapi, and finally to the client side.
   The user can download this file from his browser.

