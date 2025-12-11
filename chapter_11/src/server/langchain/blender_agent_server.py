from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import os
import sys
import uuid
import signal
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
from typing import Dict, List, Optional

from logger.logger import Logger
from ai_gateway.qwen3_coder import Qwen3Coder



# Load environment variables
from dotenv import load_dotenv
server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
config_env = f"{server_home_dir}/config/config.env"
load_dotenv(config_env)

public_dir = f"{server_home_dir}/public"
os.makedirs(public_dir, exist_ok=True)

blender_agent_server = None


# --------------------------
# Global State (for demo)
# --------------------------
# Store active WebSocket connections (user_id -> WebSocket)
active_connections: Dict[str, WebSocket] = {}
# Store chat history (user_id -> list of messages)
chat_history: Dict[str, List[Dict]] = {}




class BlenderAgentServer():
    def __init__(self):

        self.logger = Logger("langchain").getLogger()
        self.server_config = {}
        self.ssl_dir = ""
        self.root_pid = -9999
        self.master_agent = None

        try:
            # Load environment variables.
            server_config_filepath = os.getenv("SERVER_CONFIG")

            with open(server_config_filepath, "r") as fi:
                self.server_config = json.load(fi)
            self.ssl_dir = f"{server_home_dir}/{self.server_config['SSL_DIR']}"

            self.master_agent = Qwen3Coder()

        except Exception as e:
            warn_msg = f"BlenderAgentServer(), cannot load the configuration file, "
            warn_msg += f"the error message is: '{str(e)}'."
            self.logger.warning(warn_msg)



"""
Must locate FastAPI as a global variable,
otherwise, cannot use it as a decorator.
# engine = FastAPI(lifespan=self.lifespan_daemon)   
"""
engine = FastAPI()
engine.mount("/public", StaticFiles(directory="public"), name="public")

engine.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],  # Vue dev server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


"""
Refer to: 
1. How to terminate a Uvicorn + FastAPI application cleanly
   https://stackoverflow.com/questions/68603658/how-to-terminate-a-uvicorn-fastapi-application-cleanly-with-workers-2-when
2. What is the best way to stop Uvicorn server programmatically?
   https://stackoverflow.com/questions/67399724/what-is-the-best-way-to-stop-uvicorn-server-programmatically
"""
def startup():
    global blender_agent_server
    blender_agent_server = BlenderAgentServer()
    blender_agent_server.root_pid = os.getpid()

    startup_message = f"Blender agent server is starting up (PID={blender_agent_server.root_pid}) ... \n\n"
    blender_agent_server.logger.info(startup_message)

    ssl_key_filepath = f"{blender_agent_server.ssl_dir}/xm.e-inv.cn_server.key"
    ssl_cert_filepath = f"{blender_agent_server.ssl_dir}/xm.e-inv.cn_server.crt"

    uvicorn.run(
        engine,
        host="0.0.0.0",
        port=8000,
        log_level="debug"
    )


def shutdown():
    logger = Logger("langchain").getLogger()
    logger.info(f"Blender agent server is shuting down ... \n\n")

    completed_process = subprocess.run(
        ["pgrep", "-f", "blender_agent_server"], 
        capture_output=True,
        text=True
    )
    root_pid_str = completed_process.stdout
    if len(root_pid_str) > 0:
        root_pid_str = root_pid_str.strip()
        root_pid = int(root_pid_str)

        logger.info(f"Going to kill -9 '{root_pid}', the root process of outgoing fastapi engine.\n")
        proc = psutil.Process(root_pid)
        proc.kill()
    else:
        logger.warning("Cannot find the PID of the root thread of the outgoing fastapi.")




"""
For demo only
"""
def generate_ai_response(
        user_message: str, 
        files: List[str] = None
    ) -> str:
    """Mock AI response (replace with real LLM integration)"""
    if files:
        return f"Received your message: '{user_message}' + {len(files)} attached files. I'm processing them now..."
    return f"Thank you for your message: '{user_message}'. I'm an AI assistant built with FastAPI!"

@engine.get("/history/{user_id}")
async def get_chat_history(user_id: str):
    """Retrieve chat history for a user"""
    if user_id not in chat_history:
        return JSONResponse({"history": []})
    return JSONResponse({"history": chat_history[user_id]})






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
async def doc_api():
    bot_api_txt = blender_agent_server.server_config["API_DOC"]
    return bot_api_txt



@engine.post("/receive/")
async def receive_message(
        user_id: str = Form(...),
        content: str = Form("")
    ):
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")

    # Add user message to history
    user_msg = {
        "sender": user_id,
        "content": content,
        "timestamp": curr_time
    }
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append(user_msg)
    
    # Generate AI response
    content = content.strip()
    result = await blender_agent_server.master_agent.post_request(content)
    ai_msg = {
        "sender": "ai",
        "content": result["response"],
        "timestamp": curr_time
    }
    chat_history[user_id].append(ai_msg)
    
    # Proactively send AI message to client via WebSocket (if connected)
    if user_id in active_connections:
        try:
            await active_connections[user_id].send_json(ai_msg)
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
    
    return JSONResponse({
        "status": "success",
        "user_message": user_msg,
        "ai_message": ai_msg
    })



@engine.post("/transmit/")
async def transmit_message(
        user_id: str = Form(...), 
        content: str = Form(...)
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
    
    # Add to chat history
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append(transmit_msg)
    
    # Send via WebSocket (real-time)
    if user_id in active_connections:
        try:
            await active_connections[user_id].send_json(transmit_msg)
            return JSONResponse({
                "status": "success",
                "message": "Message transmitted to client",
                "data": transmit_msg
            })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to transmit: {str(e)}")
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
    blender_agent_server.logger.debug(f"upload(), response_json:\n{response_json_str}\n")

    return response_json



@engine.websocket("/ws/{user_id}")
async def websocket_chat(
        websocket: WebSocket, 
        user_id: str
    ):
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")

    await websocket.accept()

    active_connections[user_id] = websocket
    # Initialize chat history if not exists
    if user_id not in chat_history:
        chat_history[user_id] = [{
            "sender": "ai", 
            "content": "Hello! How can I help you today?", 
            "files": [], 
            "timestamp": curr_time
        }]
        # Send initial welcome message
        await websocket.send_json(chat_history[user_id][0])
    
    try:
        while True:
            # Receive message from client (text + file paths)
            data = await websocket.receive_json()
            user_message = data.get("content", "")
            file_paths = data.get("files", [])
            
            # Add user message to history
            user_msg = {
                "sender": "user",
                "content": user_message,
                "files": file_paths,
                "timestamp": curr_time
            }
            chat_history[user_id].append(user_msg)
            
            # Generate AI response
            ai_response = generate_ai_response(user_message, file_paths)
            ai_msg = {
                "sender": "ai",
                "content": ai_response,
                "files": [],
                "timestamp": curr_time
            }
            chat_history[user_id].append(ai_msg)
            
            # Send AI response back to client
            await websocket.send_json(ai_msg)
    
    except WebSocketDisconnect:
        # Remove connection on disconnect
        del active_connections[user_id]
        blender_agent_server.logger.debug(f"websocket_chat(), User '{user_id}' disconnected.")




def usage_sample():
    startup()
    time.sleep(300)
    print(f"\n[INFO] root_pid in main: [{os.getpid()}] \n")
    shutdown()


if __name__ == "__main__":
    """
    Run function from the command line
    https://stackoverflow.com/questions/3987041/run-function-from-the-command-line

    Usage for debugging:
    % cd ${buddybotty_home}
    % python3 buddybotty/buddybotty_server.py startup

    Usage for production:
    % cd ${buddybotty_home}
    % sh ./startup.sh
    % sh ./shutdown.sh
    """
    # globals()[sys.argv[1]]()

    usage_sample()

    

    
