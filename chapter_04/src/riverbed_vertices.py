

import bpy
import random

class RiverTerrain:
    """
    A class to generate a river terrain mesh in Blender,
    featuring a pitted riverbed and texture displacement.
    """
    def __init__(self, plane_width=10, plane_length=20, subdivisions=99):
        """
        Initializes the terrain parameters.

        Args:
            plane_width (int): The width of the plane (X-axis).
            plane_length (int): The length of the plane (Y-axis).
            subdivisions (int): The number of cuts for subdivision.
        """
        self.plane_width = plane_width
        self.plane_length = plane_length
        self.subdivisions = subdivisions
        self.plane = None
        self.riverbed_indices = []

    
    def create_terrain(self):
        """
        1. Creates a rectangular plane and subdivides it.
        """
        print("[INFO] Creating terrain...")
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object:
            bpy.ops.object.delete(use_global=False)

        bpy.ops.mesh.primitive_plane_add(
            size=1,
            enter_editmode=False,
            align='WORLD',
            location=(0, 0, 0)
        )
        self.plane = bpy.context.active_object
        self.plane.name = "RiverTerrain"
        self.plane.scale = (self.plane_width, self.plane_length, 1)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=self.subdivisions)
        bpy.ops.object.mode_set(mode='OBJECT')
        print("[INFO] Terrain created.")   
 

    def select_riverbed_vertices(self):
        """
        2. Identifies vertices for the riverbed based on a random path.
        """
        if not self.plane:
            print("[ERROR] Terrain plane not found. Please run create_terrain() first.")
            return

        print("[INFO] Selecting riverbed vertices...")
        min_y = -self.plane_length / 4
        max_y = self.plane_length / 4
        river_widths = []
        for y_coord in range(int(min_y) * 10, int(max_y) * 10 + 1):
            sub_y_coord = y_coord / 10.0
            random_x_left = random.uniform(-1.5, -0.5)
            random_x_right = random.uniform(0.5, 2.0)
            river_widths.append((random_x_left, random_x_right, float(sub_y_coord)))

        for vert in self.plane.data.vertices:
            closest_point = min(river_widths, key=lambda p: abs(p[2] - vert.co.y))
            riverbed_left = closest_point[0]
            riverbed_right = closest_point[1]
            if riverbed_left < vert.co.x < riverbed_right:
                self.riverbed_indices.append(vert.index)

        if not self.riverbed_indices:
            print("No vertices found for the riverbed. Aborting.")
            return
  

    def dig_riverbed(self, min_pit_depth=0.5, max_pit_depth=1.5, pit_radius=1.8):
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
            z_depth = random.uniform(min_pit_depth, max_pit_depth)
            z_target = self.plane.data.vertices[vert_index].co.z - z_depth
            if (z_target < -1.0 * max_pit_depth):
                z_target = max(-1.0 * max_pit_depth, z_target)
            elif ((self.plane.data.vertices[vert_index].co.z - z_depth) > -1.0 * min_pit_depth):
                z_target = min(-1.0 * min_pit_depth, z_target)

            z_displace = z_target - self.plane.data.vertices[vert_index].co.z
            bpy.ops.transform.translate(
                value=(0, 0, z_displace),
                orient_type='GLOBAL',
                use_proportional_edit=True, 
                proportional_edit_falloff='SMOOTH',  # Use linear for more uniform effect
                proportional_size=pit_radius,
                release_confirm=True
            )
        
        bpy.context.scene.tool_settings.proportional_edit_falloff = original_falloff
        bpy.ops.object.mode_set(mode='OBJECT')
        print("[INFO] Finished digging riverbed.")


    def apply_displace_texture(self, texture_path, strength=0.5, midlevel=0.5):
        """
        4. Applies a displacement texture to the entire terrain.

        Args:
            texture_path (str): The file path to the displacement texture.
            strength (float): The strength of the displacement modifier.
            midlevel (float): The midlevel of the displacement modifier.
        """
        if not self.plane:
            print("[ERROR] Terrain plane not found. Please run create_terrain() first.")
            return
            
        print("[INFO] Applying displacement texture...")
        bpy.context.view_layer.objects.active = self.plane
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        try:
            disp_image = bpy.data.images.load(texture_path, check_existing=True)
            disp_image.colorspace_settings.name = 'Non-Color'
        except Exception as e:
            print(f"[ERROR] Could not load displacement texture: {e}")
            return

        disp_texture = bpy.data.textures.new(name="RockDisplacementTexture", type='IMAGE')
        disp_texture.image = disp_image

        disp_mod = self.plane.modifiers.new(name="Final_Displacement", type='DISPLACE')
        disp_mod.texture = disp_texture
        disp_mod.texture_coords = 'UV'
        disp_mod.uv_layer = "UVMap"
        disp_mod.strength = strength
        disp_mod.mid_level = midlevel
        print("[INFO] Displacement modifier added.")


# --- Main execution ---
if __name__ == "__main__":
    # Define the path to the texture
    texture_file_path = "/home/robot/movie_blender_studio/asset/texture/rocks_ground_05_2k.blend/textures/rocks_ground_05_disp_2k.png"

    # 1. Create an instance of the RiverTerrain class
    my_river = RiverTerrain(plane_width=10, plane_length=20, subdivisions=99)

    # 2. Call the methods in sequence to build the terrain
    my_river.create_terrain()
    my_river.select_riverbed_vertices()
    my_river.dig_riverbed()
    my_river.apply_displace_texture(texture_path=texture_file_path)

    print("\nScript finished: A river terrain has been generated.")
