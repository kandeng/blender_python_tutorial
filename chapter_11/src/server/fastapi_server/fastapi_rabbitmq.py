import os
import uuid
import json
import time
import datetime
import aio_pika 

from fastapi import WebSocket
from typing import Dict, List, Optional, Callable, Awaitable

from logger.logger import Logger
from rabbit_mq.rabbitmq_service import RabbitMQService  


# Load environment variables
from dotenv import load_dotenv
server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
config_env = f"{server_home_dir}/config/config.env"
load_dotenv(config_env)



class FastapiRabbitmq(RabbitMQService):  # Inherit from RabbitMQService

    def __init__(self):
        # Initialize with queue for receiving from Orchestrator
        input_queue = os.getenv("RABBITMQ_QUEUE_ORCH_TO_FASTAPI")
        super().__init__(
            service_name="fastapi_server",
            input_queue=input_queue
        )
        
        # Queue for sending to Orchestrator
        self.orchestrator_queue = os.getenv("RABBITMQ_QUEUE_FASTAPI_TO_ORCH")

        self.logger = Logger("fastapi_server").getLogger()
        self.server_config = {}
        self.ssl_dir = ""
        self.root_pid = -9999

        # Store active WebSocket connections (user_id -> WebSocket)
        self.active_connections: Dict[str, WebSocket] = {}
        # Store chat history (user_id -> list of messages)
        self.chat_history: Dict[str, List[Dict]] = {}
        # Store job ID to user ID mapping (to route Orchestrator responses)
        self.job_id_to_user: Dict[str, str] = {}

        try:
            # Load environment variables
            server_config_filepath = os.getenv("SERVER_CONFIG")

            with open(server_config_filepath, "r") as fi:
                self.server_config = json.load(fi)
            self.ssl_dir = f"{server_home_dir}/{self.server_config['SSL_DIR']}"

        except Exception as e:
            warn_msg = f"BlenderAgentServer(), cannot load the configuration file, "
            warn_msg += f"the error message is: '{str(e)}'."
            self.logger.warning(warn_msg)



    async def receive_from_orchestrator(
            self, 
            message: aio_pika.IncomingMessage
        ):
        """
        Handle messages received from OrchestratorAgent
        """
        async with message.process():  # Auto-ack after processing
            try:
                job_data = json.loads(message.body.decode())
                job_id = job_data.get("job_id")
                if not job_id:
                    self.logger.warning("Received message without job_id")
                    return

                debug_msg = f"receive_from_orchestrator(), Received response for job '{job_id}' from OrchestratorAgent. \n"
                job_data_str = json.dumps(job_data, ensure_ascii=False, indent=2)
                debug_msg += f"The message is: \n{job_data_str}\n"
                self.logger.debug(debug_msg)

                # Extract relevant data
                status = job_data.get("status", "completed")
                result = job_data.get("result", "No result data")
                user_id = self.job_id_to_user.get(job_id)

                # Create response message
                response_msg = {
                    "sender": "system",
                    "content": f"Job {job_id} {status}: {result}",
                    "timestamp": datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
                }

                # Update chat history and send via WebSocket if user is connected
                if user_id:
                    if user_id not in self.chat_history:
                        self.chat_history[user_id] = []
                    self.chat_history[user_id].append(response_msg)

                    if user_id in self.active_connections:
                        await self.active_connections[user_id].send_json(response_msg)
                        
                        debug_msg = f"receive_from_orchestrator(), job '{job_id}' response "
                        debug_msg += f"has been sent to user '{user_id}'. "
                        self.logger.debug(debug_msg)

                    else:
                        warn_msg = f"receive_from_orchestrator(), User '{user_id}' is not connected, "
                        warn_msg += f"job '{job_id}' response has been stored in 'chat_history'. "
                        self.logger.warning(warn_msg)

                # Clean up job mapping after processing
                if job_id in self.job_id_to_user:
                    del self.job_id_to_user[job_id]

            except Exception as e:
                warn_msg = f"receive_from_orchestrator(), Failed to process the response of job '{job_id}' "
                warn_msg += f"from the OrchestratorAgent. \n The error message: '{str(e)}'."
                self.logger.warning(warn_msg)



    async def send_to_orchestrator(
            self, 
            user_id: str, 
            content: str, 
            file_paths: List[str]
        ) -> str:
        """
        Publish message from WebSocket to Orchestrator via RabbitMQ
        """
        try:
            if not self.connection.channel:
                await self.connect()  # Force reconnection if channel is missing
                if not self.connection.channel:
                    warn_msg = f"send_to_orchestrator(), Failed to establish RabbitMQ channel."
                    self.logger.warning(warn_msg)
                    return ""
                
            # Generate unique job ID
            job_id = str(uuid.uuid4())
            self.job_id_to_user[job_id] = user_id

            # Prepare job data
            job_data = {
                "job_id": job_id,
                "user_id": user_id,
                "prompt": content,
                "files": file_paths or [],
                "timestamp": datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
            }

            # Publish to Orchestrator queue
            await self.publish_message(
                routing_key=self.orchestrator_queue,
                data=job_data,
                correlation_id=job_id
            )

            debug_msg = f"send_to_orchestrator(), send the following message to OrchestratorAgent, "
            job_data_str = json.dumps(job_data, ensure_ascii=False, indent=2)
            debug_msg += f"\n{job_data_str}\n"
            self.logger.debug(debug_msg)

            return job_id

        except Exception as e:
            warn_msg = f"send_to_orchestrator(), Failed to send message to Orchestrator. "
            warn_msg += f"The error message is: '{str(e)}'."
            self.logger.warning(warn_msg)
