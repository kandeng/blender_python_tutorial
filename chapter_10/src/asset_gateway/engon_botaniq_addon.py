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
    



    @staticmethod
    def usage_demo():     
        botaniq_addon = EngonBotaniqAddon()
        _ = botaniq_addon.get_asset_categories()
