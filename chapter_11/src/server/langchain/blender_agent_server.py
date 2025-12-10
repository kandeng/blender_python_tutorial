from fastapi import FastAPI
from fastapi import File, Form, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import os
import sys
import signal
import subprocess
import psutil
from multiprocessing import Process
from threading import Thread
from pathlib import Path
import asyncio
import json
import gc
import time
import datetime
import pprint


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


"""
engine.add_middleware(
    CORSMiddleware,
    allow_origins=["https://127.0.0.1:7788"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""


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
async def receive(req: dict):
    req_str = json.dumps(req, ensure_ascii=False, indent=2)
    blender_agent_server.logger.debug(f"receive(), req:\n{req_str}\n")

    req_text = req["text"].strip()
    result = await blender_agent_server.master_agent.post_request(req_text)
    return result


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
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        response_json["filepath"] = filepath
    else:
        # No file: handle only metadata
        response_json["filepath"] = "No file attached"

    response_json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
    blender_agent_server.logger.debug(f"upload(), response_json:\n{response_json_str}\n")

    return response_json



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

    

    
