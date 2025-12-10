import asyncio
import aiohttp
import json
import os
from datetime import datetime



async def test_qwen3_coder(req: str=""):
    url = "http://localhost:8000/receive"

    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y.%m.%d.%H:%M")
    
    test_data = {
        "text": req,
        "metadata": {
            "timestamp": formatted_time
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_data) as response:
                status = response.status
                try:
                    result = await response.json()
                except:
                    result = {"error": "Failed to parse JSON response", "text": await response.text()}
                
                print(f"Qwen3 Coder Response Status: {status}")
                print(f"Qwen3 Coder Response Data: {json.dumps(result, indent=2)}")
                
                return status, result
    except Exception as e:
        print(f"Error in qwen3 coder test: {e}")
        return None, {"error": f"Error: {e}"}


if __name__ == "__main__":
    requests = [
        "Can you please tell me what model you are using, and its version number? Are you Qwen3 or the previous verion?",
        "Can you please write a python script, to list all the prime numbers between 0 and 1000?"
    ]
    
    # Tell the name and version of the Qwen AI model.
    print("\n Asking the name and the version of the Qwen3 AI model:")
    asyncio.run(test_qwen3_coder(requests[0]))

    # Test with a coding request.
    print("\n Testing the coding capacity of the Qwen3 AI model:")
    asyncio.run(test_qwen3_coder(requests[1]))