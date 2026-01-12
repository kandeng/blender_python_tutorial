from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import os
import subprocess
import psutil
from multiprocessing import Process
from threading import Thread
from pathlib import Path
import aiofiles
import json
import gc
import time
import datetime
from typing import Dict, List, Optional, Callable, Awaitable
from asyncio import Lock  

from logger.logger import Logger
from fastapi_server.fastapi_celery import FastapiCelery
from fastapi_server.fastapi_memory import FastapiMemory



#-----------------------------------------------------------------------------
#  Global variables
#-----------------------------------------------------------------------------

# 1. OS environmental variables.
# 
from dotenv import load_dotenv
# os.getcwd() is to get the working_directory from the systemd.service file.
server_home_dir = os.getcwd()     # Equal to 'os.getenv("PWD")'
config_env = f"{server_home_dir}/config/config.env"
load_dotenv(config_env)

# 2. Logger
# 
logger = Logger("fastapi_server").getLogger()

# 3. Public file mounting
# 
public_dir = f"{server_home_dir}/public"
os.makedirs(public_dir, exist_ok=True)

# 4. Fastapi webserver
# 
engine = FastAPI()
engine.mount("/public", StaticFiles(directory="public"), name="public")

origins = [
    "http://localhost:5173",  # Vue dev server origin
    "http://127.0.0.1:5173",  # Vue dev server origin
    "http://localhost:8000",  # Self (optional)
]

engine.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Celery task dispatcher.
# 
fastapi_celery = None  

def get_fastapi_celery() -> object:
    global fastapi_celery
    if fastapi_celery is None:
        warn_msg = f"get_fastapi_celery(), fastapi_celery instance not initialized."
        logger.warning(warn_msg)
        return None
    return fastapi_celery

# 6. Memory for chat history.
# 
fastapi_memory = None  

def get_fastapi_memory() -> object:
    global fastapi_memory
    if fastapi_memory is None:
        warn_msg = f"get_fastapi_memory(), fastapi_memory instance not initialized."
        logger.warning(warn_msg)
        return None
    return fastapi_memory

# 7. Semaphore lock, for for thread-safe.
# 
active_websockets = {}

def get_active_websockets() -> dict:
    global active_websockets
    return active_websockets

# 8. Semaphore lock, for for thread-safe.
# 
state_lock = Lock()  

def get_state_lock() -> object:
    global state_lock
    return state_lock




#-----------------------------------------------------------------------------
#  Startup and shutdown
#  actually, shutdown is never used.
#-----------------------------------------------------------------------------

def startup():
    global fastapi_celery
    fastapi_celery = FastapiCelery()

    global fastapi_memory
    fastapi_memory = FastapiMemory()

    ssl_key_filepath = f"{server_home_dir}/ssl/xm.e-inv.cn_server.key"
    ssl_cert_filepath = f"{server_home_dir}/ssl/xm.e-inv.cn_server.crt"

    startup_message = f"startup(), Fastapi webserver is starting up ... \n"
    startup_message += f"\t ssl_key_filepath={ssl_key_filepath}\n"
    startup_message += f"\t ssl_cert_filepath={ssl_cert_filepath}\n"
    logger.info(startup_message)

    uvicorn.run(
        engine,
        host="0.0.0.0",
        port=8000,
        log_level="info"   # "debug"
    )


def shutdown():
    logger.info(f"shutdown(), Fastapi webserver is shutting down ... ")

    # Improved process termination logic
    try:
        fastapi_process = subprocess.run(
            ["pgrep", "-f", "fastapi_engine"], 
            capture_output=True,
            text=True
        )
        root_pid_str = fastapi_process.stdout.strip()
        if root_pid_str:
            root_pid = int(root_pid_str)
            if root_pid != os.getpid():  # Avoid killing self prematurely
                logger.info(f"shutdown(), Killing fastapi root process {root_pid}")
                proc = psutil.Process(root_pid)
                proc.kill()

    except Exception as e:
        logger.warning(f"shutdown(), Error during process termination: {str(e)}")



#-----------------------------------------------------------------------------
#  Fastapi webserver endpoints
#-----------------------------------------------------------------------------

@engine.get("/")
async def greet():
    greeting_msg = f"Given a sketch of a 3D object or a scene, AI3D Agent uses AI models "
    greeting_msg += f"to operate Blender/FreeCAD 3D app to create the 3D object and scene. "
    greeting_msg += f"After downloading the .blend or .fbx or .gltf or .stp file, "
    greeting_msg += f"you can fine tune the 3D model and scene if necessary. "
    return {"Introduction to AI3D Agent": greeting_msg}


@engine.get("/api/", response_class=RedirectResponse)
async def api_doc():
    return "/doc/api/"


@engine.get("/history/{user_id}")
async def get_chat_history(
        user_id: str,
        fastapi_memory: FastapiMemory = Depends(get_fastapi_memory),
        state_lock: Lock = Depends(get_state_lock)
    ):
    """
    Retrieve chat history for a user with thread safety.
    """
    async with state_lock:  # Add lock for shared state access
        amount = 100
        curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
        history = fastapi_memory.get_chat_history(user_id, amount)

        return JSONResponse({
            "user_id": user_id,
            "time_stamp": curr_time,
            "history": history
        })



@engine.post("/receive/")
async def receive_message(
        user_id: str = Form(...),
        content: str = Form(...),
        fastapi_memory: FastapiMemory = Depends(get_fastapi_memory),
        fastapi_celery: FastapiCelery = Depends(get_fastapi_celery),
        active_websockets: dict = Depends(get_active_websockets),
        state_lock: Lock = Depends(get_state_lock)
    ):
    content = content.strip()
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")

    # 1. Add user message to history with thread safety
    async with state_lock:  
        fastapi_memory.add_chat_history(user_id, content)
    
    # 2. Submit the task to celery. 
    task_id = fastapi_celery.submit_task(
        user_id=user_id,
        content=content
    ) 

    # 3. Acknowledge the sender.
    ack_message = {
        "sender": "ai_agent",
        "content": f"Your request has been received (task ID: {task_id}). Processing...",
        "files": [],
        "timestamp": curr_time
    }

    async with state_lock: 
        connection = active_websockets.get(user_id)
    if connection:
        try:
            await connection.send_json(ack_message)
        except Exception as e:
            warn_msg = f"receive_message(), Failed to send message to {user_id}: '{str(e)}'"
            logger.warning(warn_msg)
    
    return JSONResponse({
        "status": "success",
        "user_content": content,
        "ack_message": ack_message
    })



@engine.post("/transmit/")
async def transmit_message(
        user_id: str = Form(...),
        result: str = Form(...),
        fastapi_memory: FastapiMemory = Depends(get_fastapi_memory),
        active_websockets: dict = Depends(get_active_websockets),
        state_lock: Lock = Depends(get_state_lock)
    ):
    result = result.strip()
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
    
    # Create system/AI message
    transmit_msg = {
        "sender": "ai_agent",
        "content": result,
        "files": [],
        "timestamp": curr_time
    }
    
    # Add to chat history with thread safety
    async with state_lock: 
        fastapi_memory.add_chat_history(user_id, result)
    
    # Send via WebSocket (real-time)
    async with state_lock:  # Add lock for shared state access
        connection = active_websockets.get(user_id)
    if connection:
        try:
            await connection.send_json(transmit_msg)
            
            warn_msg = f"transmit_message(), successfully send the message to the client:"
            transmit_msg_str = json.dumps(transmit_msg, ensure_ascii=False, indent=2)
            warn_msg += f"\n{transmit_msg_str}\n"
            logger.warning(warn_msg)

            return JSONResponse({
                "status": "success",
                "agent_content": result,
                "data": transmit_msg
            })
        
        except Exception as e:
            warn_msg = f"transmit_message(), Failed to send message to {user_id}: '{str(e)}'"
            logger.warning(warn_msg)

    else:
        # Fallback: message stored but not sent (client disconnected)
        warn_msg = f"transmit_message(), client was not connected, so that the message was not sent:"
        transmit_msg_str = json.dumps(transmit_msg, ensure_ascii=False, indent=2)
        warn_msg += f"\n{transmit_msg_str}\n"
        logger.warning(warn_msg)

        return JSONResponse({
            "status": "pending",
            "message": "Client not connected, message stored",
            "data": transmit_msg
        })



@engine.post("/upload/")
async def upload(
        sender_id:str=Form(...),
        receiver_id:str=Form(...),
        message:str=Form(...),
        file: UploadFile | None = File(default=None)
    ):
    # Uses 'File(...)' instead of 'UploadFile(...)' in 'filepath: UploadFile | None = File(default=None)'
    # Otherwise, 'file: UploadFile = UploadFile(...)' will throw exception if the file is None.
    response_json = {
        "status": "success", 
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message": message,
        "filepath": "No file attached"
    }

    filepath = ""
    if file:
        # 1. Create the directory
        upload_dir = f"{server_home_dir}/uploaded_files"
        dir_path = Path(upload_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Handle file (e.g., save it)
        filepath = f"{upload_dir}/{file.filename}"
        async with aiofiles.open(filepath, "wb") as f:
            content = await file.read()
            await f.write(content)

        response_json["filepath"] = filepath
    else:
        # No file: handle only metadata
        response_json["filepath"] = "No file attached"

    response_json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
    logger.debug(f"upload(), response_json:\n{response_json_str}\n")

    return response_json




@engine.post("/download/")
async def download(
        user_id:str=Form(...),
        bucket_name:str=Form(...),
        object_name:str=Form(...),
        fastapi_memory: FastapiMemory = Depends(get_fastapi_memory),
        active_websockets: dict = Depends(get_active_websockets),
        state_lock: Lock = Depends(get_state_lock)
    ):
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
    download_record = f"User '{user_id}' downloaded '{bucket_name}/{object_name}' at {curr_time}." 
    download_msg = {
        "sender": "ai_agent",
        "content": download_record,
        "files": [],
        "timestamp": curr_time
    }

    # 1. Download the file stream from minio_fs
    try:
        minio_client = fastapi_memory.minio_client.minio_connection
        object_stat = minio_client.stat_object(bucket_name, object_name)
    except Exception as e:
        pass

    # 2. Keep a record in chat history.
    async with state_lock:  
        fastapi_memory.add_chat_history(
            user_id=user_id,
            content=download_record
        )    
        connection = active_websockets.get(user_id)

    # 3. Inform the client.
    if connection:
        try:
            await connection.send_json(download_msg)
            return JSONResponse({
                "status": "success",
                "agent_content": download_record,
                "data": download_msg
            })
        except Exception as e:
            warn_msg = f"download(), following exception was thrown: '{str(e)}'"
            logger.warning(warn_msg)
    else:
        # Fallback: message stored but not sent (client disconnected)
        return JSONResponse({
            "status": "pending",
            "message": "Client not connected, message stored",
            "data": download_msg
        })



@engine.websocket("/ws/{user_id}")
async def websocket_chat(
        websocket: WebSocket, 
        user_id: str,
        fastapi_memory: FastapiMemory = Depends(get_fastapi_memory),
        fastapi_celery: FastapiCelery = Depends(get_fastapi_celery),
        active_websockets: dict = Depends(get_active_websockets),
        state_lock: Lock = Depends(get_state_lock)
    ):
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
    await websocket.accept()

    # Add connection with thread safety
    async with state_lock:  
        active_websockets[user_id] = websocket

    # Initialize chat history if not exists
    chat_history = fastapi_memory.get_chat_history(
        user_id=user_id, 
        amount=100
    ) 

    if len(chat_history) == 0:
        greeting_content = "Hello! How can I help you today?"
        greeting_json = {
            "sender": "ai_agent", 
            "content": greeting_content, 
            "files": [], 
            "timestamp": curr_time
        }

        fastapi_memory.add_chat_history(
            user_id=user_id,
            content=greeting_content
        )
        await websocket.send_json(greeting_json)
    
    try:
        while True:
            # 1. Receive message from client (text + file paths)
            data = await websocket.receive_json()

            data_str = json.dumps(data, ensure_ascii=False, indent=2)
            logger.debug(f"websocket_chat(), websocket message: \n{data_str}\n")

            user_content = data.get("content", "")
            file_paths = data.get("files", [])
  
            async with state_lock:  # Add lock for shared state modification
                fastapi_memory.add_chat_history(
                    user_id=user_id,
                    content=user_content
                )
            
            # 2. Submit task to celery.
            task_id = fastapi_celery.submit_task(
                user_id=user_id,
                content=user_content
            ) 

            task_status = fastapi_celery.get_task_status(
                task_id=task_id
            )
            status = task_status["status"]
            
            # 3. Acknowledge the sender.
            ack_message = {
                "sender": "ai_agent",
                "content": f"Your request has been received (task ID: {task_id}). Process status: '{status}' ...",
                "files": [],
                "timestamp": curr_time
            }
            await websocket.send_json(ack_message)
    
    except WebSocketDisconnect:
        # Remove connection on disconnect with thread safety
        async with state_lock:  # Add lock for shared state modification
            if user_id in active_websockets:
                del active_websockets[user_id]
        logger.debug(f"websocket_chat(), User '{user_id}' disconnected.")




if __name__ == "__main__":
    startup()