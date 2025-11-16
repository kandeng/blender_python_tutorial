import os
import sys
import json
import bpy


class NatureGeneratorAddon:
    """
    To retrieve objects from the nature generator addon library, 
    and control its properties.
    """
    def __init__(
            self,
            texture_folder:str=""
        ):
        self.logger = None
        self.blend_file_handler = None
        self.texture_folder = texture_folder
        
        try:
            from logger.logger import Logger
            self.logger = Logger("AssetGateway").getLogger()
            self.logger.info(f"NatureGeneratorAddon class initialized.")

            from asset_gateway.blend_file_handler import BlendFileHandler
            self.blend_file_handler = BlendFileHandler("")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not import the classes that NatureGeneratorAddon depends on, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not import the classes that NatureGeneratorAddon depends on, error message: '{str(e)}'")

        try:
            if "The_Nature_Generator" in bpy.context.preferences.addons:
                self.logger.info(f"The_Nature_Generator addon is already enabled.")
            
            else:
                # Enable the addon
                bpy.ops.preferences.addon_enable(module="The_Nature_Generator")
                self.logger.info(f"The_Nature_Generator addon enabled successfully.")

            self.get_blend_filepath()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Could not initialize NatureGeneratorAddon class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize NatureGeneratorAddon class, error message: '{str(e)}'")


    def get_blend_filepath(self):
        try:
            # For addons that are enabled, we need to get the module path differently
            module = sys.modules.get("The_Nature_Generator")
            if not module:
                warn_msg = f"get_blend_filepath(), Could not access 'The_Nature_Generator' module."
                self.logger.warning(warn_msg)
                return 
                
            addon_path = os.path.dirname(module.__file__)
            asset_lib_path = os.path.join(addon_path, "asset_library", "Nature_Generator_Assets.blend")
            
            if not os.path.exists(asset_lib_path):
                warn_msg = f"get_blend_filepath(), Asset library not found at: '{asset_lib_path}'."
                self.logger.warning(warn_msg)
                return 
            
            info_msg = f"get_blend_filepath(), the 'The_Nature_Generator' asset library is in '{asset_lib_path}' file"
            self.logger.info(info_msg)
            self.blend_file_handler.blend_filepath = asset_lib_path
                
        except Exception as e:
            warn_msg = f"get_blend_filepath(), the following exception was thrown when finding "
            warn_msg += f"the 'The_Nature_Generator' asset library .blend file."
            self.logger.warning(warn_msg)



    def get_asset_categories(self) -> dict:
        """
        This function is not very useful. 
        """
        catalog_filepath = os.path.join(
                os.path.dirname(self.blend_file_handler.blend_filepath),
                "blender_assets.cats.txt"
            )

        if not os.path.exists(catalog_filepath):
            print(f"Asset catalog file not found: {catalog_filepath}")
            warn_msg = f"get_asset_categories(), Asset catalog file '{catalog_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return {}
        
        with open(catalog_filepath, 'r') as f:
            lines = f.readlines()

        version_found = False
        catalog_dict = {}
        try:
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                    
                # Skip the VERSION line
                if line.startswith('VERSION'):
                    version_found = True
                    continue

                # Parse: '2411f423-0447-4397-815e-52a7d41b3854:06_Scatter Objects/01_Plants/01_Flowers:06_Scatter Objects-01_Plants-01_Flowers'
                parts = line.split(':', 2)
                if len(parts) == 3:
                    uuid, path, name = parts
                    # For parent_path, we'll use the parent path if it exists
                    path_parts = path.split('/')
                    subcategory = catalog_dict
                    for subpath in path_parts:
                        subpath = subpath.strip()
                        if subpath in subcategory:
                            subcategory = subcategory[subpath]
                        else:
                            subcategory[subpath] = {}

        except Exception as e:
            warn_msg = f"get_asset_categories(), the following exception was thrown "
            warn_msg += f"when parsing the content of '{catalog_filepath}'."
            self.logger.warning(warn_msg)
            return {}


        info_msg = f"get_asset_categories(), '{self.blend_file_handler.blend_filepath}' "
        info_msg += f"contains the following asset categories:\n"
        catalog_dict_str = json.dumps(catalog_dict, ensure_ascii=False, indent=2)
        info_msg += f"{catalog_dict_str}"
        self.logger.info(info_msg)
        return catalog_dict


    def get_all_asset_names(self) -> dict:
        return self.blend_file_handler.get_all_asset_names()

    def load_objects(
            self,
            object_names:list=[]
        ) -> list:
        return self.blend_file_handler.load_objects(object_names)
    
    def get_objects(
            self,
            object_names:list=[]
        ) -> list:
        return self.blend_file_handler.get_objects(object_names)
    
    def display_objects(
            self,
            object_instances:list=[]
        ):
        self.blend_file_handler.display_objects(object_instances)

    def get_materials(
            self, 
            object_instance: object
        ):
        return self.blend_file_handler.get_materials(object_instance)
    
    def load_modifiers(
            self,
            object_instance: object=None,
            modifier_names:list=[]
        ):
        return self.blend_file_handler.load_modifiers(
            object_instance=object_instance,
            modifier_names=modifier_names
        ) 
    
    def get_modifiers(
            self, 
            object_instance: object
        ):
        return self.blend_file_handler.get_modifiers(object_instance)    
    
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


    def add_scatter_effect(
            self,
            object_instance: object=None,
            scatter_asset_name: str="",
            density: float=55.0
        ):
        # 1. The asset object name is like 'NG_flower_ursinia_e'
        #    However the scatter asset collection's name is like 'NG_flower_ursinia'
        _ = self.get_objects([scatter_asset_name])
        collection_names = [c.name for c in bpy.data.collections]
        scatter_collection_names = []
        for collection_name in collection_names:
            if collection_name.lower() in scatter_asset_name.lower():
                scatter_collection_names.append(collection_name)

        # Select the longest candidate to be the scatter collection. 
        self.logger.debug(f"add_scatter_effect(), scatter_collection_names: '{scatter_collection_names}'")
        scatter_collection = max(scatter_collection_names, key=len)
        self.logger.debug(f"add_scatter_effect(), scatter_collection: '{scatter_collection}'")

        # 2. Load the modifier from the external .blend file.
        modifier_list = self.load_modifiers(
            object_instance=object_instance,
            modifier_names=['NG_Scatter_Effect']
        )

        # 3. Set the attribute to the modifier for NG_Scatter_Effect 
        if len(modifier_list) > 0:
            modifier_list[0]["Socket_135"] = bpy.data.collections[scatter_collection]
            modifier_list[0]["Socket_136"] = density

        info_msg = f"add_scatter_effect(), for object '{object_instance.name}', "
        info_msg += f"add scatter collection '{scatter_collection}' with density={density}"
        self.logger.info(info_msg)

        for idx, modifier in enumerate(object_instance.modifiers):
            debug_msg = f"add_scatter_effect(), [{idx}] modifier='{modifier.name}'"
            self.logger.debug(debug_msg)

        self.logger.debug(f"\nEnumerating all the collection in 'bpy.data.collections':")
        for idx, collection in enumerate(bpy.data.collections):
            debug_msg = f"add_scatter_effect() [{idx}] collection: '{collection.name}'"
            self.logger.debug(debug_msg)
    

    def control_panel(
            self, 
            object_name: str="",
            density: float=0.0,
            size: float=0.0,
            noise_range: tuple=(0.0, 0.0)
        ):
        debug_info = f"control_panel() is not implemented yet, because for the time being we don't know yet \n"
        debug_info += f"what nodes' what attributes' what attributes need to control."
        debug_info += f"The following is a usage demo, how to set the attribute values of a shader's node."
        self.logger.debug(debug_info)

        # object_name = 'NG_Ground_Rock_Debris_Scatter_Grass_Flower_Preset'
        object_instances = self.get_objects([object_name])

        # material_name = 'NG_Rock instance Material'
        material_name = 'NG_Basic Rock Material Snow Preset'
        node_name = 'Group.001'
        material_attributes = {
            "Base Color": (1.0, 0.0, 0.0, 1.0),
            6: 22.0
        }

        self.set_material_properties(
            object_instance=object_instances[0],
            material_name=material_name,
            node_name=node_name,
            node_attributes=material_attributes
        )

        self.add_scatter_effect(
            object_instance=object_instances[0],
            scatter_asset_name="NG_flower_ursinia_e",
            density=66.6
        )

 

    @staticmethod
    def usage_demo():  
        texture_folder = "/home/robot/blender_asset/nature_generator/NatureGenerator_Texture_Options_1.1/2K_Textures/"       
        nature_generator_addon = NatureGeneratorAddon(texture_folder=texture_folder)
        asset_dict = nature_generator_addon.get_all_asset_names()

        object_names = []
        target_obj_names = ["tree", "flower", "basic_rock"]

        for obj_name in asset_dict["Objects"]:
            if len(target_obj_names) == 0:
                break
            else:
                for target_single_name in target_obj_names:
                    if target_single_name in obj_name.lower():
                        object_names.append(obj_name)
                        target_obj_names.remove(target_single_name)

        object_names_str = json.dumps(object_names, ensure_ascii=False, indent=2)
        print(f"usage_demo(), load the following objects: \n{object_names_str}\n")

        object_instances = nature_generator_addon.load_objects(object_names)
        nature_generator_addon.display_objects(object_instances)

        material_names = []
        modifier_names = []
        print(f"\n\n")
        for idx, obj_instance in enumerate(object_instances):
            material_names.append(nature_generator_addon.get_materials(obj_instance))
            modifier_names.append(nature_generator_addon.get_modifiers(obj_instance))
            print(f"\n\n")

        # "NG_Basic_Rock_Snow_Preset"
        nature_generator_addon.control_panel(object_name=object_names[2])

        