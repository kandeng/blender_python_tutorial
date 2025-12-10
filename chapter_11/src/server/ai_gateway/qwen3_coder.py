import os
import sys
import json
from typing import Dict, Any, List
import asyncio

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger.logger import Logger
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage


class Qwen3Coder:
    """
    A simple interface to the Qwen model for code-related tasks.
    """
    MODEL_NAME = "qwen-turbo" 
    MODEL_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_KEY = "sk-e0f50dc301534b199f976f17b733ed55"
        
    def __init__(self):
        self.logger = Logger("ai_gateway").getLogger()
        self.model = None

        try:
            # Initialize Qwen model with API key and base URL
            self.model = ChatTongyi(
                dashscope_api_key=Qwen3Coder.MODEL_KEY,
                model_name=Qwen3Coder.MODEL_NAME,
                base_url=Qwen3Coder.MODEL_URL
            )
            
            info_msg = f"Qwen3Coder(), Qwen3Coder initialized successfully with model: '{Qwen3Coder.MODEL_NAME}'."
            self.logger.info(info_msg)

        except Exception as e:
            warn_msg = f"Qwen3Coder(), Failed to initialize Qwen3Coder, error message: '{str(e)}'."
            self.logger.warning(warn_msg)

    
    async def post_request(
            self, 
            user_request: str
        ) -> Dict[Any, Any]:
        """
        Process the incoming request with the Qwen model.
        """

        user_request = user_request.strip()
        if len(user_request) == 0:
            warn_msg = f"post_request(), the user_request is emptry. "
            self.logger.warning(warn_msg)
            return {}
        
        try:
            # Log the incoming request
            info_msg = f"post_request(), send the user_request '{user_request}' to Qwen model '{Qwen3Coder.MODEL_NAME}'."
            self.logger.info(info_msg)
            
            # Create messages
            messages = [
                SystemMessage(
                    content="""You are Qwen Turbo, an expert AI coding assistant. 
Your primary role is to help users with programming tasks, including:
1. Writing code in various programming languages
2. Debugging and fixing code issues
3. Explaining code concepts and best practices
4. Reviewing and optimizing code
5. Generating documentation for code
When generating code, provide complete, runnable examples with proper comments. """
                ),
                HumanMessage(
                    content=user_request
                )
            ]
            
            # Run the model asynchronously
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.invoke(messages)
            )
            
            # Format response
            response_dict = {
                "status": "success",
                "input": user_request,
                "response": result.content if hasattr(result, 'content') else str(result),
                "processed_by": "QwenCoder",
                "model": Qwen3Coder.MODEL_NAME
            }
            
            response_dict_str = json.dumps(response_dict, ensure_ascii=False, indent=2)
            info_msg = f"post_request(), response from Qwen model: \n{response_dict_str}\n"
            self.logger.info(info_msg)
            return response_dict
            
        except Exception as e:

            warn_msg = f"post_request(), Error processing request with Qwen model: '{str(e)}'."
            self.logger.warning(warn_msg)
            return {}
        


    @staticmethod
    def usage_demo():
        coder = Qwen3Coder()
        
        # Example request - more specific instruction
        example_request = f"Generate a complete Python function to calculate Fibonacci numbers recursively. "
        example_request += f"Include docstring and comments."

        # Process the request
        result = asyncio.run(coder.post_request(example_request))



# Example usage
if __name__ == "__main__":
    Qwen3Coder.usage_demo()