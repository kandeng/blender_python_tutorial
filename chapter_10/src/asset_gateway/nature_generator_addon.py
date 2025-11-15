import os
import sys
import json
import bpy


class NatureGeneratorAddon:
    """
    To retrieve objects from the nature generator addon library, 
    and control its properties.
    """
    def __init__(self):
        self.logger = None
        self.blend_file_handler=None
        
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
        self.blend_file_handler.set_material_properties(
            object_instance=object_instance,
            modifier_name=modifier_name,
            node_name=node_name,
            node_attributes=node_attributes
        )
    

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

        material_name = 'NG_Rock instance Material'
        node_attributes = {
            "Rock Color": (0.0, 0.0, 0.5, 1.0),
            3: True
        }

        self.set_material_properties(
            object_instance=object_instances[0],
            material_name=material_name,
            node_name="Group.001",
            node_attributes=node_attributes
        )



    @staticmethod
    def usage_demo():        
        nature_generator_addon = NatureGeneratorAddon()
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

        object_instances = nature_generator_addon.load_objects(object_names)
        nature_generator_addon.display_objects(object_instances)

        material_names = []
        modifier_names = []
        print(f"\n\n")
        for idx, obj_instance in enumerate(object_instances):
            material_names.append(nature_generator_addon.get_materials(obj_instance))
            modifier_names.append(nature_generator_addon.get_modifiers(obj_instance))
            print(f"\n\n")

        nature_generator_addon.control_panel(object_name=object_names[1])

        """
        selected_material_name = material_names[1][1]
        print(f"Selected material for testing: '{selected_material_name}'")

        nature_generator_addon.set_material_properties(
            object_instance=object_instances[1],
            material_name=selected_material_name,
            node_name="Group.001",
            node_attributes={
                "Rock Color": (0.0, 0.0, 0.5, 1.0),
                3: True
            }
        )        
        """
