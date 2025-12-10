import aiohttp
import asyncio
import mimetypes 
from pathlib import Path
import datetime
import json

BLENDER_AGENT_SERVER_URL = "http://localhost:8000"

async def send_get_request(
        target_url:str=""
    ) -> dict:
    headers = {
        "Content-Type": "application/json"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(target_url) as response:
                # Print response status and headers
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")

                # Parse JSON response (if applicable)
                if "application/json" in response.headers.get("Content-Type", ""):
                    data = await response.json()
                    print("Response is JSON")
                    return data
                else:
                    # Read raw text if not JSON
                    text = await response.text()
                    print("Response is Text:")
                    return text
                
    except Exception as e:
        return {"error": f"GET 请求异常: {str(e)}"}


async def _aiohttp_session(
    target_url:str="",   
    form_data=None    
    ):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(target_url, data=form_data) as response:
                # Print response status and headers
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")

                # Parse JSON response (if applicable)
                if "application/json" in response.headers.get("Content-Type", ""):
                    data = await response.json()
                    print("Response is JSON")
                    return data
                else:
                    # Read raw text if not JSON
                    text = await response.text()
                    print("Response is Text:")
                    return text
                
    except Exception as e:
        return {"error": f"POST 请求异常: {str(e)}"}    
    

async def send_post_request(
        target_url:str="",
        sender_id:str="",
        receiver_id:str="",
        message:str="",
        filepath:str=""
    ) -> dict:
    # 1. Double check if the filepath exist, and set the content_type.
    is_file_exist = False
    content_type = 'application/octet-stream'

    filepath = filepath.strip()
    file_path = Path(filepath)
    if ((len(filepath) > 0) and 
        (file_path.exists())
        ):
        is_file_exist = True
        mime_type, _ = mimetypes.guess_type(filepath)
        content_type = mime_type

    # 2. If is_file_exist == False, only send message text.
    form_data = aiohttp.FormData()
    form_data.add_field("sender_id", sender_id)
    form_data.add_field("receiver_id", receiver_id)
    form_data.add_field("message", message)

    # 3. If is_file_exist == True, send both message text and file.
    if is_file_exist:
        with open(filepath, 'rb') as file:
            form_data.add_field(
                'file',
                file,
                filename=file_path.name,
                content_type=content_type
            )

            # 4.1 Send HTTP/POST request.
            response_json = await _aiohttp_session(
                target_url=target_url,   
                form_data=form_data    
            )

    else:
        # 4.2 Send HTTP/POST request.
        response_json = await _aiohttp_session(
            target_url=target_url,   
            form_data=form_data    
        )
    
    return response_json


async def usage_demo():
    print(f"\n\nGET Request to {BLENDER_AGENT_SERVER_URL}")
    get_response_json = await send_get_request(BLENDER_AGENT_SERVER_URL)
    get_response_str = json.dumps(get_response_json, ensure_ascii=False, indent=2)
    print(f"The GET response is: \n{get_response_str}")

    upload_url = f"{BLENDER_AGENT_SERVER_URL.strip()}/upload/"
    print(f"\n\nPOST Request to {upload_url}")

    sender_id = "customer_service"
    receiver_id = "3d_engineer"
    curr_time = datetime.datetime.now().strftime("%Y.%m.%d.%H:%M")
    message = f"{receiver_id} 你好! 我是 {sender_id}，现在时间是 {curr_time}。"

    filepath_root = "/home/robot/langchain_20251209/server/public"
    filepaths = [
        f"{filepath_root}/image/Bay.jpeg",
        f"{filepath_root}/image/Forrest.jpeg",
        f"{filepath_root}/audio/出现又离开.MP3",
        f"{filepath_root}/video/awesome_movie.mp4",
        f"{filepath_root}/pdf/paper.pdf"
    ]
    post_response_json = await send_post_request(
        target_url=upload_url, 
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=message,
        filepath=filepaths[3]
    )
    post_response_str = json.dumps(post_response_json, ensure_ascii=False, indent=2)
    print(f"The POST response is: \n{post_response_str}\n\n")

if __name__ == "__main__":
    asyncio.run(usage_demo())
