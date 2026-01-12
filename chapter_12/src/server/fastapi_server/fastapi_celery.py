import os
from celery import Celery
from dotenv import load_dotenv

from logger.logger import Logger


# 1. Initialize Celery job dispatcher as a class attribute 
#    to be used in the function decorator.
celery = Celery(
    "fastapi_dispatcher",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "rpc://"),
    include=["langchain_agent.freecad_celery"]
)

# 2. Celery optimization (critical for production)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,          # Acknowledge task only after completion
    worker_prefetch_multiplier=1, # Fetch 1 task at a time (FIFO)
    result_expires=3600,          # Expire results after 1 hour (cleanup)
    result_backend_transport_options={
        "max_size": 104857600     # 100MB max payload (for large stage results)
    },
    worker_pool="solo",  # Required for async tasks (Celery 5.x)
    task_annotations={"*": {"rate_limit": "10/s"}}  # Optional: rate limiting    
)


class FastapiCelery:
    def __init__(self):
        try:
            self.logger = Logger("fastapi_server").getLogger()

            # Load environment variables
            server_home_dir = os.getcwd()
            config_env = f"{server_home_dir}/config/config.env"
            load_dotenv(config_env)

        except Exception as e:
            warn_msg = f"FastapiCelery(), following exception was thrown: \n\t'{str(e)}'\n"
            self.logger.warning(warn_msg)



    @celery.task(bind=True)
    def submit_task(
            self,
            user_id:str="",
            content:str=""
        ) -> str:
        try:
            # Task name from freecad_celery.py
            executer_name = os.getenv("FREECAD_EXECUTOR", "freecad_celery.run_workflow")
            # Dedicated queue for FreeCAD tasks
            task_queue = os.getenv("CELERY_QUEUE", "freecad_tasks")  

            task_dict = {
                "user_id": user_id,
                "text_prompt": content,
                "filepaths": []
            }
            
            celery_task = celery.send_task(
                name=executer_name,  
                args=[task_dict],
                queue=task_queue  
            )
            return str(celery_task.id)

        except Exception as e:
            warn_msg = f"submit_task(), following exception was thrown: \n\t'{str(e)}'\n"
            self.logger.warning(warn_msg)
            return ""



    @celery.task(bind=True)
    def get_task_status(
            self,
            task_id:str=""
        ) -> dict:
        task_status = {}
        try:
            task = celery.AsyncResult(task_id)

            if task.state.upper() in ["SUCCESS", "PROGRESS"]:
                task_status = {
                    "task_id": task_id, 
                    "status": "completed", 
                    "result": str(task.result)
                }
            elif task.state.upper() == "PENDING":
                task_status = {
                    "task_id": task_id, 
                    "status": "pending"
                }
            else:
                task_status = {
                    "task_id": task_id, 
                    "status": task.state.lower(), 
                    "error": str(task.result)
                }

        except Exception as e:
            warn_msg = f"get_task_status(), following exception was thrown: \n\t'{str(e)}'\n"
            self.logger.warning(warn_msg)
        
        return task_status


