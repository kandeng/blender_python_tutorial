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

8. The status of the job progress is stored in a `postgre-sql` database,
   the user can check the status of his job at any time.


&nbsp;
# 2. RabbitMQ, PostgreSQL, and MinIO

A `rabbit-mq` message queue, a `postgre-sql` rdbms database, and `MinIO` object storage service, 
are deployed in a server. 

Temporarily, they are deployed in a single node mode. 
In the future they will be deployed in a distributed way with multiple distributed nodes. 

All agents, the Blender executor, and the Fastapi web server, can use the rabbit-mq, the postgre-sql, and the min-io across machines. 
That means for the convenience of development and testing, we can run the agents in our local macbook,
and access the rabbit-mq, postgre-sql and min-io deployed in a remote server.

1. When the agents, the blender executor, and the fastapi web server, send messages to each other,
   they use rabbit-mq.

   Every agent, the blender executor, and the fastapi web server, are micro-services.
   The purpose is to keep the entire backend server loosely decoupled.

   Each micro-service runs in an infinite loop, with access to the rabbit-mq.

2. When the agents, the blender executor, and the fastapi web server, read or write data to the postgre-sql database,
   they connect the database directly via the database adapter `SQLAlchemy`.

   It is not necessary to wrap the postgre-sql database into a micro-service and connect to the outside via rabbit-mq, because,

   * Overengineering: Adds a redundant layer (DB microservice) with no tangible benefits for our use case.

   * Latency: rabbit-mq + database microservice adds 50–200ms per database call (cumulative delay for multi-step workflows).

   * Consistency Risks: Async database updates can lead to race conditions
     (e.g., the lead agent reads "pending" status， while the sub-agent writes "completed").

   * Debugging Complexity: Database operations are hidden behind rabbit-mq messages (hard to trace "who updated job X").

 3. When the agents, the blender executor, and the fastapi web server, upload or download files to or from the min-io object storage service,
    they connect min-io via http/https, instead of using rabbit-mq.

    The reason is that rabbit-mq works better for small and frequent messages, but not large files.


   
   

