import os
import sys

import bpy
import bmesh
import random
import numpy as np


class WaterGenerator:
    """
    A class to create a procedural water surface in Blender.
    """
    def __init__(self):
        """
        Initializes the WaterGenerator.
        """
        self.water_plane = None
        self.plane_width = 0
        self.plane_length = 0
        self.subdivisions = (1, 1)

        self.left_waterline = []
        self.right_waterline = []

        self.tex_gen = None
        self.tex_asset_applier = None

        try:
            from shader_modifier.shader_generator import ShaderGenerator
            self.tex_gen = ShaderGenerator()

            from shader_modifier.apply_texture_asset import ApplyTexture
            self.tex_asset_applier = ApplyTexture()

        except ImportError as e:
            print(f"[ERROR] Could not import ShaderGenerator class: {e}")
            print(f"[ERROR] Please ensure 'create_texture.py' is in the correct directory.")
            ShaderGenerator = None


    def create_water_plane(self, scale=(10.0, 10.0), subdivisions=(38, 38)):
        print(f"[INFO] Creating a water plane with scale {scale} with subdivisions {subdivisions}...")

        if self.subdivisions == (1, 1):
            self.subdivisions = subdivisions

        if self.plane_width == 0 and self.plane_length == 0:
            self.plane_width = scale[0]
            self.plane_length = scale[1]
        
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=self.subdivisions[0],
            y_subdivisions=self.subdivisions[1], 
            size=1.0, 
            align='WORLD', 
            location=(0, 0, 0)
        )

        self.water_plane = bpy.context.active_object
        self.water_plane.name = "WaterSurface"
        
        # Scale the plane to (20, 40)
        self.water_plane.scale = (self.plane_width, self.plane_length, 1)
        bpy.ops.object.transform_apply(scale=True)



    # After some trials, an appropriate subdivisions is 
    #   [(self.plane_width * 2 - 2), (self.plane_length * 2 - 2)]
    def create_water(self, scale=(10.0, 10.0), subdivisions=(38, 38)):
        """
        Creates a plane and applies a procedural water material to it.

        Args:
            scale (tuple): The size of the water plane on the (X, Y) axes.
        """
        # 1. Create a mesh plane
        self.create_water_plane(scale, subdivisions)

        # 2. Use TextureGenerator to create the material and base nodes
        self.tex_gen.set_object(self.water_plane)
        self.tex_gen.create_material("WaterMaterial")

        # Create the base shader nodes required for the water effect
        output_node = self.tex_gen.create_node('ShaderNodeOutputMaterial', "Material Output", location=(800, 0))
        bsdf_node = self.tex_gen.create_node('ShaderNodeBsdfPrincipled', "Principled BSDF", location=(500, 0))
        tex_coord_node = self.tex_gen.create_node('ShaderNodeTexCoord', "Texture Coordinate", location=(-500, 0))
        mapping_node = self.tex_gen.create_node('ShaderNodeMapping', "Mapping", location=(-250, 0))

        # 3. Configure the Principled BSDF for water
        print("[INFO] Configuring Principled BSDF for water material...")
        self.tex_gen.set_node_attribute("Principled BSDF", {
            'Transmission': 1.0,
            'Roughness': 0.0,
            'Base Color': (1.0, 1.1, 1.2, 0.0),
            'IOR': 1.5,
            'Alpha': 0.3
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
        noise_node = self.tex_gen.create_node(
            'ShaderNodeTexNoise', 
            "Noise Texture", 
            attributes=noise_attributes, 
            location=(0, 0)
        )

        # 6. Link Mapping to Noise Texture
        self.tex_gen.create_link(mapping_node, 'Vector', noise_node, 'Vector')

        # 7. Add and configure Bump node
        bump_attributes = {
            'Strength': 1.0,
            'Distance': 2.0
        }
        bump_node = self.tex_gen.create_node(
            'ShaderNodeBump', 
            "Bump", 
            attributes=bump_attributes, 
            location=(250, 0)
        )

        # 8. Link Noise Texture to Bump, and Bump to Principled BSDF
        self.tex_gen.create_link(noise_node, 'Fac', bump_node, 'Height')
        self.tex_gen.create_link(bump_node, 'Normal', bsdf_node, 'Normal')

        print("[SUCCESS] Procedural water material created.")


    def move_water(self, location=(0.0, 0.0, 0.0)):
        self.water_plane.select_set(True)
        bpy.context.view_layer.objects.active = self.water_plane
        self.water_plane.location = location
                

    def delete_vertices_beyond_waterlines(self, left_waterline, right_waterline):
        # 1. Verify the inputs are valid
        if len(left_waterline) > 0 and len(right_waterline) > 0:
            self.left_waterline = left_waterline
            self.right_waterline = right_waterline
        else:
            print(f"[ERROR] left_waterline and right_waterline cannot be empty list.")

        left_path = np.array(self.left_waterline)
        right_path = np.array(self.right_waterline)

        # 2. Select vertices based on their position between the two waterlines
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = self.water_plane
        self.water_plane.select_set(True)

        bm_water = bmesh.new()
        bm_water.from_mesh(self.water_plane.data)

        outlier_vertex_indices = []

        for vert in bm_water.verts:
            vertex_co = np.array([vert.co.x, vert.co.y])
            
            # Find the segment on water plane that is closest to the vertex's y-coordinate
            # for both left and right waterlines
            left_distances_y = np.abs(left_path[:, 1] - vertex_co[1])
            closest_left_index = np.argmin(left_distances_y)
            water_plane_left_x = left_path[closest_left_index][0]

            right_distances_y = np.abs(right_path[:, 1] - vertex_co[1])
            closest_right_index = np.argmin(right_distances_y)
            water_plane_right_x = right_path[closest_right_index][0]

            # Check if the vertex's x-coordinate is within the riverbed boundaries
            if vert.co.x < water_plane_left_x or vert.co.x > water_plane_right_x:
                outlier_vertex_indices.append(vert)

        # 3. Delete the outlier vertices that beyond the waterlines. 
        print(f"\n[INFO] Deleting {len(outlier_vertex_indices)} outlier vertices from the water plane...")

        # Ensure the vertices are still valid before deleting
        valid_verts_to_delete = [v for v in outlier_vertex_indices if v.is_valid] 
        
        if valid_verts_to_delete:
            bmesh.ops.delete(bm_water, geom=valid_verts_to_delete, context='VERTS')
            
            # Write the modified BMesh data back to the object
            bm_water.to_mesh(self.water_plane.data)
            self.water_plane.data.update()
            print("[SUCCESS] Water plane trimmed to waterlines.")
        else:
            print("[INFO] No valid vertices to delete.")

        bm_water.free()
    

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
        texture_applier.apply_texture()
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