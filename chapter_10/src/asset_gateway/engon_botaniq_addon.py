import os
import sys
import json
import bpy
from pathlib import Path


class EngonBotaniqAddon:
    """
    To retrieve objects from the engon polygoniq addon library, 
    and control its properties.
    """
    def __init__(self):
        self.logger = None
        self.blend_file_handler = None
        self.asset_pack_folders = []
        self.asset_pack_blend_filepaths = {}

        try:
            from logger.logger import Logger
            self.logger = Logger("AssetGateway").getLogger()
            self.logger.info(f"EngonBotaniqAddon class initialized.")

            from asset_gateway.blend_file_handler import BlendFileHandler
            self.blend_file_handler = BlendFileHandler("")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not import the classes that EngonBotaniqAddon depends on, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not import the classes that EngonBotaniqAddon depends on, error message: '{str(e)}'")

        try:
            if "engon" in bpy.context.preferences.addons:
                self.logger.info(f"engon addon is already enabled.")
            
            else:
                # Enable the addon
                bpy.ops.preferences.addon_enable(module="engon")
                self.logger.info(f"engon addon enabled successfully.")

            self.asset_pack_folders = self.get_asset_packs()
            self.asset_pack_blend_filepaths = self.get_asset_categories()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Could not initialize EngonBotaniqAddon class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize EngonBotaniqAddon class, error message: '{str(e)}'")


    def get_asset_packs(self) -> list:
        """
        Get installation paths of engon asset packs from addon preferences.
        
        Returns:
            The installation file directories for all registered asset packs.
        """
        try:
            # Access the engon addon preferences
            prefs = bpy.context.preferences.addons["engon"].preferences
            
            # Get the registered asset packs and their installation paths
            asset_pack_paths = []
            for pack in prefs.general_preferences.pack_info_search_paths:
                # For each search path, get discovered asset packs
                for asset_pack in pack.get_discovered_asset_packs():
                    # Get the installation path from the asset pack
                    install_path = os.path.dirname(asset_pack.pack_info_path)
                    if os.path.exists(install_path):
                        asset_pack_paths.append(install_path)
            
            asset_pack_paths_str = json.dumps(asset_pack_paths, ensure_ascii=False, indent=2)
            info_msg = f"get_asset_packs(), the installation file directories of all registered asset packs: \n"
            info_msg += f"{asset_pack_paths_str}"
            self.logger.info(info_msg)

            return asset_pack_paths
        except Exception as e:
            warn_msg = f"get_asset_packs(), the following exception was thrown "
            warn_msg += f"when accessing engon preferences: {str(e)}"
            self.logger.warning(warn_msg)
            return []



    def _build_dir_tree_dict(
            self,
            current_dir: Path
        ) -> dict:
        """
        Recursively traverses a directory and returns a dictionary 
        representing the hierarchical structure (files and directories).
        """
        
        # Base case: if it's a file, return its simple structure
        if current_dir.is_file():
            return {
                "error": f"'{current_dir.name}' should be a directory, instead of a file."
            }

        # If it's a directory, process its contents
        if current_dir.is_dir():
            contents = []
            
            # Iterate over the items in the directory
            for item in current_dir.iterdir():
                # Skip hidden files/directories (starting with '.') for clean output
                if item.name.startswith('.'):
                    continue

                if (item.is_file()) and (item.name.endswith('.blend')):
                    contents.append(item.name)

                elif item.is_dir():                
                    # Recursive call: process the subdirectory or file
                    child_structure = self._build_dir_tree_dict(item)
                    contents.append(child_structure)

                else:
                    continue

            # Return the directory structure
            return {
                # current_dir.name: contents
                str(current_dir.resolve()): contents
            }
            
        # Fallback for other path types (symlinks, devices, etc.)
        return {}
    

    def get_asset_categories(self) -> dict:
        category_dict = {}
        for asset_pack_dir in self.asset_pack_folders:

            blend_dir = f"{asset_pack_dir}/blends"
            if not os.path.exists(blend_dir):
                continue

            asset_pack_dict = self._build_dir_tree_dict(Path(blend_dir))
            category_dict[blend_dir] = asset_pack_dict[blend_dir]

        info_msg = f"get_asset_categories(), 'engon' addon contains the following asset categories:\n "
        category_dict_str = json.dumps(category_dict, ensure_ascii=False, indent=2)
        info_msg += f"{category_dict_str}"
        self.logger.info(info_msg)

        return category_dict
    


    def _traverse_nested_dict(
            self, 
            curr_dir
        ):
        """
        A recursive generator function that yields all key-value pairs 
        from a potentially deeply nested dictionary that do not have 
        another dictionary as their value.
        
        :param data: The dictionary to traverse.
        :yields: (key, value) tuples for non-dictionary items.
        """
        if not isinstance(curr_dir, dict):
            return
            
        for key, value in curr_dir.items():
            if isinstance(value, dict):
                # If the value is another dictionary, we call the function 
                # recursively using 'yield from' to process its contents.
                yield from self._traverse_nested_dict(value)

            elif isinstance(value, list):
                # If the value is a piece of data (str, int, bool, list, etc.),
                # we yield the key-value pair.
                for item in value:
                    if isinstance(item, str):
                        yield key, item
                    elif isinstance(item, dict):
                        yield from self._traverse_nested_dict(item)
                    else:
                        # This case should NOT happen.
                        return

            elif isinstance(value, str):
                yield key, value

            else:
                # This case should NOT happen.
                yield key, value


    def find_blend_filepaths(
            self,
            object_name: str=""    
        ) -> list:
        """
        Given an object name, find the .blend files that contain the object name a substring.
        
        Returns:
            A list of the .blend filepaths that contain the given object_name.
        """ 
        object_name = object_name.strip()
        if len(object_name) == 0:
            warn_msg = f"find_blend_filepaths(), the input 'object_name' is empty."
            self.logger.warning(warn_msg)
            return []

        candidate_filepaths = []
        for key, value in self._traverse_nested_dict(self.asset_pack_blend_filepaths):
            if isinstance(value, str):
                dir_path = str(key).rstrip('/')
                if object_name.lower() in str(value).lower():
                    blend_full_filepath = f"{dir_path}/{str(value)}"
                    candidate_filepaths.append(blend_full_filepath)

        info_msg = f"find_blend_filepaths(), given an object name '{object_name}', "
        info_msg += f"find the .blend file whose filename contains this object's name:\n "
        candidate_filepaths_str = json.dumps(candidate_filepaths, ensure_ascii=False, indent=2)
        info_msg += f"{candidate_filepaths_str}"
        self.logger.info(info_msg)
            
        return candidate_filepaths
        

    def get_all_asset_names(
            self,
            blend_filepath: str=""
        ) -> dict:
        blend_filepath = blend_filepath.strip()
        if len(blend_filepath) == 0:
            warn_msg = f"get_all_asset_names(), the input 'blend_filepath' is empty."
            self.logger.warning(warn_msg)
            return {}
        
        if not os.path.exists(blend_filepath):
            warn_msg = f"get_all_asset_names(), the input 'blend_filepath' doesn't exist."
            self.logger.warning(warn_msg)
            return {}
        
        self.blend_file_handler.blend_filepath = blend_filepath
        return self.blend_file_handler.get_all_asset_names()
    

    def load_objects(
            self,
            object_names:list=[]
        ) -> list:
        # 1. Find all the .blend files whose name contains one of the 'object_names'
        candidate_blends = []
        for obj_name in object_names:
            candidate_blends += self.find_blend_filepaths(
                object_name=obj_name   
            )
        unique_blends_set = set(candidate_blends)
        candidate_blends = list(unique_blends_set)

        # 2. Get all object assets from all candidate .blend files
        selected_object_instances = []
        for blend_filepath in candidate_blends:
            asset_names = self.get_all_asset_names(blend_filepath)

            candidate_object_names = []
            for candidate_obj_name in asset_names["Objects"]:
                for obj_name in object_names:
                    if ((obj_name.lower() in candidate_obj_name.lower()) or 
                        (candidate_obj_name.lower() in obj_name.lower())
                        ):
                        candidate_object_names.append(candidate_obj_name)

            # 3. Load object from the current .blend file.
            if len(candidate_object_names) > 0:
                self.blend_file_handler.blend_filepath = blend_filepath
                selected_object_instances += self.blend_file_handler.load_objects(candidate_object_names)

        # 4. Print out the results.
        info_msg = f"load_objects(), given object_names: {object_names}, \n"
        info_msg += f"we look into all .blend files whose names contain one of the object names, one by one, \n"
        info_msg += f"and find the following object assets whose name is similar to one of the given object names:"

        selected_object_names = [obj.name for obj in selected_object_instances]
        selected_object_instances_str = json.dumps(selected_object_names, ensure_ascii=False, indent=2)
        info_msg += selected_object_instances_str
        self.logger.info(info_msg)

        return selected_object_instances


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


    @staticmethod
    def usage_demo():     
        botaniq_addon = EngonBotaniqAddon()
        # _ = botaniq_addon.find_blend_filepaths("bq_pps_Forest")

        """
        blend_filepath = "/home/robot/polygoniq_asset_packs/botaniq_full/blends/particles/forest-floor/"
        blend_filepath += f"bq_pps_Forest_Mushrooms_C_spring-summer-autumn.blend"
        _ = botaniq_addon.get_all_asset_names(blend_filepath)
        """

        object_names_1 = ["bq_pps_Forest", "Tree_Phoenix"]
        _ = botaniq_addon.load_objects(object_names=object_names_1)

        object_names_2 = ["Forest_Mushrooms_A", "Tree_Phoenix-canariensis_A"]
        object_instances = botaniq_addon.get_objects(object_names=object_names_2)
        botaniq_addon.display_objects(object_instances)