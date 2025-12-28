import os
import json
import asyncio
import aio_pika
import datetime

from logger.logger import Logger
from rabbit_mq.rabbitmq_service import RabbitMQService


class OrchestratorAgent(RabbitMQService):
    def __init__(self):
        # Initialize with the input queue (from FastAPI)
        input_queue = os.getenv("RABBITMQ_QUEUE_FASTAPI_TO_ORCH")

        super().__init__(
            service_name="orchestrator", 
            input_queue=input_queue
        )
        self.fastapi_queue = os.getenv("RABBITMQ_QUEUE_ORCH_TO_FASTAPI")
        self.logger = Logger("langchain_agent").getLogger()


    async def handle_message(
            self, 
            message: aio_pika.IncomingMessage
        ):
        async with message.process():  # Auto-ack after processing
            try:
                job_data = json.loads(message.body.decode())
                job_id = job_data["job_id"]

                debug_msg = f"handle_message(), Received job message from fastapi_server: "
                job_data_str = json.dumps(job_data, ensure_ascii=False, indent=2)
                debug_msg += f"\n{job_data_str}\n"
                self.logger.debug(debug_msg)

                # Validate job
                if not job_data.get("prompt"):
                    warn_msg = f"handle_message(),  Invalid job message '{job_id}': empty prompt."
                    self.logger.warning(warn_msg)
                    return
                
                #
                # Testing content
                #
                curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
                job_data["now"] = f"[Kan] now='{curr_time}'"

                # Forward to Blender executor
                await self.publish_message(
                    routing_key=self.fastapi_queue,
                    data=job_data,
                    correlation_id=job_id
                )
                self.logger.debug(f"handle_message(), Forwarded job '{job_id}' to Blender.")

            except Exception as e:
                self.logger.warning(f"handle_message(), Failed to process job: '{str(e)}'.")



if __name__ == "__main__":
    try:
        orchestrator = OrchestratorAgent()
        
        # Run all async operations in a single event loop
        async def run_orchestrator():
            await orchestrator.connect()
            await orchestrator.start_consuming(orchestrator.handle_message)
            await asyncio.Event().wait()  # Keep service running
        
        asyncio.run(run_orchestrator())
        
    except KeyboardInterrupt:
        print("\n🛑 Orchestrator microservice stopped")
        asyncio.run(orchestrator.close())

