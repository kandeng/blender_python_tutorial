import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.tools import BaseTool
from langchain_community.chat_models import ChatTongyi

from logger.logger import Logger



# Input schema for learner agent
class FreecadLearnerInput(BaseModel):
    code_snippet: str = Field(
        description="FreeCAD Python code snippet (from FreecadCoder) to explain",
        min_length=20
    )


# Learner Agent (async-first)
class FreecadLearner(BaseTool):
    name: str = "FreecadLearner"
    description: str = "Explain FreeCAD Python code in simple terms (uses qwen-plus)"
    args_schema: type[BaseModel] = FreecadLearnerInput
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
                temperature=0.2,
                max_tokens=600
            )

        except Exception as e:
            warn_msg = f"FreecadLearner(), following exception was thrown: \n"
            warn_msg += f"\t '{str(e)}'"
            self.logger.warning(warn_msg)



    # Sync fallback (legacy only)
    def _run(self, code_snippet: str) -> str:
        return asyncio.run(self._arun(code_snippet))


    # Core async logic (orchestrator calls this)
    async def _arun(self, code_snippet: str) -> str:
        """Async core logic: Explain FreeCAD code for beginners"""
        prompt = f"""Explain this FreeCAD Python code to a beginner:
        {code_snippet}
        
        Rules:
        1. Break down each line of code
        2. Explain FreeCAD-specific functions (e.g., Part.makeBox)
        3. Use simple language (no jargon where possible)
        4. Output only the explanation (no extra text)"""

        response = await self.ai_model.ainvoke(prompt)
        return f"{response.content}"