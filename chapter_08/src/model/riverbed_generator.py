import os
import sys

import bpy
import bmesh
import random
import numpy as np

# from model.utils.curve_generator import CurveGenerator


class RiverbedGenerator:
    """
    A class to generate a river terrain mesh in Blender,
    featuring a pitted riverbed and texture displacement.
    """
    def __init__(self):
        """
        Initializes the terrain parameters.
        """
        self.plane = None
        self.plane_width = 0
        self.plane_length = 0
        self.plane_subdivisions = (0, 0)


        self.curve_generator = None
        self.left_waterline = []
        self.right_waterline = []

        self.riverbed_indices = []
        self.riverbank_indices = []
        self.riverbed_depth = 0.0

        try:
            print(f"[INFO] In RiverbedGenerator, sys.path: '{sys.path}'")
            from model.utils.curve_generator import CurveGenerator
            self.curve_generator = CurveGenerator(width=10, length=20, subdivisions=(8, 18))
        except ImportError as e:
            print(f"[ERROR] Could not import CurveGenerator class. Exception: '{str(e)}'")
            self.curve_generator = None        
        
    
    def create_terrain(self, plane_width=10, plane_length=20, subdivisions=(8, 18)):
        print("[INFO] Creating terrain...")
        self.plane_width = plane_width
        self.plane_length = plane_length
        self.plane_subdivisions = subdivisions

        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=self.plane_subdivisions[0],
            y_subdivisions=self.plane_subdivisions[1], 
            size=1.0, 
            align='WORLD', 
            location=(0, 0, 0)
        )

        self.plane = bpy.context.active_object
        self.plane.name = "RiverTerrain"
        
        # Scale the river plane to the desired dimensions
        self.plane.scale = (self.plane_width, self.plane_length, 1.0)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


    def select_riverbed_vertices(self):
        """
        Identifies vertices for the riverbed based on two smoothly interpolated waterlines.
        """
        if not self.plane:
            print("[ERROR] Terrain plane not found. Please run create_terrain() first.")
            return

        print("[INFO] Selecting riverbed vertices using smooth waterlines...")
        if self.curve_generator is None:
            print(f"[ERROR] self.curve_generator is None! ")

        # 1. Generate the left and right waterlines for the river's path
        # left_waterline, right_waterline = self.create_river_waterlines(num_left_deviations, num_right_deviations)
        
        
        bezier_curve_left = self.curve_generator.create_bezier_curve(num_deviations=14)
        self.left_waterline = [(x - 0.25 * self.plane_width, y) for x, y in bezier_curve_left]
        bezier_curve_right = self.curve_generator.create_bezier_curve(num_deviations=28)
        self.right_waterline = [(x + 0.25 * self.plane_width, y) for x, y in bezier_curve_right]          
        
        left_path = np.array(self.left_waterline)
        right_path = np.array(self.right_waterline)

        # 2. Select vertices based on their position between the two waterlines
        vertices = self.plane.data.vertices
        for vert in vertices:
            vertex_co = np.array([vert.co.x, vert.co.y])
            
            # Find the segment on the river path that is closest to the vertex's y-coordinate
            # for both left and right waterlines
            left_distances_y = np.abs(left_path[:, 1] - vertex_co[1])
            closest_left_index = np.argmin(left_distances_y)
            riverbed_left_x = left_path[closest_left_index][0]

            right_distances_y = np.abs(right_path[:, 1] - vertex_co[1])
            closest_right_index = np.argmin(right_distances_y)
            riverbed_right_x = right_path[closest_right_index][0]

            # Check if the vertex's x-coordinate is within the riverbed boundaries
            if riverbed_left_x < vert.co.x < riverbed_right_x:
                self.riverbed_indices.append(vert.index)
            else:
                self.riverbank_indices.append(vert.index)


        if not self.riverbed_indices:
            print("[WARNING] No vertices were selected for the riverbed. The river may be too narrow or off the plane.")
            return
        
        print(f"[INFO] Selected {len(self.riverbed_indices)} vertices for the riverbed.")
  

    def dig_riverbed(self, min_pit_depth=1.0, max_pit_depth=2.0, pit_radius=1.8):
        """
        3. Digs pits for each vertex in the riverbed_indices list
           using iterative proportional editing.

        Args:
            min_pit_depth (float): The minimum depth for each pit.
            max_pit_depth (float): The maximum depth for each pit.
            pit_radius (float): The radius for each proportional editing operation.
        """
        if not self.riverbed_indices:
            print("[ERROR] No riverbed vertices selected. Please run select_riverbed_vertices() first.")
            return

        print("[INFO] Digging riverbed pits... (This may take a moment)")
        bpy.context.view_layer.objects.active = self.plane
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)

        original_falloff = bpy.context.scene.tool_settings.proportional_edit_falloff
        bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'

        for i, vert_index in enumerate(self.riverbed_indices):
            if i % 100 == 0:
                print(f"  Digging pit {i} of {len(self.riverbed_indices)}...")

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            self.plane.data.vertices[vert_index].select = True
            bpy.ops.object.mode_set(mode='EDIT')

            # Apply a small, random downward translation with proportional editing
            z_depth = -1.0 * random.uniform(min_pit_depth, max_pit_depth)
            
            bpy.ops.transform.translate(
                value=(0, 0, z_depth),
                orient_type='GLOBAL',
                use_proportional_edit=True, 
                proportional_edit_falloff='SMOOTH',
                proportional_size=pit_radius,
                release_confirm=True
            )
        
        bpy.context.scene.tool_settings.proportional_edit_falloff = original_falloff
        bpy.ops.object.mode_set(mode='OBJECT')
        print("[INFO] Finished digging riverbed.")


    def get_riverbed_depth(self):
        self.riverbed_depth = sys.float_info.max

        for vert_idx in self.riverbed_indices:
            vertex = self.plane.data.vertices[vert_idx]
            if vertex.co[2] < self.riverbed_depth:
                self.riverbed_depth = vertex.co[2]
        print(f"[INFO] The depth of the riverbed is {self.riverbed_depth}")


    def raise_riverbank(self, min_riverbank_height=0.0, max_riverbank_height=1.5, bump_radius=1.8):
        """
        4. Raise riverbank for each vertex outside of the riverbed_indices list
           using iterative proportional editing.

        Args:
            min_riverbank_height (float): The minimum depth for each pit.
            max_riverbank_height (float): The maximum depth for each pit.
            riverbank_radius (float): The radius for each proportional editing operation.
        """
        if not self.riverbank_indices:
            print("[ERROR] No riverbank vertices selected. Please run select_riverbed_vertices() first.")
            return

        print("[INFO] Raising riverbank ... (This may take a moment)")
        bpy.context.view_layer.objects.active = self.plane
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)

        original_falloff = bpy.context.scene.tool_settings.proportional_edit_falloff
        bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'

        for i, vert_index in enumerate(self.riverbank_indices):
            if i % 100 == 0:
                print(f"  Raising riverbank {i} of {len(self.riverbank_indices)}...")

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            self.plane.data.vertices[vert_index].select = True
            bpy.ops.object.mode_set(mode='EDIT')

            # Apply a small, random upward translation with proportional editing
            z_height = random.uniform(min_riverbank_height, max_riverbank_height)
            
            # Make banks higher further from the river center
            deviation_from_middle = abs(self.plane.data.vertices[vert_index].co.x) / (0.5 * self.plane_width) 
            z_height *= deviation_from_middle

            bpy.ops.transform.translate(
                value=(0, 0, z_height),
                orient_type='GLOBAL',
                use_proportional_edit=True, 
                proportional_edit_falloff='SMOOTH',
                proportional_size=bump_radius,
                release_confirm=True
            )
        
        bpy.context.scene.tool_settings.proportional_edit_falloff = original_falloff
        bpy.ops.object.mode_set(mode='OBJECT')
        print("[INFO] Finished raising riverbank.")

    
    def align_riverbank_edges(self, proportional_radius=1.8):
        print("[INFO] Aligning the z-coordinates of the riverbank boundary vertices to 0.")

        # --- Perform all operations in a single Edit Mode session for stability ---
        bpy.context.view_layer.objects.active = self.plane
        bpy.ops.object.mode_set(mode='EDIT')

        # Get the bmesh representation
        bm = bmesh.from_edit_mesh(self.plane.data)
        bm.verts.ensure_lookup_table()

        # Find all boundary vertices, which is a more reliable way to get the edges of a plane
        boundary_verts = [v for v in bm.verts if v.is_boundary]
        
        print(f"[INFO] Found {len(boundary_verts)} boundary vertices to align.")

        # Set up proportional editing
        original_falloff = bpy.context.scene.tool_settings.proportional_edit_falloff
        bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)

        # Align each boundary vertex to Z=0 using proportional editing
        for vert in boundary_verts:
            # Deselect all and select the current vertex
            bpy.ops.mesh.select_all(action='DESELECT')
            vert.select = True
            
            # Update the mesh selection before the operator is called
            bmesh.update_edit_mesh(self.plane.data)

            # Calculate the translation needed to bring the vertex to Z=0
            relative_translation = (0, 0, -vert.co.z)
            
            # Apply the translation
            bpy.ops.transform.translate(
                value=relative_translation,
                orient_type='GLOBAL',
                use_proportional_edit=True, 
                proportional_edit_falloff='SMOOTH',
                proportional_size=proportional_radius,
                release_confirm=True
            )

        # Restore original settings and exit Edit Mode
        bpy.context.scene.tool_settings.proportional_edit_falloff = original_falloff
        bpy.ops.object.mode_set(mode='OBJECT')
        print("[INFO] Finished aligning riverbank edges.")
        

    def create_riverbed(self):
        # Call the methods in sequence to build the terrain
        # After some testing, an appropriate subdivions is ((width * 2 - 2), (length * 2 -2))
        self.create_terrain(plane_width=20, plane_length=40, subdivisions=(38, 78))

        self.select_riverbed_vertices()
        self.dig_riverbed(min_pit_depth=0.2, max_pit_depth=0.5, pit_radius=2.5)
        self.raise_riverbank(min_riverbank_height=0.0, max_riverbank_height=0.2, bump_radius=3.0)    
        self.align_riverbank_edges(proportional_radius=3.0)
 
        ## shade_smooth() doesn't work here, 
        ## but it works well in rocky_river_terrain.py, after applying textures. 
        # self.plane.select_set(True)
        # bpy.context.view_layer.objects.active = self.plane   
        # bpy.ops.object.shade_smooth()

        print("[SUCCESS] A riverbed has been generated.")


    def move_riverbed(self, location=(0, 0, 0)):
        print(f"[INFO] Moving {self.plane.name} to {location}.")
        self.plane.location = location


    @staticmethod
    def run_demo():
        # Clear the scene
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        # Define the path to the texture
        # texture_file_path = "/home/robot/movie_blender_studio/asset/texture/rocks_ground_05_2k.blend/textures/rocks_ground_05_disp_2k.png"

        # Create an instance of the RiverTerrain class
        my_river = RiverbedGenerator()
        my_river.create_riverbed()
        my_river.get_riverbed_depth()
        my_river.move_riverbed(location=(-10, 20, 15))
        my_river.get_riverbed_depth()


# --- Main execution ---
if __name__ == "__main__":
    # This script is intended to be run within Blender's scripting environment
    try:
        RiverbedGenerator.run_demo()
    except Exception as e:
        print(f"[FATAL] An error occurred: {e}")
    
