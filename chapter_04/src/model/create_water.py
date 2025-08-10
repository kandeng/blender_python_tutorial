import bpy
import os
import sys


class WaterGenerator:
    """
    A class to create a procedural water surface in Blender.
    """
    def __init__(self, texture_directory="/"):
        """
        Initializes the RockGenerator and ensures the necessary addon is enabled.
        """
        self.water_plane = None
        self.texture_applier = None

        try:
            print(f"[INFO] In WaterGenerator, sys.path: '{sys.path}'")
            from texture.apply_texture_to_mesh import ApplyTexture
            self.texture_applier = ApplyTexture(self.water_plane, texture_directory)
        except ImportError:
            print("[ERROR] Could not import ApplyTexture class. Make sure 'apply_texture_to_mesh.py' is in the correct directory.")
            ApplyTexture = None
            

    def create_water(self, scale=(10.0, 10.0)):
        """
        Creates a plane and applies a procedural water material to it.

        Args:
            scale (tuple): The size of the water plane on the (X, Y) axes.
        """
        # 1. Create a mesh plane
        print(f"[INFO] Creating a water plane with scale {scale}...")
        bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, location=(0, 0, 10))
        self.water_plane = bpy.context.active_object
        self.water_plane.name = "WaterSurface"
        self.water_plane.scale = (scale[0], scale[1], 1)
        bpy.ops.object.transform_apply(scale=True)

        # 2. Use ApplyTexture to create base nodes
        self.texture_applier.set_mesh_object(self.water_plane)
        self.texture_applier.create_base_nodes()

        # Get references to the created nodes and links for easier access
        nodes = self.texture_applier.nodes
        links = self.texture_applier.links
        bsdf = self.texture_applier.principled_bsdf

        # 3. Configure the Principled BSDF for water
        print("[INFO] Configuring Principled BSDF for water material...")
        if 'Transmission Weight' in bsdf.inputs:
            bsdf.inputs['Transmission Weight'].default_value = 1.0
        elif 'Transmission' in bsdf.inputs:
            bsdf.inputs['Transmission'].default_value = 1.0

        bsdf.inputs['Roughness'].default_value = 0.0
        bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0) # White

        # 4. Link Texture Coordinate (Generated) to Mapping
        tex_coord_node = nodes.get("Texture Coordinate")
        mapping_node = self.texture_applier.mapping_node
        if tex_coord_node and mapping_node:
            # The base function links UV by default, so we create the correct link here.
            links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
            print("[INFO] Linked Texture Coordinate (Generated) to Mapping node.")

        # 5. Add and configure Noise Texture node
        print("[INFO] Creating and configuring Noise Texture node...")
        noise_node = nodes.new(type='ShaderNodeTexNoise')
        noise_node.location = (200, -200)
        noise_node.noise_dimensions = '4D'
        noise_node.inputs['W'].default_value = 1.2
        noise_node.inputs['Scale'].default_value = 40.0
        noise_node.inputs['Detail'].default_value = 15.0
        noise_node.inputs['Roughness'].default_value = 0.6
        noise_node.inputs['Distortion'].default_value = 0.4

        # 6. Link Mapping to Noise Texture
        links.new(mapping_node.outputs['Vector'], noise_node.inputs['Vector'])

        # 7. Add and configure Bump node
        print("[INFO] Creating and configuring Bump node...")
        bump_node = nodes.new(type='ShaderNodeBump')
        bump_node.location = (450, -200)
        bump_node.inputs['Strength'].default_value = 0.1
        bump_node.inputs['Distance'].default_value = 1.0

        # 8. Link Noise Texture to Bump, and Bump to Principled BSDF
        links.new(noise_node.outputs['Fac'], bump_node.inputs['Height'])
        links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])

        print("[SUCCESS] Procedural water material created.")


    # --- Main execution example ---
    @staticmethod
    def testrun():
        # It's good practice to start with a clean scene for a demo.
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        # 1. Instantiate the generator.
        water_generator = WaterGenerator()

        # 2. Create the water surface.
        water_generator.create_water(scale=(20, 20))

        # Add a simple light and camera for context
        bpy.ops.object.light_add(type='SUN', location=(15, -15, 20), rotation=(-0.8, -0.4, -0.7))
        bpy.context.active_object.data.energy = 4
        bpy.ops.object.camera_add(location=(20, -20, 15), rotation=(1.1, 0, -0.8))
        bpy.context.scene.camera = bpy.context.active_object

        print("\nScript finished. A water plane has been created.")

