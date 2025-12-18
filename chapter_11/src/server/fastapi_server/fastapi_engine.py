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
import asyncio
import aiofiles
import json
import gc
import time
import datetime
from typing import Dict, List, Optional, Callable, Awaitable
from asyncio import Lock  # Added for async locks

from logger.logger import Logger
from fastapi_server.fastapi_rabbitmq import FastapiRabbitmq


# Load environment variables
from dotenv import load_dotenv
server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
config_env = f"{server_home_dir}/config/config.env"
load_dotenv(config_env)

public_dir = f"{server_home_dir}/public"
os.makedirs(public_dir, exist_ok=True)



"""
FastAPI initialization
"""
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


fastapi_rabbitmq = None  
state_lock = Lock()  # Async lock for thread-safe state modifications


# Dependency function to get the global fastapi_rabbitmq instance
def get_fastapi_rabbitmq():
    global fastapi_rabbitmq
    if fastapi_rabbitmq is None:
        warn_msg = f"get_fastapi_rabbitmq(), RabbitMQ instance not initialized."
        raise HTTPException(status_code=500, detail=warn_msg)
        
    return fastapi_rabbitmq


async def start_rabbitmq_consumer():
    """
    Start RabbitMQ consumer in background with reconnection logic.
    """
    global fastapi_rabbitmq
    if fastapi_rabbitmq is None:
        return

    while True:  # Add reconnection loop
        try:
            await fastapi_rabbitmq.connect()
            await fastapi_rabbitmq.start_consuming(
                message_handler=fastapi_rabbitmq.receive_from_orchestrator
            )
            
            debug_msg = f"start_rabbitmq_consumer(), RabbitMQ consumer started successfully."
            fastapi_rabbitmq.logger.debug(debug_msg)
            break  # Exit loop if consumption starts successfully

        except Exception as e:
            fastapi_rabbitmq.logger.warning(
                f"start_rabbitmq_consumer(), Failed to start RabbitMQ consumer: '{str(e)}'. Retrying in 5s..."
            )
            await asyncio.sleep(5)  # Wait before retrying


def startup():
    global fastapi_rabbitmq
    fastapi_rabbitmq = FastapiRabbitmq()
    fastapi_rabbitmq.root_pid = os.getpid()

    # Initialize thread-safe structures
    fastapi_rabbitmq.chat_history = {}
    fastapi_rabbitmq.active_connections = {}

    startup_message = f"startup(), Fastapi server is starting up (PID={fastapi_rabbitmq.root_pid}) ... \n\n"
    fastapi_rabbitmq.logger.info(startup_message)

    # Start RabbitMQ consumer in a background task
    loop = asyncio.get_event_loop()
    loop.create_task(start_rabbitmq_consumer())

    ssl_key_filepath = f"{fastapi_rabbitmq.ssl_dir}/xm.e-inv.cn_server.key"
    ssl_cert_filepath = f"{fastapi_rabbitmq.ssl_dir}/xm.e-inv.cn_server.crt"

    uvicorn.run(
        engine,
        host="0.0.0.0",
        port=8000,
        log_level="info"   # "debug"
    )


def shutdown():
    global fastapi_rabbitmq
    logger = Logger("fastapi_server").getLogger()
    logger.info(f"shutdown(), Fastapi server is shutting down ... ")

    # Close RabbitMQ connection gracefully with proper null check
    if fastapi_rabbitmq is not None:
        try:
            asyncio.run(fastapi_rabbitmq.close())
        except Exception as e:
            logger.warning(f"shutdown(), Error closing RabbitMQ connection: '{str(e)}'.")

    # Improved process termination logic
    try:
        completed_process = subprocess.run(
            ["pgrep", "-f", "fastapi_server"], 
            capture_output=True,
            text=True
        )
        root_pid_str = completed_process.stdout.strip()
        if root_pid_str:
            root_pid = int(root_pid_str)
            if root_pid != os.getpid():  # Avoid killing self prematurely
                logger.info(f"shutdown(), Killing root process {root_pid}")
                proc = psutil.Process(root_pid)
                proc.kill()

    except Exception as e:
        logger.warning(f"shutdown(), Error during process termination: {str(e)}")


"""
Message handling utilities
"""
def generate_ai_response(
        user_message: str, 
        files: List[str] = None
    ) -> str:
    """
    Mock AI response (replace with real LLM integration).
    """
    if files:
        return f"Received your message: '{user_message}' + {len(files)} attached files. I'm processing them now..."
    return f"Thank you for your message: '{user_message}'. I'm an AI assistant built with FastAPI!"


@engine.get("/history/{user_id}")
async def get_chat_history(
        user_id: str,
        rabbitmq: FastapiRabbitmq = Depends(get_fastapi_rabbitmq)
    ):
    """
    Retrieve chat history for a user with thread safety.
    """
    async with state_lock:  # Add lock for shared state access
        history = rabbitmq.chat_history.get(user_id, [])
    return JSONResponse({"history": history})


@engine.get("/")
async def greet():
    greeting_msg = f"Given a sketch of a 3D object or a scene, Blender AI Agent uses AI model "
    greeting_msg += f"to operate Blender 3D app to create the 3D model and scene. "
    greeting_msg += f"After downloading the .blend or .fbx or .gltf file, "
    greeting_msg += f"you can fine tune the 3D model and scene if necessary. "
    return {"Introduction to Blender AI Agent": greeting_msg}


@engine.get("/api/", response_class=RedirectResponse)
async def api_doc():
    return "/doc/api/"


@engine.get("/doc/api/")
async def doc_api(
        rabbitmq: FastapiRabbitmq = Depends(get_fastapi_rabbitmq)
    ):
    bot_api_txt = rabbitmq.server_config["API_DOC"]
    return bot_api_txt


@engine.post("/receive/")
async def receive_message(
        user_id: str = Form(...),
        content: str = Form(""),
        rabbitmq: FastapiRabbitmq = Depends(get_fastapi_rabbitmq)
    ):
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")

    # Add user message to history with thread safety
    user_msg = {
        "sender": user_id,
        "content": content,
        "timestamp": curr_time
    }
    async with state_lock:  # Add lock for shared state modification
        if user_id not in rabbitmq.chat_history:
            rabbitmq.chat_history[user_id] = []
        rabbitmq.chat_history[user_id].append(user_msg)
    
    # Generate AI response
    content = content.strip()
    job_id = await rabbitmq.send_to_orchestrator(
        user_id=user_id,
        content=user_msg,
        file_paths=[]
    )
    
    # 2.2 Reply to client via WebSocket immediately
    confirmation_msg = {
        "sender": "ai",
        "content": f"Your request has been received (Job ID: {job_id}). Processing...",
        "files": [],
        "timestamp": curr_time
    }
    async with state_lock:  # Add lock for shared state modification
        rabbitmq.chat_history[user_id].append(confirmation_msg)
    
    # Proactively send AI message to client via WebSocket (if connected)
    async with state_lock:  # Add lock for shared state access
        connection = rabbitmq.active_connections.get(user_id)
    if connection:
        try:
            await connection.send_json(confirmation_msg)
        except Exception as e:
            warn_msg = f"receive_message(), Failed to send message to {user_id}: '{str(e)}'"
            rabbitmq.logger.warning(warn_msg)
    
    return JSONResponse({
        "status": "success",
        "user_message": user_msg,
        "ai_message": confirmation_msg
    })


@engine.post("/transmit/")
async def transmit_message(
        user_id: str = Form(...), 
        content: str = Form(...),
        rabbitmq: FastapiRabbitmq = Depends(get_fastapi_rabbitmq)
    ):
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")

    """Proactively send a message from server to client (e.g., AI notifications)"""
    if not user_id or not content:
        raise HTTPException(status_code=400, detail="User ID and content are required")
    
    # Create system/AI message
    transmit_msg = {
        "sender": "ai",
        "content": content,
        "files": [],
        "timestamp": curr_time
    }
    
    # Add to chat history with thread safety
    async with state_lock:  # Add lock for shared state modification
        if user_id not in rabbitmq.chat_history:
            rabbitmq.chat_history[user_id] = []
        rabbitmq.chat_history[user_id].append(transmit_msg)
    
    # Send via WebSocket (real-time)
    async with state_lock:  # Add lock for shared state access
        connection = rabbitmq.active_connections.get(user_id)
    if connection:
        try:
            await connection.send_json(transmit_msg)
            return JSONResponse({
                "status": "success",
                "message": "Message transmitted to client",
                "data": transmit_msg
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to transmit: '{str(e)}'")
    else:
        # Fallback: message stored but not sent (client disconnected)
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
        file: UploadFile | None = File(default=None),
        rabbitmq: FastapiRabbitmq = Depends(get_fastapi_rabbitmq)  
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
    rabbitmq.logger.debug(f"upload(), response_json:\n{response_json_str}\n")

    return response_json


@engine.websocket("/ws/{user_id}")
async def websocket_chat(
        websocket: WebSocket, 
        user_id: str,
        rabbitmq: FastapiRabbitmq = Depends(get_fastapi_rabbitmq)
    ):
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")

    await websocket.accept()

    # Add connection with thread safety
    async with state_lock:  # Add lock for shared state modification
        rabbitmq.active_connections[user_id] = websocket
        # Initialize chat history if not exists
        if user_id not in rabbitmq.chat_history:
            rabbitmq.chat_history[user_id] = [{
                "sender": "ai", 
                "content": "Hello! How can I help you today?", 
                "files": [], 
                "timestamp": curr_time
            }]
            # Send initial welcome message
            await websocket.send_json(rabbitmq.chat_history[user_id][0])
    
    try:
        while True:
            # Receive message from client (text + file paths)
            data = await websocket.receive_json()

            data_str = json.dumps(data, ensure_ascii=False, indent=2)
            rabbitmq.logger.warning(f"websocket_chat(), websocket message: \n{data_str}\n")

            user_message = data.get("content", "")
            file_paths = data.get("files", [])
            
            # Add user message to history with thread safety
            user_msg = {
                "sender": "user",
                "content": user_message,
                "files": file_paths,
                "timestamp": curr_time
            }
            async with state_lock:  # Add lock for shared state modification
                rabbitmq.chat_history[user_id].append(user_msg)
            
            # 2.1 Publish message to RabbitMQ via Orchestrator queue
            job_id = await rabbitmq.send_to_orchestrator(
                user_id=user_id,
                content=user_message,
                file_paths=file_paths
            )
            
            # 2.2 Reply to client via WebSocket immediately
            confirmation_msg = {
                "sender": "ai",
                "content": f"Your request has been received (Job ID: {job_id}). Processing...",
                "files": [],
                "timestamp": curr_time
            }
            async with state_lock:  # Add lock for shared state modification
                rabbitmq.chat_history[user_id].append(confirmation_msg)
            await websocket.send_json(confirmation_msg)
    
    except WebSocketDisconnect:
        # Remove connection on disconnect with thread safety
        async with state_lock:  # Add lock for shared state modification
            if user_id in rabbitmq.active_connections:
                del rabbitmq.active_connections[user_id]
        rabbitmq.logger.debug(f"websocket_chat(), User '{user_id}' disconnected.")


def usage_sample():
    startup()
    time.sleep(300)
    print(f"\n[INFO] root_pid in main: [{os.getpid()}] \n")
    shutdown()


if __name__ == "__main__":
    usage_sample()