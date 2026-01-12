import os
import json
import asyncio
import aiohttp
from celery import Celery
from pydantic import BaseModel, Field


import os
import json
import re
import time
import json
import asyncio
from asyncio import Semaphore
from pydantic import BaseModel, Field
from dotenv import load_dotenv


from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from logger.logger import Logger
from langchain_agent.freecad_rabbitmq import FreecadRabbitmq
from langchain_agent.planner_agent.freecad_planner import FreecadPlanner
from langchain_agent.coder_agent.freecad_coder import FreecadCoder
from langchain_agent.learner_agent.freecad_learner import FreecadLearner


# Load environment variables
from dotenv import load_dotenv
working_directory = os.getcwd()
config_env = f"{working_directory}/config/config.env"
load_dotenv(config_env)


# ---------------------------------------------------------------------------
#  Celery executor to receive tasks
# ---------------------------------------------------------------------------

# 1. Initialize Celery job dispatcher as a class attribute 
#    to be used in the function decorator.
celery = Celery(
    "freecad_executor",
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "rpc://")
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
    worker_pool="solo"      # Explicitly set pool type (redundant with CLI but safe)
)


# ---------------------------------------------------------------------------
#  Langchain agent workflow state 
# ---------------------------------------------------------------------------
class FreecadState(BaseModel):
    user_id: str = Field(description="User ID")
    text_prompt: str = Field(description="User input text prompt")
    filepaths: list = Field(description="User upload files")
    
    plan: str = Field(default="", description="Generated FreeCAD part plan")
    code: str = Field(default="", description="Generated FreeCAD Python code")
    evaluation: str = Field(default="", description="Evaluation of the code")
    final_result: str = Field(default="", description="Compiled final output")



class FreecadCelery:
    def __init__(self):
        try:
            self.logger = Logger("langchain_agent").getLogger()

            # 1. Initialize qwen AI model
            model_key = os.getenv("MODEL_KEY")
            model_name = os.getenv("MODEL_NAME")
            self.ai_model = ChatTongyi(
                dashscope_api_key=model_key,
                model_name=model_name,
                temperature=0.1,
                max_tokens=1000
            )

            # 2. Initialize the sub-agents
            self.planner_agent = FreecadPlanner()
            self.coder_agent = FreecadCoder()
            self.learner_agent = FreecadLearner()
            self.graph = self.build_freecad_graph()

            debug_msg = f"FreecadCelery(), successfully setup the celery executor and built the langchain agent graph."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"FreecadCelery(), following exception was thrown: \n\t'{str(e)}'\n"
            self.logger.warning(warn_msg)



    async def _aiohttp_post(
            self,
            target_url:str="",   
            form_data=None    
        ):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(target_url, data=form_data) as response:
                    content_type = response.headers.get('Content-Type').lower()
                    response_dict = {
                        "content_type": content_type,
                        "status": response.status
                    }

                    if "application/json" in content_type:
                        response_content = await response.json()
                        response_dict |= response_content

                    else:
                        response_content = await response.text()
                        response_dict["content"] = response_content

                    return response_dict
    
        except Exception as e:
            warn_msg = f"_aiohttp_post(), following exception was thrown: \n\t'{str(e)}'\n"
            self.logger.warning(warn_msg)
            return {}    
        
            

    async def send_webhook(
            self,
            user_id:str="", 
            result:str=""
        ):
        try:
            form_data = aiohttp.FormData()
            form_data.add_field("user_id", user_id)
            form_data.add_field("result", result)

            webhook_url = os.getenv("FASTAPI_WEBHOOK_URL", "http://localhost:8000/transmit/")

            response_json = await self._aiohttp_post(
                target_url=webhook_url,   
                form_data=form_data    
            )

            response_json_str = json.dumps(response_json, ensure_ascii=False, indent=2)
            debug_msg = f"send_webhook(), response_json: \n{response_json_str}\n"
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"send_webhook(), following exception was thrown: \n\t'{str(e)}'\n"
            self.logger.warning(warn_msg)



    # ---------------------------------------------------------------------------
    #  Langchain agent workflow
    # ---------------------------------------------------------------------------

    # ------------------------------------
    #  1. Define Workflow Nodes 
    # ------------------------------------
    async def call_planner(
            self,
            state: FreecadState
        ) -> dict:
        """Node 1: Call planner agent to generate a random part plan"""

        # Call planner's _arun() (async core logic)
        plan_output = await self.planner_agent._arun(part_type="")

        debug_msg = f"call_planner(), given input prompt: \n"
        debug_msg += f"\t '{state.text_prompt}', \n"
        debug_msg += f"the freecad_planner agent generated following plan: \n"
        debug_msg += f"\t '{plan_output}'. \n\n"
        self.logger.debug(debug_msg)

        await self.send_webhook(
            user_id=state.user_id, 
            result=plan_output
        )

        return {"plan": plan_output}


    async def call_coder(
            self,
            state: FreecadState
        ) -> dict:
        """Node 2: Call coder agent with the generated plan"""

        # Call coder's _arun() with the clean plan
        code_output = await self.coder_agent._arun(modeling_plan=state.plan)

        # Use regex to extract content between the first ```python and the next ```
        code_pattern = re.compile(r"```python(.*?)```", re.DOTALL)  # re.DOTALL makes . match newlines
        match = code_pattern.search(code_output)
        
        if match:
            # Extract the captured group (code inside the tags) and strip whitespace
            clean_code = match.group(1).strip()
        else:
            # Fallback: use the entire output if no code blocks are found
            clean_code = code_output.strip()

        debug_msg = f"call_coder(), given the plan generated by the freecad_planner agent: \n"
        debug_msg += f"\t '{state.plan}', \n"
        debug_msg += f"the freecad_coder agent generated following code: \n"
        debug_msg += f'\t "{clean_code}". \n\n'
        # self.logger.debug(debug_msg)

        await self.send_webhook(
            user_id=state.user_id, 
            result=clean_code
        )

        return {"code": clean_code}


    async def call_learner(
            self,
            state: FreecadState
        ) -> dict:
        """Node 3: Call learner agent with the generated code"""

        # Call learner's _arun() with clean code
        eval_output = await self.learner_agent._arun(code_snippet=state.code)

        debug_msg = f"call_learner(), given the code generated by the freecad_coder agent: \n"
        debug_msg += f"\t '{state.code}', \n"
        debug_msg += f"the freecad_learner agent generated following evaluation: \n"
        debug_msg += f"\t '{eval_output}'. \n\n"
        # self.logger.debug(debug_msg)

        await self.send_webhook(
            user_id=state.user_id, 
            result=eval_output
        )

        return {"evaluation": eval_output}


    async def compile_final_result(
            self,
            state: FreecadState
        ) -> dict:
        """Node 4: Compile plan + code + evaluation into a user-friendly response"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Compile the following FreeCAD workflow results into a clean, user-friendly response:
            - Use headings for Plan, Code, and Evaluation
            - Format code as a Python code block
            - Keep language simple and clear
            - Do NOT add extra text beyond the compiled response"""),
            ("user", """Plan: {plan}
            Code: {code}
            Evaluation: {evaluation}""")
        ])
        
        # Async LLM call to compile final response
        final_response = await self.ai_model.ainvoke(prompt.format(
            plan=state.plan,
            code=state.code,
            evaluation=state.evaluation
        ))
        final_result = final_response.content

        debug_msg = f"compile_final_result(), given the evaluation generated by the freecad_planner agent: \n"
        debug_msg += f"\t '{state.evaluation}', \n"
        debug_msg += f"ChatPromptTemplate generated following result: \n"
        debug_msg += f"\t{final_result}\n\n"
        # self.logger.debug(debug_msg)

        await self.send_webhook(
            user_id=state.user_id, 
            result=final_result
        )
        
        return {"final_result": final_result}
            
        
    # ------------------------------------
    #  2. Build the langchain workflow
    # ------------------------------------
    def build_freecad_graph(
            self
        ) -> CompiledStateGraph:
        """Build the stateful workflow graph (explicit step order)"""

        # Initialize StateGraph with our FreeCADState schema
        self.graph = StateGraph(FreecadState)

        # Add nodes to the graph
        self.graph.add_node("call_planner", self.call_planner)
        self.graph.add_node("call_coder", self.call_coder)
        self.graph.add_node("call_learner", self.call_learner)
        self.graph.add_node("compile_final", self.compile_final_result)

        self.graph.add_edge("call_planner", "call_coder")  # planner → coder
        self.graph.add_edge("call_coder", "call_learner")  # coder → learner
        self.graph.add_edge("call_learner", "compile_final")  # learner → compile
        self.graph.add_edge("compile_final", END)  # compile → end

        # Set the starting node
        self.graph.set_entry_point("call_planner")

        # Compile the graph (enables async execution)
        return self.graph.compile()


# ---------------------------------------------------------------------------
#  Standalone Celery Task Function
# ---------------------------------------------------------------------------
freecad_celery_instance = FreecadCelery()

@celery.task(name="freecad_celery.run_workflow", max_retries=1)
def run_workflow(
        task_dict:dict={}
    ) -> str:
    """Run the full async workflow via LangGraph"""
    task_dict_str = json.dumps(task_dict, ensure_ascii=False, indent=2)
    debug_msg = f"run_workflow(), task_dict received from celery:"
    debug_msg += f"\n{task_dict_str}\n"
    freecad_celery_instance.logger.debug(debug_msg)

    try:
        initial_state = FreecadState(
            user_id=task_dict["user_id"],
            text_prompt=task_dict["text_prompt"],
            filepaths=task_dict["filepaths"]
        )
        
        # Run the graph async (executes all nodes in order)
        final_state = asyncio.run(freecad_celery_instance.graph.ainvoke(initial_state))
        return final_state["final_result"]
    
    except Exception as e:
        warn_msg = f"run_workflow(), following exception was thrown: \n\t'{str(e)}'\n"
        freecad_celery_instance.logger.warning(warn_msg)


    

