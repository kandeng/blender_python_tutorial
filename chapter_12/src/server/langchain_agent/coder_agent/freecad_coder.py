import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain_community.chat_models import ChatTongyi

from logger.logger import Logger



# Input schema for coder agent
class FreecadCoderInput(BaseModel):
    modeling_plan: str = Field(
        description="Step-by-step FreeCAD modeling plan (from FreecadPlanner)",
        min_length=10  # Ensure plan is valid
    )

# Coder Agent (async-first)
class FreecadCoder(BaseTool):
    name: str = "FreecadCoder"
    description: str = "Generate FreeCAD Python code from a modeling plan (uses qwen-plus)"
    args_schema: type[BaseModel] = FreecadCoderInput
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
                temperature=0.3,  # Lower temp for deterministic code
                max_tokens=800
            )

        except Exception as e:
            warn_msg = f"FreecadCoder(), following exception was thrown: \n"
            warn_msg += f"\t '{str(e)}'"
            self.logger.warning(warn_msg)



    # Sync fallback (legacy only)
    def _run(self, modeling_plan: str) -> str:
        return asyncio.run(self._arun(modeling_plan))
    


    # Core async logic (orchestrator calls this)
    async def _arun(self, modeling_plan: str) -> str:
        """Async core logic: Generate FreeCAD code from plan"""
        prompt = f"""Generate minimal, runnable FreeCAD Python code for this modeling plan:
        {modeling_plan}
        
        Rules:
        1. Use FreeCAD's Python API (import FreeCAD, Part)
        2. Keep code simple (no extra features)
        3. Add comments for each step
        4. Output only the code (no explanations)"""

        response = await self.ai_model.ainvoke(prompt)
        return f"{response.content}"