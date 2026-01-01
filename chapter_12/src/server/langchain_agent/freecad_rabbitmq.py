import os
import uuid
import json
import queue
import time
import datetime
import aio_pika 
from dotenv import load_dotenv

from fastapi import WebSocket
from typing import Dict, List, Optional, Callable, Awaitable

from logger.logger import Logger
from rabbit_mq.rabbitmq_client import RabbitmqClient  



class FreecadRabbitmq: 

    def __init__(self):
        try:
            # 1. Initialize the logger.
            self.logger = Logger("langchain_agent").getLogger()

            # 2. Load environment variables
            working_directory = os.getcwd()   # Equal to 'os.getenv("PWD")'
            config_env = f"{working_directory}/config/config.env"
            load_dotenv(config_env)

            # 3.1 Initialize the receiving queue from the Fastapi webserver
            queue_from_fastapi = os.getenv("RABBITMQ_QUEUE_FASTAPI_TO_LANGCHAIN", "fastapi_to_langchain")
            self.rabbitmq_client = RabbitmqClient(
                client_name="langchain_agent",
                input_queue=queue_from_fastapi
            )
            
            # 3.2 The routing_key to send message to the Fastapi webserver
            self.queue_to_fastapi = os.getenv("RABBITMQ_QUEUE_LANGCHAIN_TO_FASTAPI", "langchain_to_fastapi")


            # 4. Initialize the job queue to store the messages received from the Fastapi webserver.
            self.job_queue = queue.Queue()

        except Exception as e:
            warn_msg = f"FreecadRabbitmq(), following exception was thrown: \n"
            warn_msg += f"\t '{str(e)}'."
            self.logger.warning(warn_msg)




    async def receive_from_fastapi(
            self, 
            message: aio_pika.IncomingMessage
        ):
        """
        Handle messages received from the Fastapi web server
        """
        async with message.process():  # Auto-ack after processing
            try:
                job_data = json.loads(message.body.decode())
                job_id = job_data.get("job_id")
                if not job_id:
                    self.logger.warning("Received message without job_id")
                    return
                
                self.job_queue.put(job_data) 

                debug_msg = f"receive_from_fastapi(), Received response for job '{job_id}' from the Fastapi webserver. \n"
                job_data_str = json.dumps(job_data, ensure_ascii=False, indent=2)
                debug_msg += f"The message is: \n{job_data_str}\n"
                self.logger.debug(debug_msg)

                """
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
                        
                        debug_msg = f"receive_from_langchain(), job '{job_id}' response "
                        debug_msg += f"has been sent to user '{user_id}'. "
                        self.logger.debug(debug_msg)

                    else:
                        warn_msg = f"receive_from_langchain(), User '{user_id}' is not connected, "
                        warn_msg += f"job '{job_id}' response has been stored in 'chat_history'. "
                        self.logger.warning(warn_msg)

                # Clean up job mapping after processing
                if job_id in self.job_id_to_user:
                    del self.job_id_to_user[job_id]
                """

            except Exception as e:
                warn_msg = f"receive_from_fastapi(), Failed to process the response of job '{job_id}' "
                warn_msg += f"from the Fastapi webserver. \n The error message: '{str(e)}'."
                self.logger.warning(warn_msg)



    async def send_to_fastapi(
            self, 
            user_id: str, 
            content: str, 
            file_paths: List[str]
        ) -> str:
        """
        Publish message from Langchain agent to Fastapi webserver via rabbit_mq
        """
        try:
            if not self.rabbitmq_client.connection.channel:
                await self.rabbitmq_client.connect()  # Force reconnection if channel is missing
                if not self.rabbitmq_client.connection.channel:
                    warn_msg = f"send_to_fastapi(), Failed to establish RabbitMQ channel."
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
            await self.rabbitmq_client.publish_message(
                routing_key=self.queue_to_fastapi,
                data=job_data,
                correlation_id=job_id
            )

            debug_msg = f"send_to_fastapi(), send the following message to Fastapi webserver, "
            job_data_str = json.dumps(job_data, ensure_ascii=False, indent=2)
            debug_msg += f"\n{job_data_str}\n"
            self.logger.debug(debug_msg)

            return job_id

        except Exception as e:
            warn_msg = f"send_to_fastapi(), Failed to send message to Fastapi webserver, \n"
            warn_msg += f"\t The error message is: '{str(e)}'."
            self.logger.warning(warn_msg)


