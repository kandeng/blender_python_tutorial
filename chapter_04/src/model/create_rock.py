

import bpy
from math import radians
import os
import sys

"""
def get_script_directory():
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
    blend_file_path = bpy.data.filepath if bpy.data.filepath else dir_path
    print(f"[INFO] blend_file_path='{blend_file_path}'")
    return blend_file_path


# --- Add local modules to Python path ---
# This allows us to import the classes from the other scripts in the same directory.
script_directory = get_script_directory()
if script_directory not in sys.path:
    sys.path.append(script_directory)
    print("[INFO] Added script directory to Python path:", script_directory)
"""


class RockGenerator:
    """
    A class to create and manipulate individual rock objects using Blender's
    built-in rock generator addon.
    """

    def __init__(self, texture_directory="/"):
        """
        Initializes the RockGenerator and ensures the necessary addon is enabled.
        """
        self.rock_object = None
        self.texture_applier = None
        # self._enable_extra_objects_addon()

        try:
            print(f"[INFO] In RockGenerator, sys.path: '{sys.path}'")
            from texture.apply_texture_to_mesh import ApplyTexture
            # self.texture_applier = ApplyTexture(mesh_object=self.rock_object, texture_dir=texture_directory)
            self.texture_applier = ApplyTexture(self.rock_object, texture_directory)
        except ImportError:
            print("[ERROR] Could not import ApplyTexture class. Make sure 'apply_texture_to_mesh.py' is in the correct directory.")
            ApplyTexture = None
        

    # Looks like the add-on's name, "add_mesh_extra_objects", is not right.
    # We have tried the following module names, all failed, including, 
    # "extra_mesh_objects", "add_extra_mesh_objects", "add_mesh_rock", "VIEW3D_MT_mesh_extras_add"
    # "extra_mesh_objects.add_mesh_rocks", "extra_mesh_objects/add_mesh_rocks"
    def _enable_extra_objects_addon(self):
        # A private helper to ensure the 'Add Mesh: Extra Objects' addon is enabled. 
        try:
            bpy.ops.preferences.addon_enable(module="add_mesh_rock")
            print("[INFO] 'Add Mesh: Extra Objects' addon is enabled.")
        except Exception as e:
            print(f"[ERROR] Could not enable the required addon: {e}")
            print("[ERROR] The rock generator will not function.")    



    def create_rock(self, scale=(1.0, 1.0, 1.0), skew=(0.0, 0.0, 0.0)):
        """
        Creates a new rock at the origin with a specific initial scale.
        The new rock becomes the active rock for other methods.

        Args:
            scale (tuple): The initial scale of the rock on the (X, Y, Z) axes.
            skew (tuple): The skewing factor along the (X, Y, Z) axes, with value range (0.0, 1.0).
        """
        print(f"[INFO] Creating a new rock with scale {scale}...")
        try:
            # Try to use the rock generator if available
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.normals_make_consistent()
            bpy.ops.object.editmode_toggle()
            
            bpy.ops.mesh.add_mesh_rock(
                scale_fac=scale,
                skew_X=skew[0], 
                skew_Y=skew[1], 
                skew_Z=skew[2]
            )

            self.rock_object = bpy.context.active_object
            self.rock_object.name = "GeneratedRock"
            print(f"[SUCCESS] Created rock: {self.rock_object.name}")
        except RuntimeError as e:
            print(f"[ERROR] Failed to create rock. Is the addon enabled? Error: {e}")
            self.rock_object = None

    def apply_texture(self, texture_directory):
        """
        Applies a set of PBR textures to the current rock object.

        Args:
            texture_directory (str): The path to the folder containing texture images.
        """
        if not self.rock_object:
            print("[WARNING] No rock object to texture. Please use create_rock() first.")
            return

        print(f"[INFO] Applying textures from {texture_directory} to {self.rock_object.name}.")
        self.texture_applier.set_mesh_object(self.rock_object)
        self.texture_applier.set_texture_directory(texture_directory)

        # First, create a UV map for the rock so textures can be applied correctly.
        bpy.context.view_layer.objects.active = self.rock_object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')
        print(f"[INFO] Created Smart UV Project for {self.rock_object.name}.")

        try:
            # Use the ApplyTexture class to handle the node setup.
            
            self.texture_applier.run()
            print(f"[SUCCESS] Textures applied to {self.rock_object.name}.")
        except (ValueError, FileNotFoundError) as e:
            print(f"[ERROR] Failed to apply textures: {e}")

    def scale_rock(self, scale=(1.0, 1.0, 1.0)):
        """
        Applies an additional scaling factor to the current rock object.

        Args:
            scale (tuple): The scaling factor for the (X, Y, Z) axes.
        """
        if not self.rock_object:
            print("[WARNING] No rock object to scale. Please use create_rock() first.")
            return
        
        print(f"[INFO] Scaling {self.rock_object.name} by {scale}.")
        self.rock_object.scale = scale

    def move_rock(self, location=(0, 0, 0)):
        """
        Moves the current rock object to a new location.

        Args:
            location (tuple): The target (X, Y, Z) coordinates.
        """
        if not self.rock_object:
            print("[WARNING] No rock object to move. Please use create_rock() first.")
            return

        print(f"[INFO] Moving {self.rock_object.name} to {location}.")
        self.rock_object.location = location

    def rotate_rock(self, angle=(0, 0, 0)):
        """
        Rotates the current rock object.

        Args:
            angle (tuple): The rotation angles in radians for the (X, Y, Z) axes.
        """
        if not self.rock_object:
            print("[WARNING] No rock object to rotate. Please use create_rock() first.")
            return

        print(f"[INFO] Rotating {self.rock_object.name} by {angle} radians.")
        self.rock_object.rotation_euler = angle


    # --- Execution example ---
    @staticmethod
    def testrun():

        # It's good practice to start with a clean scene for a demo.
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        # Create a ground plane for context.
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))

        # Define the texture directory for the rocks
        rock_texture_dir = "/home/robot/movie_blender_studio/asset/texture/Rock003_2K-JPG/"

        # 1. Instantiate the generator.
        rock_generator = RockGenerator()

        # 2. Create the first rock and apply textures.
        print("\n--- Creating First Rock ---")
        rock_generator.create_rock(scale=(1.0, 1.5, 0.8), skew=(0.0, 1.0, 0.0))
        rock_generator.move_rock(location=(2, -3, 0))
        rock_generator.rotate_rock(angle=(radians(30), radians(0), radians(45)))
        rock_generator.apply_texture(texture_directory=rock_texture_dir)

        # 3. Create a second, different rock and apply textures.
        print("\n--- Creating Second Rock ---")
        rock_generator.create_rock(scale=(2.5, 2.0, 2.2), skew=(1.0, 1.0, 1.0))
        rock_generator.move_rock(location=(-4, 1, 0))
        rock_generator.rotate_rock(angle=(radians(0), radians(15), radians(-25)))
        rock_generator.apply_texture(texture_directory=rock_texture_dir)

        print("\n[SUCCESS] Script finished.")


if __name__ == "__main__":
    RockGenerator.testrun()