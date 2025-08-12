import bpy
import os
import sys


class WaterGenerator:
    """
    A class to create a procedural water surface in Blender.
    """
    def __init__(self):
        """
        Initializes the WaterGenerator.
        """
        self.water_plane = None
        self.tex_gen = None
        self.tex_asset_applier = None

        try:
            from shader_modifier.shader_generator import ShaderGenerator
            self.tex_gen = ShaderGenerator()

            from shader_modifier.apply_texture_asset import ApplyTexture
            self.tex_asset_applier = ApplyTexture()

            print("[INFO] WaterGenerator class imported successfully.")   
        except ImportError as e:
            print(f"[ERROR] Could not import ShaderGenerator class: {e}")
            print(f"[ERROR] Please ensure 'create_texture.py' is in the correct directory.")
            ShaderGenerator = None


    def create_water(self, scale=(10.0, 10.0)):
        """
        Creates a plane and applies a procedural water material to it.

        Args:
            scale (tuple): The size of the water plane on the (X, Y) axes.
        """
        # 1. Create a mesh plane
        print(f"[INFO] Creating a water plane with scale {scale}...")
        bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, location=(0, 0, 0))
        self.water_plane = bpy.context.active_object
        self.water_plane.name = "WaterSurface"
        self.water_plane.scale = (scale[0], scale[1], 1)
        bpy.ops.object.transform_apply(scale=True)

        # 2. Use TextureGenerator to create the material and base nodes
        self.tex_gen.set_object(self.water_plane)
        self.tex_gen.create_material("WaterMaterial")

        # Create the base shader nodes required for the water effect
        output_node = self.tex_gen.create_node('ShaderNodeOutputMaterial', "Material Output", location=(1000, 0))
        bsdf_node = self.tex_gen.create_node('ShaderNodeBsdfPrincipled', "Principled BSDF", location=(700, 0))
        tex_coord_node = self.tex_gen.create_node('ShaderNodeTexCoord', "Texture Coordinate", location=(0, 300))
        mapping_node = self.tex_gen.create_node('ShaderNodeMapping', "Mapping", location=(200, 300))

        # 3. Configure the Principled BSDF for water
        print("[INFO] Configuring Principled BSDF for water material...")
        self.tex_gen.set_node_attribute("Principled BSDF", {
            'Transmission': 1.0,
            'Roughness': 0.0,
            'Base Color': (0.0, 0.3, 0.6, 0.5),
            'IOR': 1.5,
            'Alpha': 0.5
        })

        # 4. Link the base nodes
        self.tex_gen.create_link(bsdf_node, 'BSDF', output_node, 'Surface')
        self.tex_gen.create_link(tex_coord_node, 'Generated', mapping_node, 'Vector')

        # 5. Add and configure Noise Texture node
        noise_attributes = {
            'noise_dimensions': '4D',
            'W': 1.2,
            'Scale': 40.0,
            'Detail': 15.0,
            'Roughness': 0.6,
            'Distortion': 0.4
        }
        noise_node = self.tex_gen.create_node('ShaderNodeTexNoise', "Noise Texture", attributes=noise_attributes, location=(200, -200))

        # 6. Link Mapping to Noise Texture
        self.tex_gen.create_link(mapping_node, 'Vector', noise_node, 'Vector')

        # 7. Add and configure Bump node
        bump_attributes = {
            'Strength': 1.0,
            'Distance': 2.0
        }
        bump_node = self.tex_gen.create_node('ShaderNodeBump', "Bump", attributes=bump_attributes, location=(450, -200))

        # 8. Link Noise Texture to Bump, and Bump to Principled BSDF
        self.tex_gen.create_link(noise_node, 'Fac', bump_node, 'Height')
        self.tex_gen.create_link(bump_node, 'Normal', bsdf_node, 'Normal')

        print("[SUCCESS] Procedural water material created.")


    @staticmethod
    def run_demo():
        """
        A static method to demonstrate the functionality of the WaterGenerator class.
        """
        print("[INFO] --- Running WaterGenerator Demo ---")
        # Clear the scene and create a sample mesh to texture
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        water_generator = WaterGenerator()

        # 1. Create a wood floor underneath the water plane
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -5))
        riverbed = bpy.context.active_object
        riverbed.name = "Riverbed Wooden Floor"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=50)
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Define the texture directory
        # IMPORTANT: Update this path to your texture folder
        texture_directory = "/home/robot/movie_blender_studio/asset/texture/WoodFloor043_4K"

        # 1.1 Instantiate the class with the mesh and texture directory
        texture_applier = water_generator.tex_asset_applier
        texture_applier.set_object(riverbed)
        texture_applier.set_texture_directory(texture_directory)

        # 1.2 Run the texturing process
        texture_applier.run()
        texture_applier.create_displacement_modifier()


        # 2. Create a water plane
        water_generator.create_water(scale=(20, 20))


        # 3. Print out all the object in viewport

        # Get the collection of all visible objects in the current context
        # Check if there are any visible objects
        visible_objects = bpy.context.visible_objects
        if visible_objects:
            print("\n--- Visible Objects in Viewport ---")
            # Iterate through the collection and print each object's name
            for obj in visible_objects:
                print(obj.name)
        else:
            print("No visible objects found in the viewport.")
        print("\n[SUCCESS] --- WaterGenerator Demo Finished ---")


if __name__ == "__main__":
    WaterGenerator.run_demo()