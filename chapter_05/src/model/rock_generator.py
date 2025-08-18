

import bpy
from math import radians
import os
import sys


class RockGenerator:
    """
    A class to create and manipulate individual rock objects using Blender's
    built-in rock generator addon.
    """

    def __init__(self):
        """
        Initializes the RockGenerator and ensures the necessary addon is enabled.
        """
        self.rock_object = None
        self.texture_applier = None
        # self._enable_extra_objects_addon()

        try:
            # print(f"[INFO] In RockGenerator, sys.path: '{sys.path}'")
            from shader_modifier.apply_texture_asset import ApplyTexture
            self.texture_applier = ApplyTexture()

        except ImportError:
            print("[ERROR] Could not import ApplyTexture class. Make sure 'apply_texture_asset.py' is in the correct directory.")
            ApplyTexture = None
        

    # Looks like the add-on's name, "add_mesh_extra_objects", is not right.
    # We have tried the following module names, all failed, including, 
    # "extra_mesh_objects", "add_mesh_extra_objects" "add_extra_mesh_objects", "add_mesh_rock", 
    # "extra_mesh_objects.add_mesh_rocks", "extra_mesh_objects/add_mesh_rocks", "VIEW3D_MT_mesh_extras_add"
    def _enable_extra_objects_addon(self):
        # A private helper to ensure the 'Add Mesh: Extra Objects' addon is enabled. 
        try:
            bpy.ops.preferences.addon_enable(module="add_mesh_rock")
            print("[INFO] 'Add Mesh: Extra Objects' addon is enabled.")
        except Exception as e:
            print(f"[ERROR] Could not enable the required addon: {e}")
            print("[ERROR] The rock generator will not function.")    


    def set_texture_directory(self, texture_directory="/"):
        self.texture_applier.set_texture_directory(texture_directory)


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
            self.rock_object.scale = scale
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
        # First, create a UV map for the rock so textures can be applied correctly.
        bpy.context.view_layer.objects.active = self.rock_object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')
        print(f"[INFO] Created Smart UV Project for {self.rock_object.name}.")       

        try:
            self.texture_applier.set_object(self.rock_object)
            self.texture_applier.set_texture_directory(texture_directory)

            self.texture_applier.create_base_nodes()
            self.texture_applier.create_texture_nodes()
            print(f"[SUCCESS] Preliminary textures applied to {self.rock_object.name}.")
        except (ValueError, FileNotFoundError) as e:
            print(f"[ERROR] Failed to apply preliminary textures: {e}")


    def apply_secondary_texture(self, texture_directory):
        """
        Applies a set of PBR textures to the current rock object.

        Args:
            texture_directory (str): The path to the folder containing texture images.
        """
        if not self.rock_object:
            print("[WARNING] No rock object to texture. Please use create_rock() first.")
            return

        print(f"[INFO] Applying textures from {texture_directory} to {self.rock_object.name}.")
        # First, create a UV map for the rock so textures can be applied correctly.
        bpy.context.view_layer.objects.active = self.rock_object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')
        print(f"[INFO] Created Smart UV Project for {self.rock_object.name}.")       

        try:
            self.texture_applier.set_object(self.rock_object)
            self.texture_applier.set_secondary_texture_directory(texture_directory)

            self.texture_applier.create_secondary_base_nodes()
            self.texture_applier.create_secondary_texture_nodes()
            print(f"[SUCCESS] Secondary textures applied to {self.rock_object.name}.")
        except (ValueError, FileNotFoundError) as e:
            print(f"[ERROR] Failed to apply secondary textures: {e}")



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
    def run_demo():

        # It's good practice to start with a clean scene for a demo.
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        # Create a ground plane for context.
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))

        # Define the texture directory for the rocks
        rock_texture_files = "/home/robot/movie_blender_studio/asset/texture/Rock003_2K-JPG/"
        moss_texture_files = "/home/robot/movie_blender_studio/asset/texture/Moss002_2K-JPG"
        
        print(f"[INFO] rock_texture_files={rock_texture_files}")
        print(f"[INFO] moss_texture_files={moss_texture_files}")

        # 1. Instantiate the generator.
        rock_generator = RockGenerator()
        rock_generator.set_texture_directory(rock_texture_files)

        # 2. Create the first rock and apply textures.
        print("\n--- Creating First Rock ---")
        rock_generator.texture_applier.use_modifier=True
        rock_generator.create_rock(scale=(10.0, 8.5, 5.8), skew=(0.0, 1.0, 0.0))
        rock_generator.move_rock(location=(2, -3, 0))
        rock_generator.rotate_rock(angle=(radians(30), radians(0), radians(45)))
        rock_generator.apply_texture(rock_texture_files)

        rock_generator.texture_applier.create_displacement_modifier()
        print(f"[INFO] Displacement modifier created successfully.")

        rock_generator.texture_applier.use_modifier=False
        rock_generator.apply_secondary_texture(moss_texture_files)

        # 3. Create a second, different rock and apply textures.
        print("\n--- Creating Second Rock ---")
        rock_generator.texture_applier.use_modifier=True
        rock_generator.create_rock(scale=(3.5, 4.0, 2.2), skew=(1.0, 1.0, 1.0))
        rock_generator.move_rock(location=(-4, 1, 0))
        rock_generator.rotate_rock(angle=(radians(0), radians(15), radians(-25)))
        rock_generator.apply_texture(rock_texture_files)

        rock_generator.texture_applier.create_displacement_modifier()
        print(f"[INFO] Displacement modifier created successfully.")
        
        rock_generator.texture_applier.use_modifier=False
        rock_generator.apply_secondary_texture(moss_texture_files)


        # 4. Print out all the object in viewport
        # Get the collection of all visible objects in the current context
        visible_objects = bpy.context.visible_objects

        # Check if there are any visible objects
        if visible_objects:
            print("\n--- Visible Objects in Viewport ---")
            # Iterate through the collection and print each object's name
            for obj in visible_objects:
                print(obj.name)
        else:
            print("No visible objects found in the viewport.")
        print("\n[SUCCESS] Script finished.")


if __name__ == "__main__":
    RockGenerator.run_demo()