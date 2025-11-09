import bpy
import sys
import os
import addon_utils
import pprint

class BlenderImporter:
    def __init__(self):
        self.blend_file_path = "/"

    def get_script_directory(self):
    # Get the directory of the current script
        try:
            # When script is run from Blender's Text Editor or as embedded script
            if bpy.data.texts:
                # Get the directory of the blend file if it exists, otherwise use current working directory
                if bpy.data.filepath:  # If blend file is saved
                    print(f"\n[INFO] The blend python script is saved")
                    dir_path = os.path.dirname(bpy.data.filepath)
                else:  # If blend file is not saved
                    print(f"\n[INFO] The blend python script is not saved")
                    dir_path = os.path.dirname(bpy.data.texts[0].filepath) if bpy.data.texts[0].filepath else os.getcwd()
            else:
                # When script is run as external file
                print(f"\n[INFO] script is run as external filed")
                dir_path = os.path.dirname(os.path.abspath(__file__))
        except:
            # Fallback to current working directory
            print(f"\n[INFO] Fallback to current working directory")
            dir_path = os.getcwd()

        # Ensure we have an absolute path
        dir_path = os.path.abspath(dir_path)

        # Get blend file path
        self.blend_file_path = bpy.data.filepath if bpy.data.filepath else dir_path
        print(f"[INFO] blend_file_path='{self.blend_file_path}'")

    @staticmethod
    def append_script_directory():
        blender_importer = BlenderImporter()
        blender_importer.get_script_directory()

        # --- Add local modules to Python path ---
        # This allows us to import the classes from the other scripts in the same directory.
        if blender_importer.blend_file_path not in sys.path:
            sys.path.append(blender_importer.blend_file_path)
            print(f"[INFO] Added script directory to Python path: {blender_importer.blend_file_path}")

    @staticmethod
    def list_all_addons():
        """
        Prints a list of all installed add-ons and their versions.
        The list includes both enabled and disabled add-ons.
        """
        print("\n[INFO]--- All Available Add-ons ---")
        
        # The `modules(refresh=False)` function returns a list of all registered
        # add-on modules. Setting refresh=False is usually faster if the list
        # has already been generated.
        # The 'True' argument can also be used to get all modules, enabled and disabled.
        for mod in addon_utils.modules():
            try:
                # Add-on information is stored in the 'bl_info' dictionary.
                name = mod.bl_info.get("name", "Unknown Name")
                version = mod.bl_info.get("version", (0, 0, 0))

                # Format the version tuple into a readable string
                version_str = ".".join(map(str, version))

                #  print(f"Name: {name} (Version: {version_str})")
                pprint.pprint(mod.bl_info)
                print()

            except AttributeError:
                # This handles cases where a module might not have the bl_info
                # dictionary, which can happen for certain internal modules.
                print(f"Module without bl_info: {mod.__name__}")

        print("    -----------------------------\n")



if __name__ in "__main__":
    BlenderImporter.append_script_directory()
    BlenderImporter.list_all_addons()