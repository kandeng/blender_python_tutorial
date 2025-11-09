import os
import sys
import bpy


class BlendRetriever:
    """
    To retrieve objects from a .blend file.
    """
    def __init__(self):
        self.logger = None
        
        try:
            from logger.logger import Logger
            self.logger = Logger("AssetGateway").getLogger()
            self.logger.info(f"BlendRetriever class initialized.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize BlendRetriever class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize BlendRetriever class, error message: '{str(e)}'")


    def retrieve_object(
            self, 
            blend_filepath: str="",
            object_name: str=""
        ) -> object:

        # 1. Validation Check: Ensure the source file exists
        if not os.path.exists(blend_filepath):
            warn_msg = f"retrieve_object(), Source .blend file not found at path: '{blend_filepath}'."
            self.logger.warning(warn_msg)
            return None
        blend_filepath = bpy.path.abspath(blend_filepath)

        # 2. This is not a standard filepath, but a Blender library path. 
        blend_object_path = os.path.join(blend_filepath, "Object")

        # 3. Execute the Append operation
        try:
            # The Append operator copies the object and automatically brings in all 
            # data blocks it references (Mesh, Materials, GeometryNodeTree, etc.).
            bpy.ops.wm.append(
                filepath=os.path.join(blend_object_path, object_name),
                directory=blend_object_path,
                filename=object_name
            )

            retrieved_obj = bpy.data.objects.get(object_name)
            
            # FIX: If the object was renamed (e.g., 'Suzanne' -> 'Suzanne.001') due to a conflict, 
            if retrieved_obj is None:
                for idx, obj in enumerate(bpy.data.objects):
                    self.logger.debug(f"retrieve_object(), [{idx}] obj.name='{obj.name}'")

                    # Check if the object name starts with the target name (e.g., 'Suzanne.001')
                    if obj.name.startswith(object_name):
                        retrieved_obj = obj
                        self.logger.debug(f"retrieve_object(), Object was renamed due to conflict. Now tracking '{retrieved_obj.name}'.")
                        break

            if retrieved_obj:
                info_msg = f"retrieve_object(), Successfully retrieving object '{object_name}' "
                info_msg += f"from .blend file '{blend_filepath}'."
                self.logger.info(info_msg)
                return retrieved_obj
            else:
                warn_msg = f"retrieve_object(), Cannot retrieve object '{object_name}' "
                warn_msg += f"from .blend file '{blend_filepath}'. The reason is yet to know."
                self.logger.warning(warn_msg)
                return None

        except Exception as e:
            warn_msg = f"retrieve_object(), Cannot retrieve object '{object_name}' "
            warn_msg += f"from .blend file '{blend_filepath}'. "
            warn_msg += f"\n\t The error message is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return None
        


    @staticmethod
    def usage_demo():
        SOURCE_BLEND_FILE = "/home/robot/polygoniq_asset_packs/botaniq_full/blends/models/plants/bq_Tree_Citrus-medica_A_spring-summer-autumn.blend" 
        TARGET_OBJECT_NAME = "bq_Tree_Citrus-medica_A_spring-summer-autumn" 

        blend_retriever = BlendRetriever()
        retrieved_obj = blend_retriever.retrieve_object(
            blend_filepath=SOURCE_BLEND_FILE,
            object_name=TARGET_OBJECT_NAME
        )

        if retrieved_obj:
            bpy.ops.object.select_all(action='DESELECT')
            retrieved_obj.select_set(True)
            bpy.context.view_layer.objects.active = retrieved_obj

            blend_retriever.logger.info(f"usage_demo(), Object '{retrieved_obj.name}' is now selected and active.")
 
            # Show any relevant material/node information
            if retrieved_obj.data and retrieved_obj.data.materials:
                material_str = ', '.join([m.name for m in retrieved_obj.data.materials])
                blend_retriever.logger.info(f"usage_demo(), Attached Materials: '{material_str}'.")

            if retrieved_obj.modifiers.get('GeometryNodes'):
                blend_retriever.logger.info(f"usage_demo(), GeometryNodes modifier found and applied.")

        else:
            blend_retriever.logger.warning(f"usage_demo(), Failed to find object starting with '{retrieved_obj}'.")
