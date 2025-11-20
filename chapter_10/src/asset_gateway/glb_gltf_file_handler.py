import os
import sys
import json
import bpy
from pathlib import Path


class GlbGltfFileHandler:
    """
    To retrieve objects from the engon polygoniq addon library, 
    and control its properties.
    """
    def __init__(self):
        self.logger = None
        self.blend_file_handler = None

        try:
            from logger.logger import Logger
            self.logger = Logger("AssetGateway").getLogger()
            self.logger.info(f"GlbGltfFileHandler class initialized.")

            from asset_gateway.blend_file_handler import BlendFileHandler
            self.blend_file_handler = BlendFileHandler("")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not import the classes that GlbGltfFileHandler depends on, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not import the classes that GlbGltfFileHandler depends on, error message: '{str(e)}'")



    def import_glb_gltf(
            self,
            glb_gltf_filepath: str=""
        ) -> list:
        """
        Import a .glb or .gltf file, and load its objects to both 'bpy.data.objects' and 'bpy.context.scene.objects'.

        Args:
            glb_gltf_filepath (str): The filepath of the .glb/.gltf file.

        Returns:
            list: The list of objects loaded from the .glb/.gltf file to the 'bpy.data.objects' and 'bpy.context.scene.objects'.
        """
        # 1. Verify if the filepath is valid
        glb_gltf_filepath = glb_gltf_filepath.strip()
        if len(glb_gltf_filepath) == 0:
            warn_msg = f"import_glb_gltf(), the 'glb_gltf_filepath' is empty."
            self.logger.warning(warn_msg)
            return []
        
        glb_gltf_file_path = Path(glb_gltf_filepath)
        glb_gltf_suffix = glb_gltf_file_path.suffix
        if glb_gltf_suffix.lower() not in [".glb", ".gltf"]:
            warn_msg = f"import_glb_gltf(), the '{glb_gltf_filepath}' is not a .glb or .gltf file."
            self.logger.warning(warn_msg)
            return []        

        if not os.path.exists(glb_gltf_filepath):    
            warn_msg = f"import_glb_gltf(), the '{glb_gltf_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return []                  


        # 2. Take a record the object names in 'bpy.context.scene.objects' before importing the .glb file.
        existing_objects = set(bpy.context.scene.objects)

        # 3. Import the .glb file
        try:
            bpy.ops.import_scene.gltf(
                filepath=glb_gltf_filepath,
                import_pack_images=True,   # Pack the embedded texture images into blender 
                # import_shadows=True,       # Import shadow settings
                # import_cameras=False,      # Import cameras from the GLTF/GLB
                # import_lights=False        # Import lights from the GLTF/GLB
            )
        except Exception as e:
            warn_msg = f"import_glb_gltf(), fail to import: {glb_gltf_filepath} file, "
            warn_msg += f"the error message is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []
    

        # 4. Get the object names that were imported from the .glb file. 
        object_names = [obj.name for obj in bpy.context.scene.objects if obj not in existing_objects]

        if len(object_names) == 0:
            warn_msg = f"import_glb_gltf(), no objects were imported from '{glb_gltf_filepath}' file."
            self.logger.warning(warn_msg)
            return []

        # 5. Print out the log info, and return object_names.
        info_msg = f"import_glb_gltf(), successfully imported: {glb_gltf_filepath},"
        object_names_str = json.dumps(object_names, ensure_ascii=False, indent=2)
        info_msg += f"with following objects: \n{object_names_str}\n"
        self.logger.info(info_msg)

        return object_names
    

    
    def get_objects(
            self,
            object_names:list=[]
        ) -> list:
        return self.blend_file_handler.get_objects(object_names)

    def get_materials(
            self, 
            object_instance: object
        ):
        return self.blend_file_handler.get_materials(object_instance)

    def set_material_properties(
            self, 
            object_instance: object=None,
            material_name: str="",
            node_name: str="",
            node_attributes: dict={}
        ):
        self.blend_file_handler.set_material_properties(
            object_instance=object_instance,
            material_name=material_name,
            node_name=node_name,
            node_attributes=node_attributes
        )      

    def set_modifier_properties(
            self, 
            object_instance: object=None,
            modifier_name: str="",
            node_name: str="",
            node_attributes: dict={}
        ):
        self.blend_file_handler.set_modifier_properties(
            object_instance=object_instance,
            modifier_name=modifier_name,
            node_name=node_name,
            node_attributes=node_attributes
        )



    @staticmethod
    def usage_demo():
        glb_gltf_handler = GlbGltfFileHandler() 
        
        blender_asset_dir = "/home/robot/blender_asset"
        glb_gltf_filepaths = [
            f"{blender_asset_dir}/sketchfab/flower_rose/model.glb",
            f"{blender_asset_dir}/sketchfab/flower_rose/model_out/model.gltf"
        ]

        for idx in range(len(glb_gltf_filepaths)):
            object_names = glb_gltf_handler.import_glb_gltf(
                glb_gltf_filepath=glb_gltf_filepaths[idx]
            ) 

            object_instances = glb_gltf_handler.get_objects(object_names)

            # Set up the sun. 
            bpy.context.scene.render.engine = 'CYCLES'
            sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
            sun_data.energy = 30.0  # Strength (irradiance in Watts/m²)
            sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
            sun_obj.location = (15, 10.0, 50.0) 
            bpy.context.collection.objects.link(sun_obj)




