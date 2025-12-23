import os
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from langchain_core.documents import Document
from chromadb import HttpClient  
from chromadb.config import Settings

from logger.logger import Logger

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
    

class ChromaClient:
    def __init__(self):
        self.logger = Logger("chroma_search").getLogger()
        self.embedding_model = MultilingualEmbedding()

        self.collection_name = ""
        self.http_client = None
        self.chroma_connection = None

        # Disable proxies
        os.environ["http_proxy"] = "" 
        os.environ["https_proxy"] = ""
        os.environ["all_proxy"] = ""
        os.environ["ALL_PROXY"] = ""


    def start_connection(
            self,
            collection_name:str=""        
        ) -> Chroma:
        self.collection_name = collection_name.strip()

        try:
            # Create or load collection using LangChain's Chroma wrapper
            self.http_client = HttpClient(host="localhost", port=5566)

            self.chroma_connection = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                client=self.http_client,  
                client_settings=Settings(  
                    anonymized_telemetry=False
                )
            )

            debug_msg = f"connect(), successfully set up the Chroma connection to collection '{self.collection_name}'. \n"
            debug_msg += f"  If the collection '{self.collection_name}' already exists, simply connect to it, "
            debug_msg += f"without any reset/deleted/modified. \n"
            debug_msg += f"  If the collection '{self.collection_name}' doesn't exist, create a new one."
            self.logger.debug(debug_msg)
            return self.chroma_connection
        
        except Exception as e:
            warn_msg = f"connect(), following exception was thrown when setting up the connection to "
            warn_msg += f"collection '{self.collection_name}': '{str(e)}'."
            self.logger.warning(warn_msg)
            return None


    def stop_connection(
            self,
            collection_name:str=""        
        ):
        collection_name = collection_name.strip()
        if ((collection_name != self.collection_name) or 
            (collection_name != self.chroma_connection._collection.name)
            ):
            warn_msg = f"stop_connection(), the input collection_name '{collection_name}' doesn't match \n"
            warn_msg += f"  self.collection_name '{self.collection_name}' or \n"
            warn_msg += f"  self.chroma_connection._collection.name '{self.chroma_connection._collection.name}'."
            return

        try:
            # 1. Delete the collection.
            if self.chroma_connection._collection:
                self.chroma_connection.delete_collection()

            # 2. Release HTTP client resources (Chroma v0.4+ has explicit cleanup)
            if hasattr(self.http_client, 'close'):
                self.http_client.close() 
            print("Chroma HTTP client closed.")

            # 3. Nullify references (garbage collection)
            self.collection_name = ""
            self.http_client = None
            self.chroma_connection = None
            print("Chroma connection fully cleaned up.")

            debug_msg = f"stop_connection(), successfully 1. deleted collection '{self.chroma_connection._collection.name}', \n"
            debug_msg += f"  2. close chroma http client, \n"
            debug_msg += f"  3. set the self.collection_name, self.http_client, self.chroma_connection to empty string and none."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"stop_connection(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def delete_collection(
            self,
            collection_name:str=""
        ):
        collection_name = collection_name.strip()
        if collection_name != self.collection_name:
            _ = self.start_connection(
                    collection_name=collection_name    
                )

        try:
            if self.chroma_connection._collection:
                self.chroma_connection.delete_collection()

        except Exception as e:
            warn_msg = f"delete_collection(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def add_documents(
            self,
            documents:list=[]
        ):
        self.chroma_connection.add_documents(
            documents=documents
        )
        debug_msg = f"add_documents(), successfully add {len(documents)} to collection '{self.collection_name}'."
        self.logger.debug(debug_msg)


    def delete_documents(
            self,
            metadata_key:str="",
            metadata_value:str=""
        ):
        try:
            self.chroma_connection.delete(
                where={metadata_key: metadata_value} 
            )

            debug_msg = f"delete_documents(), successfully deleted those documents from collection '{self.collection_name}', "
            debug_msg += f"whose metadata field '{metadata_key}' is '{metadata_value}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"delete_documents(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)


    def search_documents(
            self,
            search_query:str="",
            metadata_filter:dict={},
            result_amount:int=1
        ) -> list:
        try:
            score_results = []
            if len(metadata_filter) > 0:
                score_results = self.chroma_connection.similarity_search_with_score(
                    query=search_query,
                    filter=metadata_filter,
                    k=result_amount
                )    
            else:
                score_results = self.chroma_connection.similarity_search_with_score(
                    query=search_query,
                    k=result_amount
                )                          

            debug_msg = f"search_documents(), searched chroma for query '{search_query}', "
            debug_msg += f"got {len(score_results)} results, each result consists of (doc, score)."
            self.logger.debug(debug_msg)
            return score_results
        
        except Exception as e:
            warn_msg = f"search_documents(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []


    @staticmethod
    def usage_demo():
        # --------------------------
        # 1. Initialize chroma connection and document collection.
        # --------------------------
        chroma_client = ChromaClient()

        collection_name = "demo_chroma_collection"
        _ = chroma_client.start_connection(
            collection_name=collection_name    
        )

        # --------------------------
        # 2. Add Documents via LangChain
        # --------------------------
        documents = [
            Document(
                page_content="人工智能（AI）代理可以自动处理任务",
                metadata={"language": "chinese", "topic": "AI"}
            ),
            Document(
                page_content="AI agents can automate tasks like planning and execution",
                metadata={"language": "english", "topic": "AI"}
            ),
            Document(
                page_content="Chroma向量数据库支持多语言文本检索",
                metadata={"language": "chinese", "topic": "Chroma"}
            ),
            Document(
                page_content="Chroma vector database supports multilingual text search",
                metadata={"language": "english", "topic": "Chroma"}
            ),
            Document(
                page_content="Python执行器可以运行用户定义的代码片段",
                metadata={"language": "chinese", "topic": "Python"}
            )
        ]

        # Add documents to Chroma through LangChain
        chroma_client.add_documents(documents=documents)
        print(f"\n[INFO] Added {len(documents)} documents via LangChain! \n")


        # --------------------------
        # 3. Search via LangChain (Similarity Search)
        # --------------------------
        # Example 1: Chinese query
        chinese_query = "什么是Chroma向量数据库？"
        chinese_results = chroma_client.search_documents(
            search_query=chinese_query,
            result_amount=3
        )
        print("\n[INFO] === Chinese Search Results ===")
        for i, result in enumerate(chinese_results):
            res = result[0]
            print(f"Rank {i+1}: {res.page_content} (Topic: {res.metadata['topic']}) (Score: {result[1]:.4f})")
        print("")

        # Example 2: English query with filtering
        english_query = "How do AI agents work?"
        english_results = chroma_client.search_documents(
            search_query=english_query,
            metadata_filter={"language": "english"},
            result_amount=3
        )
        print("\n[INFO] === English Search Results (Filtered) ===")
        for i, result in enumerate(english_results):
            res = result[0]
            print(f"Rank {i+1}: {res.page_content} (Topic: {res.metadata['topic']}) (Score: {result[1]:.4f})")
        print("")

        # Example 3: Search with scores
        score_results = chroma_client.search_documents(
            search_query="Python执行器的功能"
        )
        print("\n[INFO] === Search with Score ===")
        doc, score = score_results[0]
        print(f"Content: {doc.page_content}")
        print(f"Similarity Score: {score:.4f}")
        print("")

        # Example 4: Delete documents
        metadata_key="topic"
        metadata_value="Python"
        chroma_client.delete_documents(
            metadata_key=metadata_key,
            metadata_value=metadata_value
        )
        print("\n[INFO] === Delete document ===")
        metadata_filter = {metadata_key: metadata_value}
        print(f"Filter: '{metadata_filter}'")
        print("")


        # Example 5: Search with scores, again, expected different result.
        score_results = chroma_client.search_documents(
            search_query="Python执行器的功能"
        )
        print("\n[INFO] === Search with Score ===")
        doc, score = score_results[0]
        print(f"Content: {doc.page_content}")
        print(f"Similarity Score: {score:.4f}")
        print("")

        # Example 6: Delete collection
        chroma_client.delete_collection(
            collection_name=collection_name
        )
        print("\n[INFO] === Delete collection ===")
        print(f"Collection: '{chroma_client.collection_name}'. \n")



if __name__ == "__main__":
    """
    $ pwd
      /home/robot/aiBlender/aiBlender_20251218/server
    $ python3 chroma_search/chroma_vdb.py
    """
    ChromaClient.usage_demo()




