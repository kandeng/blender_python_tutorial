import os
import sys
import json
import bpy
from pathlib import Path


class FbxFileHandler:
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
            self.logger.info(f"FbxFileHandler class initialized.")

            from asset_gateway.blend_file_handler import BlendFileHandler
            self.blend_file_handler = BlendFileHandler("")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not import the classes that FbxFileHandler depends on, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not import the classes that FbxFileHandler depends on, error message: '{str(e)}'")



    def import_fbx(
            self,
            fbx_filepath: str=""
        ) -> list:
        """
        Import a .fbx file, and load its objects to both 'bpy.data.objects' and 'bpy.context.scene.objects'.

        Args:
            fbx_filepath (str): The filepath of the .fbx file.

        Returns:
            list: The list of objects loaded from the .fbx file to the 'bpy.data.objects' and 'bpy.context.scene.objects'.
        """
        # 1. Verify if the filepath is valid
        fbx_filepath = fbx_filepath.strip()
        if len(fbx_filepath) == 0:
            warn_msg = f"import_fbx(), the 'fbx_filepath' is empty."
            self.logger.warning(warn_msg)
            return []
        
        fbx_file_path = Path(fbx_filepath)
        fbx_suffix = fbx_file_path.suffix
        if fbx_suffix.lower() != ".fbx":
            warn_msg = f"import_fbx(), the '{fbx_filepath}' is not a .fbx file."
            self.logger.warning(warn_msg)
            return []        

        if not os.path.exists(fbx_filepath):    
            warn_msg = f"import_fbx(), the '{fbx_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return []                  


        # 2. Take a record the object names in 'bpy.context.scene.objects' before importing the .fbx file.
        existing_objects = set(bpy.context.scene.objects)

        # 3. Import the .fbx file
        try:
            bpy.ops.import_scene.fbx(
                filepath=fbx_filepath,
                use_image_search=True,
                use_manual_orientation=False,
                axis_forward='-Z',
                axis_up='Y'
            )
        except Exception as e:
            warn_msg = f"import_fbx(), fail to import: {fbx_filepath} file, "
            warn_msg += f"the error message is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []
    

        # 4. Get the object names that were imported from the .fbx file. 
        object_instances = [obj for obj in bpy.context.scene.objects if obj not in existing_objects]
        object_names = [obj.name for obj in object_instances]

        if len(object_names) == 0:
            warn_msg = f"import_fbx(), no objects were imported from '{fbx_filepath}' file."
            self.logger.warning(warn_msg)
            return []

        # 5. Load the textures for the objects
        texture_dirpath = os.path.dirname(os.path.abspath(fbx_filepath)) 
        self.load_materials(
            object_instances=object_instances,
            texture_dirpath=texture_dirpath
        )

        # 6. Print out the log info, and return object_names.
        info_msg = f"import_fbx(), successfully imported: {fbx_filepath},"
        object_names_str = json.dumps(object_names, ensure_ascii=False, indent=2)
        info_msg += f"with following objects: \n{object_names_str}\n"
        self.logger.info(info_msg)

        return object_names
    

    def load_materials(
            self, 
            object_instances: list=[],
            texture_dirpath: str=""
        ):
        # 1. Double check if there is a subdirectory called 'texture' or 'textures'
        for item_name in os.listdir(texture_dirpath):
            item_path = os.path.join(texture_dirpath, item_name)
            
            if os.path.isdir(item_path):
                if 'texture' in item_path.lower():
                    # self.logger.debug(f"load_materials(): item_path='{item_path}'")
                    texture_dirpath = item_path

        # 2. Apply texture for each object instances.
        for obj in object_instances:
            if obj.type == 'MESH':
                try:
                    from modeling.texture_shader import TextureShader
                    texture_shader = TextureShader(obj)
                    texture_shader.apply_texture(texture_dir=texture_dirpath)

                    info_msg = f"load_materials(), applied textures from '{texture_dirpath}' to object '{obj.name}'."
                    self.logger.info(info_msg)

                except Exception as e:
                    warn_msg = f"load_materials(), when appling textures from '{texture_dirpath}' to object '{obj.name}', "
                    warn_msg += f"following exception was thrown: '{str(e)}'."
                    self.logger.warning(warn_msg)
                    continue


    
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
        fbx_handler = FbxFileHandler() 
        
        blender_asset_dir = "/home/robot/blender_asset/quixel/Assembly_Rock_td0fefoda_8K_3d_ms"
        texture_dir = "/home/robot/blender_asset/quixel/textures"  # Example texture directory
        fbx_filepaths = [
            f"{blender_asset_dir}/td0fefoda_LOD0.fbx",
            f"{blender_asset_dir}/td0fefoda_LOD5.fbx"
        ]

        for idx in range(len(fbx_filepaths)):
            object_names = fbx_handler.import_fbx(
                    fbx_filepath=fbx_filepaths[idx]
                )
            object_instances = fbx_handler.get_objects(object_names)
            
        # Set up the sun. 
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 30.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (10.0, 10.0, 15.0) 
        bpy.context.collection.objects.link(sun_obj)

