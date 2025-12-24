import os
import json
from dotenv import load_dotenv
from typing import Optional, Callable, Awaitable

from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.documents import Document
from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine  
from sentence_transformers import SentenceTransformer

from logger.logger import Logger
import traceback


# Wrap embedding model for LangChain compatibility
class MultilingualEmbedding:
    def __init__(self):
        model_cache_dir = f"/home/robot/.cache/modelscope/hub/models"
        paraphrase_multilingual_MiniLM_L12v2 = f"{model_cache_dir}/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.model = SentenceTransformer(paraphrase_multilingual_MiniLM_L12v2)
        
    def embed_documents(self, texts):
        return [self.model.encode(text) for text in texts]
    
    def embed_query(self, text):
        return self.model.encode(text)
    

class PostgreClient:
    def __init__(self):
        self.logger = Logger("postgre_sql").getLogger() 

        self.embedding_model = None
        self.user_name = ""
        self.user_password = ""
        self.database_name = ""
        self.database_connection = None
        self.vector_store_connection = None

        try:
            self.embedding_model = MultilingualEmbedding()

            debug_msg = f"PostgreClient(), PostgreClient initialized successfully."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"PostgreClient(), Failed to initialize PostgreClient, error message: '{str(e)}'."
            self.logger.warning(warn_msg)


    def connect_database(
            self,
            database_name:str="",
            user_name:str="",
            user_password:str=""
        ) -> SQLDatabase:

        if len(user_name.strip()) == 0:
            config_env = ""
            try:
                server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
                config_env = f"{server_home_dir}/config/config.env"
                load_dotenv(config_env)  

                self.user_name = os.getenv("POSTGRE_USER")
                self.user_password = os.getenv("POSTGRE_PASSWORD")

                debug_msg = f"connect_database(), got 'POSTGRE_USER/POSTGRE_PASSWORD' from config '{config_env}': "
                debug_msg += f"'{self.user_name}/{self.user_password}'"
                # self.logger.debug(debug_msg)

            except Exception as e:
                warn_msg = f"connect_database(), following exception was thrown, "
                warn_msg += f"when getting 'POSTGRE_USER' and 'POSTGRE_PASSWORD' from config file '{config_env}': '{str(e)}'."
                self.logger.warning(warn_msg)
                return None
        else:
            self.user_name = user_name.strip()
            self.user_password = user_password.strip()
            
        # e.g. "postgresql+psycopg2://robot:your_password@localhost:5432/robot_db"
        self.database_name = database_name.strip()
        postgre_url = f"postgresql+psycopg2://{self.user_name}:{self.user_password}@localhost:5432/{self.database_name}"

        try:
            engine = create_engine(
                postgre_url,
                isolation_level="AUTOCOMMIT"
            )
            database_connection = SQLDatabase(engine)
            self.database_connection = database_connection

            debug_msg = f"connect_database(), successfully connecting to database '{self.database_name}'."
            self.logger.debug(debug_msg)
            return self.database_connection
      
        except Exception as e:
            warn_msg = f"connect_database(), following exception was thrown, "
            warn_msg += f"when connecting to database '{self.database_name}': \n\t '{str(e)}'."
            self.logger.warning(warn_msg)
            return None



    def create_database(
            self,
            database_name:str=""
        ):
        try:
            # In PostgreSQL, when creating a new database, you cannot connect to a concrete database, e.g. 'robot_db',
            # instead, you must connect to a default database, including 'postgres' and 'template1'.
            curr_database_name = self.database_name
            self.connect_database(
                database_name="postgres"
            )

            # PostgreSQL requires terminating DB creation with ; (critical!)
            self.database_connection.run(f"CREATE DATABASE {database_name};")

            if curr_database_name:
                self.connect_database(
                    database_name=curr_database_name
                )  
                self.database_name = curr_database_name      

            debug_msg = f"create_database(), successfully created a new database '{database_name}'. "
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"create_database(), following exception was thrown when "
            warn_msg += f"creating a database '{self.database_name}': '{str(e)}'."
            self.logger.warning(warn_msg)



    def delete_database(
            self,
            database_name: str = ""
        ):
        if not database_name:
            warn_msg = "delete_database(), database_name is required."
            self.logger.warning(warn_msg)
            return

        try:
            curr_database_name = self.database_name
            
            # In PostgreSQL, when deleting a database, you cannot connect to a concrete database, e.g. 'robot_db',
            # instead, you must connect to a default database, including 'postgres' and 'template1'.
            self.connect_database(
                database_name="postgres"
            )
            
            # Terminate the active connections linked to the target database.
            self.database_connection.run(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{database_name}'
                AND pid <> pg_backend_pid();
            """)

            # Drop the target database.
            self.database_connection.run(f"DROP DATABASE IF EXISTS {database_name};")
            self.database_name = ""  # 重置当前数据库名

            # Recover the previous database connection if exists.
            if curr_database_name and curr_database_name != database_name:
                self.connect_database(database_name=curr_database_name)

            debug_msg = f"delete_database(), successfully deleted database '{database_name}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"delete_database(), error when deleting database '{database_name}': '{str(e)}'."
            self.logger.warning(warn_msg)


    def create_table(
            self,    
            table_name:str=""
        ):
        try:
            self.database_connection.run(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    price FLOAT NOT NULL,
                    category VARCHAR(50)
                );
            """)
            debug_msg = f"create_table(), successfully created a table '{table_name}', "
            debug_msg += f"in database '{self.database_name}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"create_table(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def drop_table(
            self,
            table_name:str=""
        ):
        try:
            self.database_connection.run(
                    f"DROP TABLE IF EXISTS {table_name};"                     
                )

            debug_msg = f"drop_table(), successfully dropped a table '{table_name}', "
            debug_msg += f"in database '{self.database_name}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"drop_table(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def insert_data(
            self,
            table_name:str="",
            data_dict:dict={}
        ):
        col_names = f""
        col_values = f""
        for idx, key_value in enumerate(data_dict.items()):
            value = None
            if isinstance(key_value[1], str):
                value = f"'{key_value[1]}'"
            else:
                value = key_value[1]

            if idx == len(data_dict) - 1:
                col_names += f"{key_value[0]}"
                col_values += f"{value}"
            else:
                col_names += f"{key_value[0]}, "
                col_values += f"{value}, "


        try:
            # Use parameterized queries to avoid SQL injection (critical!)
            query = f"INSERT INTO {table_name} ({col_names}) VALUES ({col_values});"

            # For production: Use psycopg2 directly for parameterized queries (safer)
            # Example with psycopg2:
            # import psycopg2
            # conn = psycopg2.connect(**DB_CONFIG)
            # cur = conn.cursor()
            # cur.execute("INSERT INTO products (name, price, category) VALUES (%s, %s, %s)", (name, price, category))
            # conn.commit()
            
            self.database_connection.run(query)

            debug_msg = f"insert_data(), successfully insert data to table '{table_name}' in database '{self.database_name}', "
            data_dict_str = json.dumps(data_dict, ensure_ascii=False, indent=2)
            debug_msg += f"\n{data_dict_str} \n"
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"insert_data(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def delete_data(
            self,
            table_name:str="",
            where_clause:str=""    # e.g. where_clause="name = 'Coffee Mug'"
        ):
        if not where_clause:
            warn_msg = f"delete_data(), 'where_clause' is required, to prevent from deleting all data."
            warn_msg += f"\t Do nothing this time."
            self.logger.warning(warn_msg)
            return

        try:   
            query = f"DELETE FROM {table_name} WHERE {where_clause};"
            self.database_connection.run(query)

            debug_msg = f"delete_data(), successfully delete data with where_clause: '{where_clause}', \n"
            debug_msg += f"\t from table '{table_name}' in database '{self.database_name}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"delete_data(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def search_keyword(
            self,
            table_name:str="",
            where_clause:str=""
        ) -> list:
        try:
            query = f"SELECT * FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            
            # Run query and return results (list of dictionaries)
            results = self.database_connection.run(query)

            debug_msg = f"search_keyword(), search with where_clause: '{where_clause}', \n"
            debug_msg += f"\t from table '{table_name}' in database '{self.database_name}', find the following results: "
            
            results_str = json.dumps(results, ensure_ascii=False, indent=2)
            debug_msg += f"\n{results_str} \n"
            self.logger.debug(debug_msg) 

            return results
        
        except Exception as e:
            warn_msg = f"search_keyword(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []
    


    def connect_vector_store(
            self,
            database_name:str="",
            vector_store_name:str="",
            user_name:str="",
            user_password:str=""
        ) -> PGVector:

        self.connect_database(
            database_name=database_name,   # "robot_db", "postgres"
            user_name=user_name,
            user_password=user_password
        )
            
        # e.g. "postgresql+psycopg2://robot:your_password@localhost:5432/robot_db"
        postgre_url = f"postgresql+psycopg2://{self.user_name}:{self.user_password}@localhost:5432/{self.database_name}"

        try:
            self.vector_store_name = vector_store_name.strip()
            self.vector_store_connection = PGVector.from_documents(
                documents=[],
                embedding=self.embedding_model,
                collection_name=self.vector_store_name,
                connection_string=postgre_url,
                create_extension=True   # Auto-enable pgvector
            )

            debug_msg = f"connect_vector_store(), successfully connecting to vector_store '{self.vector_store_name}'."
            self.logger.debug(debug_msg)
            return self.vector_store_connection
      
        except Exception as e:
            warn_msg = f"connect_vector_store(), following exception was thrown, "
            warn_msg += f"when connecting to vector_store '{self.vector_store_name}': \n\t '{str(e)}'."
            self.logger.warning(warn_msg)
            return None


    def insert_vector(
            self,
            content_str:str="",
            metadata_dict:dict={}
        ) -> list:
        try:
            # Add new documents/embeddings
            new_docs = [
                Document(
                    page_content=content_str, 
                    metadata=metadata_dict
                )
            ]
            inserted_ids = self.vector_store_connection.add_documents(new_docs)

            debug_msg = f"insert_vector(), insert vector {inserted_ids} to vector_store '{self.vector_store_name}' "
            debug_msg += f"in database '{self.database_name}', "

            new_docs_dict = {
                "page_content": content_str,
                "metadata": metadata_dict
            }
            new_docs_str = json.dumps(new_docs_dict, ensure_ascii=False, indent=2)
            debug_msg += f"\n{new_docs_str}\n"
            self.logger.debug(debug_msg)

            return inserted_ids  

        except Exception as e:
            warn_msg = f"insert_vector(), following exception was thrown, "
            warn_msg += f"when insert vector to vector_store '{self.vector_store_name}': \n\t '{str(e)}'."
            self.logger.warning(warn_msg)
            return []


    def delete_vector(
            self,
            ids_list:list=[]
        ):
        try:   
            # Delete specific IDs
            self.vector_store_connection.delete(ids=ids_list) 

            debug_msg = f"delete_vector(), successfully delete vectors with ids: {ids_list}, \n"
            debug_msg += f"\t from vector_store '{self.vector_store_name}' in database '{self.database_name}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"delete_vector(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def drop_vector_store(
            self,
            database_name:str="",
            vector_store_name:str=""
        ):
        try:
            curr_database_name = self.database_name
            curr_vector_store_name = self.vector_store_name

            self.connect_vector_store(
                database_name=database_name,
                vector_store_name=vector_store_name
            ) 

            self.vector_store_connection.delete_collection()

            if curr_vector_store_name and curr_vector_store_name != vector_store_name:
                self.connect_vector_store(
                    database_name=curr_database_name,
                    vector_store_name=curr_vector_store_name
                ) 

            debug_msg = f"drop_vector_store(), successfully dropped a vector store '{vector_store_name}', "
            debug_msg += f"in database '{database_name}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"drop_vector_store(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def search_semantics(
            self,
            search_query:str="",
            metadata_filter:dict={},
            result_amount:int=1
        ) -> list:
        try:
            # Semantic search
            results = self.vector_store_connection.similarity_search(
                query=search_query,
                k=result_amount,  
                filter=metadata_filter # Filter by metadata
            )

            debug_msg = f"search_semantics(), search with semantic embedding: '{search_query}', \n"
            debug_msg += f"\t from vector_store '{self.vector_store_name}' in database '{self.database_name}', "
            debug_msg += f"find the following results: \n"

            for idx, doc in enumerate(results):
                debug_msg += f"    [{idx}] {doc.page_content} (metadata: {doc.metadata})\n"
            self.logger.debug(debug_msg) 

            return results
        
        except Exception as e:
            warn_msg = f"search_semantics(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []
    


    @staticmethod
    def usage_demo():
        postgre_client = PostgreClient()

        postgre_client.create_database(
            database_name="langchain_demo"
        )

        postgre_client.connect_database(
            database_name="langchain_demo"   # "robot_db", "postgres"
        )

        postgre_client.create_table( 
            table_name="table_demo"
        )

        data_list = [
            {"name": "Laptop", "price": 999.99, "category": "Electronics"},
            {"name": "Coffee Mug", "price": 12.99, "category": "Home"}
        ]
        
        for data_point in data_list:
            postgre_client.insert_data(
                table_name="table_demo",
                data_dict=data_point
            )

        postgre_client.search_keyword(
            table_name="table_demo",
            where_clause="category = 'Home'"
        )

        postgre_client.delete_data(
            table_name="table_demo",
            where_clause="name = 'Coffee Mug'"
        )

        postgre_client.search_keyword(
            table_name="table_demo",
            where_clause="category = 'Home'"
        )


        postgre_client.connect_vector_store(
            database_name="langchain_demo",
            vector_store_name="vector_store_demo"
        ) 


        vector_ids = postgre_client.insert_vector(
            content_str="Smartphone is a portable electronic device",
            metadata_dict={"category": "Electronics"}
        )

        postgre_client.search_semantics(
            search_query="portable electronics",
            metadata_filter={"category": "Electronics"},
            result_amount=2
        )

        postgre_client.delete_vector(
            ids_list=vector_ids
        )

        postgre_client.drop_vector_store(
            database_name="langchain_demo",
            vector_store_name="vector_store_demo"
        )

        postgre_client.drop_table( 
            table_name="table_demo"
        )

        postgre_client.delete_database(
            database_name="langchain_demo"
        )


if __name__ == "__main__":
    PostgreClient.usage_demo()

