import os
import json
import traceback
from dotenv import load_dotenv

from logger.logger import Logger
from minio_fs.minio_client import MinioClient
from postgre_sql.postgre_client import PostgreClient



class FastapiMemory:
    def __init__(self):
        self.logger = Logger("fastapi_server").getLogger()
        self.minio_client = MinioClient()
        self.postgre_client = PostgreClient()

    
    def get_chat_history(
            self, 
            user_id:str="", 
            amount:int=0
        ) -> list:
        debug_msg = f"get_chat_history(), user_id='{user_id}', amount='{amount}'."
        self.logger.debug(debug_msg)

        # traceback.print_stack()
        # self.logger.debug("--------------- Above is the traceback stack -----------------")
        return []


    def add_chat_history(
            self,
            user_id:str="", 
            content:str=""
        ):
        debug_msg = f"add_chat_history(), user_id='{user_id}', content='{content}'."
        self.logger.debug(debug_msg)