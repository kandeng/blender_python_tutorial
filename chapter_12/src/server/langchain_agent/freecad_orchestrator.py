import os
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



# ----------------------------------------------------
# Define Workflow State (data passed between steps)
# ----------------------------------------------------
class FreecadState(BaseModel):
    """State schema for the FreeCAD workflow (tracks data across steps)"""

    input: str = Field(description="User input prompt")
    plan: str = Field(default="", description="Generated FreeCAD part plan")
    code: str = Field(default="", description="Generated FreeCAD Python code")
    evaluation: str = Field(default="", description="Evaluation of the code")
    final_result: str = Field(default="", description="Compiled final output")


# ----------------------------------------------------
# LangGraph-powered Orchestrator Class
# ----------------------------------------------------
class FreecadOrchestrator:
    def __init__(self):
        try:
            # 1. Initialize the logger.
            self.logger = Logger("langchain_agent").getLogger() 

            # 2. Get the WorkingDirectory from systemd (runtime CWD)
            working_directory = os.getcwd()   # Equal to 'os.getenv("PWD")'
            config_env = f"{working_directory}/config/config.env"
            load_dotenv(config_env)
            model_key = os.getenv("MODEL_KEY")
            model_name = os.getenv("MODEL_NAME")

            # 3. Initialize a semaphore for concurrency control (throttling parallel execution)
            # Fixed delay between loop iterations (prevents continuous execution)
            self.BASE_DELAY_SECONDS = 60  # Run once every 60 seconds
            # Dynamic delay fallback (if workflow is fast, add extra buffer)
            self.MIN_ITERATION_DURATION = 10  # Ensure each loop cycle takes at least 10s

            # Max concurrent workflow runs (prevents parallel overload)
            self.MAX_CONCURRENT_WORKFLOWS = 1  # Only 1 workflow at a time
            self.concurrency_semaphore = Semaphore(self.MAX_CONCURRENT_WORKFLOWS)            


            # 4. Initialize rabbit_mq 
            self.rabbitmq = FreecadRabbitmq()


            # 5. Initialize qwen AI model
            self.ai_model = ChatTongyi(
                dashscope_api_key=model_key,
                model_name=model_name,
                temperature=0.1,
                max_tokens=1000
            )

            # 6. Initialize the sub-agents
            self.planner_agent = FreecadPlanner()
            self.coder_agent = FreecadCoder()
            self.learner_agent = FreecadLearner()
            self.graph = self.build_freecad_graph()

            debug_msg = f"FreecadOrchestrator(), successfully built the langchain agent graph."
            self.logger.debug(debug_msg)
        
        except Exception as e:
            warn_msg = f"FreecadOrchestrator(), following exception was thrown: \n"
            warn_msg += f"\t '{str(e)}'"
            self.logger.warning(warn_msg)


    # --------------------------
    # Define Workflow Nodes 
    # --------------------------
    async def call_planner(
            self,
            state: FreecadState
        ) -> dict:
        """Node 1: Call planner agent to generate a random part plan"""

        # Call planner's _arun() (async core logic)
        plan_output = await self.planner_agent._arun(part_type="")

        debug_msg = f"call_planner(), given input prompt: \n"
        debug_msg += f"\t '{state.input}', \n"
        debug_msg += f"the freecad_planner agent generated following plan: \n"
        debug_msg += f"\t '{plan_output}'. \n\n"
        # self.logger.debug(debug_msg)

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

        return {"code": clean_code}


    async def call_learner(
            self,
            state: FreecadState
        ) -> dict:
        """Node 3: Call learner agent with the generated code"""

        # Call learner's _arun() with clean code
        eval_output = await self.learner_agent._arun(code_snippet=state.code)
        
        # Extract evaluation (remove "📚 FreeCAD Code Explanation:\n" prefix)
        # clean_eval = eval_output.split("\n", 1)[1] if "📚" in eval_output else eval_output

        debug_msg = f"call_learner(), given the code generated by the freecad_coder agent: \n"
        debug_msg += f"\t '{state.code}', \n"
        debug_msg += f"the freecad_learner agent generated following evaluation: \n"
        debug_msg += f"\t '{eval_output}'. \n\n"
        # self.logger.debug(debug_msg)

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
        
        return {"final_result": final_result}
            
        
    # --------------------------
    # Build the LangGraph Workflow
    # --------------------------
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



    async def run_workflow(
            self, 
            input_prompt:str =""
        ) -> str:
        """Run the full async workflow via LangGraph"""

        # Initial state (only user input is set)
        initial_state = FreecadState(input=input_prompt)
        
        # Run the graph async (executes all nodes in order)
        final_state = await self.graph.ainvoke(initial_state)

        return final_state["final_result"]
    


    async def startup(self):
        input_prompt = "Generate a random FreeCAD part plan, code, and explanation"

        # 1. Startup the rabbit_mq connection.
        retry_count = 0
        while retry_count < 5:  # Add reconnection loop
            try:
                await self.rabbitmq.rabbitmq_client.connect() 
                await self.rabbitmq.rabbitmq_client.start_consuming(
                    message_handler=self.rabbitmq.receive_from_fastapi
                )
                
                debug_msg = f"startup_orchestrator(), RabbitMQ consumer started successfully."
                self.logger.debug(debug_msg)
                break  # Exit loop if consumption starts successfully

            except Exception as e:
                retry_count += 1
                self.logger.warning(
                    f"startup_orchestrator(), Failed to start RabbitMQ consumer: '{str(e)}'. Retrying in 5s..."
                )
                time.sleep(5)  # Wait before retrying


        # 2. Endless concurrency control (throttling) for agents.
        while True: 
            async with self.concurrency_semaphore:    # Enforce max concurrent runs
                try:
                    job_dict = self.rabbitmq.job_queue.get(block=True)
                    user_id = job_dict["user_id"]
                    input_prompt = job_dict["content"]
                    
                    start_time = time.time()
                    final_result = await self.run_workflow(input_prompt)

                    _ = self.rabbitmq.send_to_fastapi(
                        user_id=user_id, 
                        content=final_result, 
                        file_paths=[]
                    )
                    
                    # Calculate execution time for dynamic throttling
                    execution_time = time.time() - start_time
                    debug_msg = f"startup(), the entire workflow is completed. It took {execution_time:.2f} seconds."  
                    debug_msg += f"\n{final_result}\n"              
                   
                    # Dynamic delay: if workflow finished fast, add extra buffer
                    dynamic_delay = max(self.MIN_ITERATION_DURATION - execution_time, 0)
                    total_delay = self.BASE_DELAY_SECONDS + dynamic_delay
                    
                    debug_msg += f"  Next run will start in {total_delay:.2f} seconds. "
                    self.logger.debug(debug_msg)

                    await asyncio.sleep(total_delay)  # Throttle: wait before next run
                    
                except Exception as e:
                    # Short delay on error (retry faster but still throttle)
                    warn_msg = f"startup(), Error in workflow: '{str(e)}'."
                    self.logger.warning(warn_msg)

                    await asyncio.sleep(10)  # Avoid immediate retry storms


    
    @staticmethod
    def startup_orchestrator():
        freecad_orchestrator = FreecadOrchestrator()

        try:
            asyncio.run(freecad_orchestrator.startup())

        except KeyboardInterrupt:
            print("[INFO] startup_orchestrator(), stopped by user's (ctrl+c).")

        except Exception as e:
            print(f"[ERROR] startup_orchestrator(), Fatal error in orchestrator agent: '{str(e)}'.")


    @staticmethod
    def usage_demo():
        print(f"\n[INFO] Initializing LangGraph FreeCAD Orchestrator, using LangGraph ...")
        orchestrator = FreecadOrchestrator()

        print("\n=== Starting FreeCAD Workflow ===")
        input_prompt = "Generate a random FreeCAD part plan, code, and explanation"
        final_result = asyncio.run(orchestrator.run_workflow(
            input_prompt=input_prompt
        ))

        print("\n=== Final Result ===")
        print(final_result)        



# --------------------------
# Demo Entry Point
# --------------------------
if __name__ == "__main__":
    # FreecadOrchestrator.usage_demo()
    FreecadOrchestrator.startup_orchestrator()