import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain_community.chat_models import ChatTongyi

from logger.logger import Logger



# Input schema for planner agent (parameter validation)
class FreecadPlannerInput(BaseModel):
    part_type: str = Field(
        description="Type of FreeCAD part to plan (e.g., 'cube', 'cylinder', 'gear'); leave empty for random",
        default=""
    )

# Planner Agent (async-first: _arun() as core logic)
class FreecadPlanner(BaseTool):
    name: str = "FreecadPlanner"
    description: str = "Generate a step-by-step modeling plan for a random FreeCAD part (uses qwen-plus)"
    args_schema: type[BaseModel] = FreecadPlannerInput
    ai_model: ChatTongyi = Field(default=None)
    logger: Logger = Field(default=None)

    def __init__(self):
        super().__init__()

        try:
            self.logger = Logger("langchain_agent").getLogger() 

            # Load environment variables
            server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
            config_env = f"{server_home_dir}/config/config.env"
            load_dotenv(config_env)

            model_key = os.getenv("MODEL_KEY")
            model_name = os.getenv("MODEL_NAME")

            # Initialize qwen-plus for async calls
            self.ai_model = ChatTongyi(
                dashscope_api_key=model_key,
                model_name=model_name,
                temperature=0.7,  # Higher temp for randomness
                max_tokens=500
            )

        except Exception as e:
            warn_msg = f"FreecadPlanner(), following exception was thrown: \n"
            warn_msg += f"\t '{str(e)}'"
            self.logger.warning(warn_msg)



    # Sync fallback (only for legacy compatibility, not used by orchestrator)
    def _run(
            self, 
            part_type:str=""
        ) -> str:
        return asyncio.run(self._arun(part_type))
    

    # Core async logic (orchestrator calls this directly via arun())
    async def _arun(
            self, 
            part_type:str=""
        ) -> str:
        """Async core logic: Generate random FreeCAD modeling plan"""

        # Random part if no type provided (demo randomness)
        random_parts = ["cube", "cylinder", "gear", "bolt", "nut", "pyramid"]
        target_part = part_type if part_type else random_parts[hash(os.urandom(1)) % len(random_parts)]

        # Prompt for qwen-plus (demo task: generate modeling plan)
        prompt = f"""Generate a concise, step-by-step modeling plan for a {target_part} in FreeCAD:
        1. Keep steps simple (3-5 steps)
        2. Use FreeCAD terminology (e.g., Part Workbench, Sketch, Extrude)
        3. Output only the plan (no extra text)"""

        # Async call to qwen-plus (ainvoke instead of invoke)
        response = await self.ai_model.ainvoke(prompt)
        return f"{response.content}"