import os
import json
from dotenv import load_dotenv

from minio import Minio
from minio.error import S3Error

from logger.logger import Logger


class MinioClient:
    def __init__(self):
        self.logger = Logger("minio_fs").getLogger() 

        self.user_name = ""
        self.user_password = ""
        self.minio_url = ""
        self.minio_connection = None
        self.bucket_name = ""
        self.meta_prefix = "x-amz-meta-"

        try:
            debug_msg = f"MinioClient(), MinioClient initialized successfully."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"MinioClient(), Failed to initialize MinioClient, error message: '{str(e)}'."
            self.logger.warning(warn_msg)


    def connect_minio(
            self,
            bucket_name:str="",
            user_name:str="",
            user_password:str=""
        ) -> Minio:
        if len(user_name.strip()) == 0:
            config_env = ""
            try:
                server_home_dir = os.getenv("PWD")    # Equal to 'os.getcwd()'
                config_env = f"{server_home_dir}/config/config.env"
                load_dotenv(config_env)  

                self.user_name = os.getenv("MINIO_USER")
                self.user_password = os.getenv("MINIO_PASSWORD")
                self.minio_url = os.getenv("MINIO_URL")

                debug_msg = f"connect_minio(), got 'MINIO_USER/MINIO_PASSWORD' from config '{config_env}': "
                debug_msg += f"'{self.user_name}/{self.user_password}'"
                # self.logger.debug(debug_msg)

            except Exception as e:
                warn_msg = f"connect_minio(), following exception was thrown, "
                warn_msg += f"when getting 'MINIO_USER' and 'MINIO_PASSWORD' from config file '{config_env}': '{str(e)}'."
                self.logger.warning(warn_msg)
                return None
        else:
            self.user_name = user_name.strip()
            self.user_password = user_password.strip()
            

        self.bucket_name = bucket_name.strip()
        try:
            minio_connection = Minio(
                endpoint=self.minio_url,
                access_key=self.user_name,
                secret_key=self.user_password,
                secure=False
            )
            self.minio_connection = minio_connection

            debug_msg = f""
            if not minio_connection.bucket_exists(self.bucket_name):
                minio_connection.make_bucket(self.bucket_name)
                debug_msg = f"connect_minio(), Bucket '{self.bucket_name}' created successfully."

            debug_msg += f"connect_minio(), Connected to bucket '{self.bucket_name}' in MinIO storage successfully."
            self.logger.debug(debug_msg)
            return minio_connection
        
        except S3Error as e:
            warn_msg = f"connect_minio(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)

        except Exception as e:
            warn_msg = f"connect_minio(), unexpected exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)

        return None



    def upload_file(
            self,
            local_filepath:str="", 
            minio_filepath:str="", 
            metadata:dict={}
        ):
        """
        Enhanced upload function: support adding metadata during upload
        Args:
            metadata: Optional dict of metadata (e.g., {"author": "Alice", "category": "test"})
        """
        if not self.minio_connection:
            warn_msg = f"upload_file(), Please connect to MinIO storage first."
            self.logger.warning(warn_msg)
            return
        
        local_filepath = local_filepath.strip()
        if len(minio_filepath.strip()):
            minio_filepath = os.path.basename(local_filepath)
        
        if not os.path.exists(local_filepath):
            warn_msg = f"upload_file(), Local file '{local_filepath}' does not exist."
            self.logger.warning(warn_msg)
            return
        
        try:
            # Add metadata if provided (default to empty dict)
            upload_metadata = metadata or {}
            self.minio_connection.fput_object(
                bucket_name=self.bucket_name,
                object_name=minio_filepath,
                file_path=local_filepath,
                metadata=upload_metadata
            )

            debug_msg = f"upload_file(), File '{minio_filepath}' was uploaded successfully to bucket '{self.bucket_name}'."
            if len(upload_metadata) > 0:
                debug_msg += f"\n    with metadata: {upload_metadata}."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"upload_file(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)



    def download_file(
            self,
            minio_filepath:str="", 
            local_filepath:str=""
        ) -> str:
        """
        Download a file from MinIO to a local directory
        Args:
            minio_filepath: The filepath in MinIO to download
            local_filepath: Local filepath to save the downloaded file (default: /tmp/minio/my_file.txt)
        Returns:
            Local filepath if successful, empty string otherwise.
        """
        if not self.minio_connection:
            warn_msg = f"download_file(), Please connect to MinIO storage first."
            self.logger.warning(warn_msg)
            return ""    
        
        # Create full local path preserving MinIO's object structure
        local_filepath = local_filepath.strip()
        if len(local_filepath) == 0:
            tmp_minio_dir = "/tmp/minio"
            os.makedirs(tmp_minio_dir, exist_ok=True) 

            local_filepath = os.path.basename(minio_filepath)
            local_filepath = f"{tmp_minio_dir}/{local_filepath}"
        else:
            local_dirpath = os.path.dirname(local_filepath)
            os.makedirs(local_dirpath, exist_ok=True) 

        try:
            # Verify file exists in MinIO
            self.minio_connection.stat_object(
                bucket_name=self.bucket_name, 
                object_name=minio_filepath
            )
            
            # Download the file
            self.minio_connection.fget_object(
                bucket_name=self.bucket_name,
                object_name=minio_filepath,
                file_path=local_filepath
            )

            debug_msg = f"download_file(), File '{minio_filepath}' has been downloaded to '{local_filepath}'."
            self.logger.debug(debug_msg)
            return local_filepath
        
        except Exception as e:
            warn_msg = f"download_file(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return ""



    def delete_file(
            self,
            minio_filepath:str=""
        ):
        if not self.minio_connection:
            warn_msg = f"delete_file(), Please connect to MinIO storage first."
            self.logger.warning(warn_msg)
            return 
        
        try:
            self.minio_connection.stat_object(
                bucket_name=self.bucket_name, 
                object_name=minio_filepath
            )
            self.minio_connection.remove_object(
                bucket_name=self.bucket_name, 
                object_name=minio_filepath
            )

            debug_msg = f"delete_file(), File '{minio_filepath}' has been deleted."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"delete_file(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return ""



    def update_metadata(
            self,
            minio_filepath:str="", 
            new_metadata:dict={}
        ):
        """
        Update metadata by downloading, deleting, and re-uploading the file.

        Args:
            minio_filepath: Name of the file in MinIO to update
            new_metadata: Dict of metadata to update (existing keys overwritten, new keys added)
        """
        if not self.minio_connection:
            warn_msg = f"update_metadata(), Please connect to MinIO storage first."
            self.logger.warning(warn_msg)
            return False

        if not isinstance(new_metadata, dict):
            warn_msg = f"update_metadata(), new_metadata '{new_metadata}' must be a dict."
            self.logger.warning(warn_msg)
            return False


        tmp_local_filepath = ""
        try:
            # Step 1: Get current metadata from existing object
            obj_stat = self.minio_connection.stat_object(
                bucket_name=self.bucket_name, 
                object_name=minio_filepath
            )

            
            current_metadata = {
                k.lower().replace(self.meta_prefix, ""): v 
                for k, v in obj_stat.metadata.items() 
                if k.lower().startswith(self.meta_prefix)
            }

            # Step 2: Merge new metadata with existing (overwrite/add keys)
            for key, value in new_metadata.items():
                normalized_key = key.lower().replace(" ", "_")
                if value == "":  # Delete key if value is empty string
                    current_metadata.pop(normalized_key, None)
                else:
                    current_metadata[normalized_key] = str(value)

            # Step 3: Download file to temporary directory
            tmp_minio_dir = "/tmp/minio"
            os.makedirs(tmp_minio_dir, exist_ok=True) 

            local_name = os.path.basename(minio_filepath)
            tmp_local_filepath = f"{tmp_minio_dir}/{local_name}"

            tmp_local_filepath = self.download_file(
                minio_filepath=minio_filepath, 
                local_filepath=tmp_local_filepath
            )
            if not tmp_local_filepath or not os.path.exists(tmp_local_filepath):
                warn_msg = f"update_metadata(), Failed to download file '{minio_filepath}' for metadata updating."
                self.logger.warning(warn_msg)
                return False

            # Step 4: Delete original file from MinIO
            try:
                self.minio_connection.remove_object(
                    bucket_name=self.bucket_name, 
                    object_name=minio_filepath
                )
            except Exception as e:
                warn_msg = f"update_metadata(), Failed to delete original file '{minio_filepath}': '{str(e)}'."
                self.logger.warning(warn_msg)
                return False

            # Step 5: Re-upload with updated metadata
            self.upload_file(
                local_filepath=tmp_local_filepath, 
                minio_filepath=minio_filepath, 
                metadata=current_metadata
            )

            # Step 6: Verify update
            updated_stat = self.minio_connection.stat_object(
                bucket_name=self.bucket_name, 
                object_name=minio_filepath
            )
            updated_metadata = {
                k.lower().replace(self.meta_prefix, ""): v 
                for k, v in updated_stat.metadata.items() 
                if k.lower().startswith(self.meta_prefix)
            }

            debug_msg = f"update_metadata(), the metadata of '{minio_filepath}' has been updated to: "
            debug_msg += f"\n\t {updated_metadata}"
            self.logger.debug(debug_msg)
            return True

        except Exception as e:
            warn_msg = f"update_metadata(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return False

        finally:
            # Clean up temporary files
            if tmp_local_filepath and os.path.exists(tmp_local_filepath):
                try:
                    os.remove(tmp_local_filepath)
                except Exception as e:
                    warn_msg = f"update_metadata(), Failed to clean up temporary files '{tmp_local_filepath}', "
                    warn_msg += f"\n   following exception was thrown: '{str(e)}'."
                    self.logger.warning(warn_msg)
        


    def search_by_filename(
            self,
            filename_substr:str=""
        ) -> list:

        if not self.minio_connection:
            warn_msg = f"search_by_filename(), Please connect to MinIO storage first."
            self.logger.warning(warn_msg)
            return []

        matched_files = []
        try:
            objects = self.minio_connection.list_objects(
                bucket_name=self.bucket_name, 
                recursive=True
            )

            for obj in objects:
                file_name = obj.object_name
                if filename_substr in file_name:
                    matched_files.append(file_name)
            
            if matched_files:
                debug_msg = f"search_by_filename(), Found {len(matched_files)} matched files as following: "
                matched_files_str = json.dumps(matched_files, ensure_ascii=False, indent=2)
                debug_msg += f"{matched_files_str}\n"
                self.logger.debug(debug_msg)

            else:
                debug_msg = f"search_by_filename(), No files matched '{filename_substr}'."
                self.logger.debug(debug_msg)

            return matched_files
        
        except Exception as e:
            warn_msg = f"search_by_filename(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []



    def search_by_metadata(
            self, 
            metadata_filter:dict={}
        ) -> list:

        if not self.minio_connection:
            warn_msg = f"search_by_metadata(), Please connect to MinIO storage first."
            self.logger.warning(warn_msg)
            return []
        
        if not isinstance(metadata_filter, dict) or len(metadata_filter) == 0:
            warn_msg = f"search_by_metadata(), Error: metadata_filter '{metadata_filter}' must be a non-empty dict."
            self.logger.warning(warn_msg)
            return []
        
        matched_files = []
        try:
            objects = self.minio_connection.list_objects(
                bucket_name=self.bucket_name, 
                recursive=True
            )

            for obj in objects:
                file_name = obj.object_name
                obj_stat = self.minio_connection.stat_object(
                    bucket_name=self.bucket_name, 
                    object_name=file_name                    
                )
                obj_metadata = {
                    k.lower().replace(self.meta_prefix, "").lower(): v.lower() 
                    for k, v in obj_stat.metadata.items() 
                    if k.lower().startswith(self.meta_prefix)    # if k.startswith("X-Amz-Meta-")
                }
                
                normalized_filter = {
                    k.lower().replace(" ", "_"): str(v).lower() 
                    for k, v in metadata_filter.items()
                }

                print(f"\n[debug] obj_stat.metadata={obj_stat.metadata}\n")
                print(f"[debug] obj_metadata={obj_metadata}\n")
                print(f"[debug] normalized_filter={normalized_filter}\n")
                
                
                match = any(obj_metadata.get(k) == v for k, v in normalized_filter.items())   
                if match:
                    matched_files.append({
                        "file_name": file_name,
                        "metadata": obj_metadata
                    })

            if matched_files:
                debug_msg = f"search_by_metadata(), Found {len(matched_files)} matched files as following: "
                matched_files_str = json.dumps(matched_files, ensure_ascii=False, indent=2)
                debug_msg += f"{matched_files_str}\n"
                self.logger.debug(debug_msg)

            else:
                debug_msg = f"search_by_filename(), No files matched '{metadata_filter}'."
                self.logger.debug(debug_msg)
            
            return [item["file_name"] for item in matched_files]
        
        except Exception as e:
            warn_msg = f"search_by_filename(), following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []

    

    @staticmethod
    def usage_demo():
        minio_client = MinioClient()
        if not minio_client:
            exit(1)

        minio_client.connect_minio(
            bucket_name="minio-bucket-demo"
        ) 
        
        # Test upload with metadata
        local_filepath = "/home/robot/aiBlender/aiBlender_20251218/server/public/image/Bay.jpeg"  
        minio_filepath = "asset/image/Bay_demo.jpeg"
        minio_client.upload_file(
            local_filepath=local_filepath,
            minio_filepath=minio_filepath,
            metadata={"author": "Alice", "category": "test", "version": "1.0"}
        )
        
        # Test metadata update
        minio_client.update_metadata(
            minio_filepath=minio_filepath,
            new_metadata={"author": "Bob", "version": "2.0", "status": "updated"}
        )
        
        # Test metadata search
        minio_client.search_by_metadata(
            metadata_filter={"author": "Bob", "version": "2.0"}
        )
        minio_client.search_by_metadata(
            metadata_filter={"category": "test"}
        )
        
        # Test download
        minio_client.download_file(
            minio_filepath=minio_filepath, 
            local_filepath="/home/robot/Downloads/downloaded_bay.jpg"
        )
        
        # Cleanup
        minio_client.delete_file(
            minio_filepath=minio_filepath
        )


if __name__ == "__main__":
    MinioClient.usage_demo()

