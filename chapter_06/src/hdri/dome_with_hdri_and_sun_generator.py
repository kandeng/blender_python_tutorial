import bpy
import bmesh
import os
from math import atan2, pi, acos, sin, cos, asin
import numpy as np
import random
from typing import Union

class DomeHdriGenerator:
    """
    A class to create a dome mesh object with HDRI texture applied directly to the mesh.
    
    Process:
    1. Generate a UV sphere at (0, 0, 0) with specified radius (e.g., 100 meters)
    2. Select all vertices with Z < (radius/10) and flatten them (Z=0)
    3. Result: Upper part of sphere with a flat circular floor
    4. Apply HDRI texture directly to the dome mesh with custom shader setup
    5. Analyze HDRI to find brightest point and convert to 3D position on dome
    6. Place sunlight at that position
    """
    
    def __init__(self, radius=100, hdri_path=None):
        """
        Initialize the dome creation parameters.
        
        Args:
            radius (float): Radius of the dome in meters (default: 100)
            hdri_path (str): Path to HDRI texture file
        """
        self.radius = radius
        self.dome_object = None
        self.floor_vertex_indices = []

        self.hdri_path = hdri_path
        self.hdri_image = None
        self.emission = None
    

    def create_sphere(self):
        print(f"[INFO] DomeHdriGenerator::create_sphere(), Create a UV sphere at (0, 0, 0) with radius: {self.radius}.")
        
        # Create a UV sphere at origin with specified radius
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=self.radius,
            segments=128,  # Higher resolution for better texture mapping
            ring_count=64,
            location=(0, 0, 0)
        )
        
        # Get the sphere object
        self.dome_object = bpy.context.active_object
        self.dome_object.name = "DomeWithHdri"

    
    def flatten_lower_vertices(self):
        print(f"[INFO] DomeHdriGenerator::flatten_lower_vertices(),")
        print(f"       Select all vertices with Z < (radius/10) and flatten them by setting Z=0, ")
        print(f"       while preserving X and Y coordinates.")
        
        if not self.dome_object:
            raise RuntimeError("No dome object created. Call create_sphere() first.")
        
        self.floor_vertex_indices = []

        # Calculate the Z threshold (1/10 of radius)
        z_threshold = -1.0 * self.radius / 10
        
        # Enter edit mode
        bpy.context.view_layer.objects.active = self.dome_object
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Get the bmesh representation
        bm = bmesh.from_edit_mesh(self.dome_object.data)
        bm.verts.ensure_lookup_table()
        
        # Process vertices with Z < threshold
        flattened_count = 0
        for vert in bm.verts:
            # Flatten vertices by setting Z-coordinate to 0
            # while preserving X and Y coordinates
            if vert.co.z <= z_threshold:
                vert.co.z = z_threshold
                self.floor_vertex_indices.append(vert.index) # Store index instead of BMVert
                flattened_count += 1
        
        # Update the mesh
        bmesh.update_edit_mesh(self.dome_object.data)
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        print(f"Flattened {flattened_count} vertices with Z < {z_threshold}")
    
    
    def punch(self, target_obj, target_vertex_idx, target_location: Union[float, tuple], radius):
        # --- Perform all operations in a single Edit Mode session for efficiency ---
        bpy.context.view_layer.objects.active = target_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Set up proportional editing settings
        original_falloff = bpy.context.scene.tool_settings.proportional_edit_falloff
        bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)

        """
        Applies a proportional editing translation to a specific vertex.
        This function assumes it is called when the object is already in Edit Mode.
        """
        # Get the bmesh representation
        bm = bmesh.from_edit_mesh(target_obj.data)
        bm.verts.ensure_lookup_table()

        # Deselect all vertices first
        for v in bm.verts:
            v.select = False
        
        # Select the target vertex
        try:
            target_vertex = bm.verts[target_vertex_idx]
            target_vertex.select = True
        except IndexError:
            print(f"[ERROR] Vertex index {target_vertex_idx} is out of range.")
            return

        # Ensure the selection is updated in the mesh data
        bmesh.update_edit_mesh(target_obj.data)

        # Apply the translation with proportional editing
        target_tuple = (0, 0, 0)
        if isinstance(target_location, (int, float)):
            target_tuple = (0, 0, target_location)
        elif isinstance(target_location, tuple):
            target_tuple = target_location

        bpy.ops.transform.translate(
            value=target_tuple,
            orient_type='GLOBAL',
            use_proportional_edit=True, 
            proportional_edit_falloff='SMOOTH',
            proportional_size=radius,
            release_confirm=True
        )        

        # Restore original settings and exit Edit Mode
        bpy.context.scene.tool_settings.proportional_edit_falloff = original_falloff
        bpy.ops.object.mode_set(mode='OBJECT')

    
    def floor_punch(self, num_punches=5, punch_height=10, punch_radius=10):
        """
        Applies several random "punches" (proportional edits) to the floor vertices.
        """
        if not self.floor_vertex_indices:
            print("[WARN] No floor vertices to punch.")
            return

        print(f"[INFO] Applying {num_punches} random punches to the floor, with punch_height={punch_height}, punch_radius={punch_radius}...")

        """
        # --- Perform all operations in a single Edit Mode session for efficiency ---
        bpy.context.view_layer.objects.active = self.dome_object
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Set up proportional editing settings
        original_falloff = bpy.context.scene.tool_settings.proportional_edit_falloff
        bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)        
        """

        # Randomly select some vertex indices to punch
        if len(self.floor_vertex_indices) < num_punches:
            print(f"[WARN] Not enough floor vertices for {num_punches} punches. Using {len(self.floor_vertex_indices)} instead.")
            selected_floor_indices = self.floor_vertex_indices
        else:
            selected_floor_indices = random.sample(self.floor_vertex_indices, num_punches)

        # Iterate through the selected indices and apply the punch
        for vert_idx in selected_floor_indices:
            self.punch(
                target_obj=self.dome_object, 
                target_vertex_idx=vert_idx,
                target_location=punch_height, 
                radius=punch_radius
            )
        
        """"
        # Restore original settings and exit Edit Mode
        bpy.context.scene.tool_settings.proportional_edit_falloff = original_falloff
        bpy.ops.object.mode_set(mode='OBJECT')        
        """


    def set_floor_basin_height(self, rectangular_region=(-1.0, -1.0, 1.0, 1.0), height_to_change: float=0.0):
        print(f"[INFO] DomeHdriGenerator::set_floor_regional_height(),", end=" ")
        print(f"rectangular_region={rectangular_region}, height_to_change={height_to_change}.")

        if not self.dome_object:
            raise RuntimeError("No dome object created. Call create_sphere() first.")
        
        if not self.floor_vertex_indices:
            print("[WARN] No floor vertices to modify.")
            return

        # Enter edit mode to safely modify mesh data
        bpy.context.view_layer.objects.active = self.dome_object
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Get a fresh bmesh representation
        bm = bmesh.from_edit_mesh(self.dome_object.data)
        bm.verts.ensure_lookup_table()

        min_x, min_y, max_x, max_y = rectangular_region
        modified_count = 0

        # Iterate through the stored vertex indices
        for vert_index in self.floor_vertex_indices:
            vert = bm.verts[vert_index]
            
            # Check if the vertex is within the rectangular region
            if min_x < vert.co.x < max_x and min_y < vert.co.y < max_y:
                vert.co.z += height_to_change
                modified_count += 1
                
        # Write the changes back to the mesh
        bmesh.update_edit_mesh(self.dome_object.data)
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        print(f"[INFO] Modified height for {modified_count} vertices within {rectangular_region}.")


    def create_uv_map(self):
        print(f"[INFO] DomeHdriGenerator::create_uv_map(), Create UV map for the dome to properly apply textures.")
        
        if not self.dome_object:
            raise RuntimeError("No dome object created. Call create_sphere() first.")
        
        # Enter edit mode
        bpy.context.view_layer.objects.active = self.dome_object
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Select all faces
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Create smart UV projection
        bpy.ops.uv.smart_project()
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        

    def add_modifiers_and_shading(self):
        print(f"[INFO] DomeHdriGenerator::add_modifiers_and_shading(), Add subsurface modifier and smooth shading to the dome.")
        
        if not self.dome_object:
            raise RuntimeError("No dome object created. Call create_sphere() first.")
        
        # Add a subsurface modifier for smoother shading
        subsurf_mod = self.dome_object.modifiers.new(name="Subsurf", type='SUBSURF')
        subsurf_mod.levels = 2
        subsurf_mod.render_levels = 3
        
        # Add smooth shading
        bpy.context.view_layer.objects.active = self.dome_object
        bpy.ops.object.shade_smooth()

    
    def apply_hdri_to_dome(self):
        print(f"[INFO] DomeHdriGenerator::apply_hdri_to_dome(), Apply HDRI texture directly to the dome mesh with custom shader setup.")
        
        if not self.dome_object:
            raise RuntimeError("No dome object created. Call create_sphere() first.")
        
        # Create a new material for the dome
        material = bpy.data.materials.new(name="DomeMaterial")
        material.use_nodes = True
        
        # Clear default nodes
        material.node_tree.nodes.clear()
        
        # Get node tree references
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Create shader nodes
        # Output node
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (800, 0)
        
        # Mix shader node
        mix_shader = nodes.new(type='ShaderNodeMixShader')
        mix_shader.location = (600, 0)
        mix_shader.inputs['Fac'].default_value = 0.5  # 50/50 mix
        
        # Emission node with strength 50
        self.emission = nodes.new(type='ShaderNodeEmission')
        self.emission.location = (400, 100)
        self.emission.inputs['Strength'].default_value = 50.0 
        
        # Diffuse BSDF node
        diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        diffuse.location = (400, -100)
        
        # Environment texture node
        env_texture = nodes.new(type='ShaderNodeTexEnvironment')
        env_texture.location = (0, 0)
        
        # Load HDRI if it exists
        if os.path.exists(self.hdri_path):
            self.hdri_image = bpy.data.images.load(self.hdri_path)
            env_texture.image = self.hdri_image
            print(f"[INFO] Loaded HDRI: {self.hdri_path}")
        else:
            print(f"[WARN] HDRI not found: {self.hdri_path}")
            # Create a simple gradient as fallback
            env_texture.image = None
        
        # Texture coordinate node
        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        tex_coord.location = (-400, 0)
        
        # Mapping node
        mapping = nodes.new(type='ShaderNodeMapping')
        mapping.location = (-200, 0)
        
        # Set the Z-location of the mapping node as 1/5 of the dome radius times minus 1
        mapping.inputs['Location'].default_value[2] = -(self.radius / 5)
      
        # Create links
        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], env_texture.inputs['Vector'])
        
        if env_texture.image:
            links.new(env_texture.outputs['Color'], self.emission.inputs['Color'])
            links.new(env_texture.outputs['Color'], diffuse.inputs['Color'])
        else:
            # Fallback colors if no HDRI
            self.emission.inputs['Color'].default_value = (0.2, 0.2, 0.8, 1)  # Blue
            diffuse.inputs['Color'].default_value = (0.2, 0.2, 0.8, 1)   # Blue
        
        links.new(self.emission.outputs['Emission'], mix_shader.inputs[1])
        links.new(diffuse.outputs['BSDF'], mix_shader.inputs[2])
        links.new(mix_shader.outputs['Shader'], output_node.inputs['Surface'])
        
        # Apply material to dome
        if self.dome_object.data.materials:
            self.dome_object.data.materials[0] = material
        else:
            self.dome_object.data.materials.append(material)
        
        print(f"[INFO] DomeHdriGenerator::apply_hdri_to_dome(), Applied HDRI texture directly to dome with custom shader setup")
        print(f"     - Texture coordinate node")
        print(f"     - Mapping node")
        print(f"     - Environment texture node")
        print(f"     - Emission node (strength: 50)")
        print(f"     - Diffuse BSDF node")
        print(f"     - Mix shader node")
        print(f"     - Mapping Z-location set to: -(radius/5) = -{self.radius/5}")
    

    def set_hdri_brightness(self, brightness: float=2.5):
        self.emission.inputs['Strength'].default_value = brightness


    def find_brightest_point_in_hdri(self):
        print(f"[INFO] DomeHdriGenerator::find_brightest_point_in_hdri(), this will take several minutes to finish.")
        print(f"       Enumerate all pixels in the HDRI image and find the brightest point based on 4x4 pixel neighborhoods.")
        print(f"       Return: tuple: (brightest_uv_coord, max_brightness_value) ")

        if not self.hdri_image:
            raise RuntimeError("HDRI image not available.")
        
        # Get HDRI image dimensions
        hdri_width, hdri_height = self.hdri_image.size
        
        # Store HDRI pixels for processing
        # Note: Blender stores pixels as [R,G,B,A,R,G,B,A,...] with bottom-left origin
        if not self.hdri_image.pixels:
            self.hdri_image.reload()  # Ensure pixels are loaded
        
        pixels = np.array(self.hdri_image.pixels[:])
        pixels = pixels.reshape((hdri_height, hdri_width, 4))  # Reshape to HxWx4
        
        # Flip vertically since Blender uses bottom-left origin but we need top-left for calculations
        pixels = np.flipud(pixels)
        
        max_brightness = -1
        brightest_uv = (0, 0)
        
        # Process all pixels in the HDRI
        for v in range(2, hdri_height - 2):  # Avoid edges for 4x4 neighborhood
            for u in range(2, hdri_width - 2):
                # Calculate brightness in a 4x4 neighborhood
                brightness = 0
                count = 0
                
                for du in range(-2, 2):
                    for dv in range(-2, 2):
                        nu = u + du
                        nv = v + dv
                        
                        # Check bounds
                        if 0 <= nu < hdri_width and 0 <= nv < hdri_height:
                            # Sum RGB values
                            brightness += pixels[nv, nu, 0] + pixels[nv, nu, 1] + pixels[nv, nu, 2]
                            count += 1
                
                # Average brightness
                if count > 0:
                    brightness /= count
                    
                    # Update maximum if this is brighter
                    if brightness > max_brightness:
                        max_brightness = brightness
                        # Convert pixel coordinates to UV coordinates (0-1 range)
                        uv_u = u / (hdri_width - 1)
                        uv_v = v / (hdri_height - 1)
                        # uv_v = (v + self.radius / 10) / (hdri_height - 1)
                        # uv_v = v / (hdri_height - 1) + self.radius / 10
                        brightest_uv = (uv_u, uv_v)
        
        if max_brightness > 0:
            print(f"[INFO] Found brightest point in HDRI at UV: {brightest_uv}, Brightness value: {max_brightness}")
            return (brightest_uv, max_brightness)
        else:
            print("[WARN] Could not find a brightest point in the HDRI")
            # Return a default UV position
            return ((0.5, 0.5), 0)
    

    def convert_hdri_uv_to_3d(self, uv_coord):
        print(f"[INFO] DomeHdriGenerator::convert_hdri_uv_to_3d(), Convert 2D UV coordinate in HDRI to 3D coordinate on the dome surface.")
        print(f"       - u (0-1) maps to longitude (0 to 2π)")
        print(f"       - v (0-1) maps to latitude (π/2 to -π/2)")
        print(f"       - uv_coord (tuple): UV coordinates (u, v) in range [0, 1]")
        print(f"       - Return: 3D coordinates (x, y, z) tuple on the dome surface")

        u, v = uv_coord
        
        # Convert UV to spherical coordinates
        # Longitude: 0 to 2π
        # longitude = u * 2 * pi
        longitude = (0.5 - u) * 2 * pi
        # Latitude: π/2 to -π/2 (90° to -90°)
        # latitude = (0.5 - v) * pi
        latitude = v * pi
        
        # Convert spherical to Cartesian coordinates
        # x = self.radius * cos(latitude) * cos(longitude)
        # y = self.radius * cos(latitude) * sin(longitude)
        # z = self.radius * sin(latitude)
        x = self.radius * sin(latitude) * cos(longitude)
        y = self.radius * sin(latitude) * sin(longitude)
        # z = self.radius * cos(latitude)
        z = self.radius * cos(latitude) + self.radius / 10

        # Ensure the point is on the upper half of the dome (z > 0)
        if z < 0:
            z = abs(z)  # Flip to upper half
            
        print(f"Converted UV ({u:.3f}, {v:.3f}) to 3D ({x:.2f}, {y:.2f}, {z:.2f})")
        return (x, y, z)
    

    def add_sunlight_at_brightest_point(self, brightest_3d_point):
        print(f"[INFO] DomeHdriGenerator::add_sunlight_at_brightest_point(),  Add a sunlight at the brightest point on the dome.")

        # Extract coordinates
        x, y, z = brightest_3d_point
        
        # Position the sun light just above the dome surface
        sun_height = self.radius * 0.1  # 10% of dome radius above surface
        sun_x, sun_y, sun_z = x + sun_height, y + sun_height, z + sun_height
        
        # Add a sun light
        bpy.ops.object.light_add(type='SUN', location=(sun_x, sun_y, sun_z))
        sun = bpy.context.active_object
        sun.name = "HdriSunLight"
        
        # Point the sun toward the center of the dome
        # Calculate direction vector from sun to dome center (0,0,0)
        direction = (-x, -y, -z)
        
        # Normalize the direction vector
        length = (x**2 + y**2 + z**2)**0.5
        if length > 0:
            dir_x, dir_y, dir_z = -x/length, -y/length, -z/length
            
            # Set sun rotation to point toward center
            # This is a simplified approach - in practice, you might need to calculate
            # the exact Euler angles, but the track_to constraint below handles this
            sun.rotation_euler = (0, 0, 0)
        
        # Add track-to constraint to point sun at dome center
        track_to = sun.constraints.new(type='TRACK_TO')
        track_to.target = self.dome_object
        track_to.track_axis = 'TRACK_NEGATIVE_Z'
        track_to.up_axis = 'UP_Y'
        
        # Set energy to 100 * dome radius
        sun.data.energy = 100 * self.radius
        
        print(f"[INFO] Added sunlight at position: ({sun_x}, {sun_y}, {sun_z}), Sunlight energy: {sun.data.energy}")
        return sun
    

    def cleanup_scene(self):
        print(f"[INFO] DomeHdriGenerator::cleanup_scene(), Remove any existing mesh objects from the scene.")
 
        # Clear existing mesh objects
        bpy.ops.object.select_all(action='DESELECT')
        # Select only mesh objects
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' or obj.type == 'LIGHT':
                obj.select_set(True)
        # Delete selected objects
        if bpy.context.selected_objects:
            bpy.ops.object.delete()
    

    def create(self, radius=100, hdri_path=None):
        print(f"[INFO] DomeHdriGenerator::create(), Execute the complete dome creation process.")
 
        self.radius = radius
        self.hdri_path = hdri_path or "/home/robot/blender_assets/hdri/furstenstein_4k.exr"
        
        # Create the sphere
        self.create_sphere()
        
        # Flatten vertices with Z < (radius/10)
        self.flatten_lower_vertices()
        
        # Create UV map
        self.create_uv_map()
        
        # Add modifiers and shading
        self.add_modifiers_and_shading()
        
        # Apply HDRI texture to dome
        self.apply_hdri_to_dome()
        
        # Find brightest point in HDRI
        brightest_uv, brightness = self.find_brightest_point_in_hdri()
        
        # Convert brightest UV to 3D coordinates on dome
        brightest_3d = self.convert_hdri_uv_to_3d(brightest_uv)
        
        # Add sunlight at brightest point
        sun = self.add_sunlight_at_brightest_point(brightest_3d)        
        

        # Print summary
        z_threshold = self.radius / 10
        print(f"[INFO] Dome creation completed:")
        print(f"     - Radius: {self.radius} meters")
        print(f"     - HDRI: {self.hdri_path}")
        print(f"     - Process:")
        print(f"       1. Generated a UV sphere at (0, 0, 0) with radius {self.radius} meters")
        print(f"       2. Selected all vertices with Z < {z_threshold}")
        print(f"       3. Set their Z-coordinate to 0 while preserving X and Y coordinates")
        print(f"       4. Created upper part of sphere with a flat circular floor")
        print(f"       5. Applied HDRI texture directly to the dome mesh with custom shader setup")
        print(f"       6. Set mapping Z-location to -(radius/5) = -{self.radius/5}")
    
        print(f"       7. Found brightest point in HDRI at UV: {brightest_uv}")
        print(f"       8. Converted to 3D point on dome: {brightest_3d}")
        print(f"       9. Added sunlight at that point with energy: {sun.data.energy}")        

        return self.dome_object


    def setup_scene_for_dome(self):
        print(f"[INFO] DomeHdriGenerator::setup_scene_for_dome(), for demo and testing.")

        # Add a fill light
        bpy.ops.object.light_add(type='POINT', location=(-50, -50, 50))
        fill_light = bpy.context.active_object
        fill_light.name = "FillLight"
        fill_light.data.energy = 10000  # Adjusted for 100m scale
        
        # Set up camera
        bpy.ops.object.camera_add(location=(150, -150, 100))
        camera = bpy.context.active_object
        camera.name = "DomeCamera"
        bpy.context.scene.camera = camera
        
        # Add track-to constraint to camera
        track_to = camera.constraints.new(type='TRACK_TO')
        track_to.target = self.dome_object
        track_to.track_axis = 'TRACK_NEGATIVE_Z'
        track_to.up_axis = 'UP_Y'
        
        print("Set up additional lighting and camera for the dome")


    def render_dome_scene(self, output_path):
        print(f"[INFO] DomeHdriGenerator::render_dome_scene(), for demo and testing.")
        """
        Render the dome scene.
        
        Args:
            output_path (str): Path to save the rendered image
        """
        # Set render settings
        scene = bpy.context.scene
        
        # Try to set the render engine, with fallback for newer Blender versions
        try:
            scene.render.engine = 'BLENDER_EEVEE'
            print("Using BLENDER_EEVEE render engine")
        except:
            try:
                scene.render.engine = 'BLENDER_EEVEE_NEXT'
                print("Using BLENDER_EEVEE_NEXT render engine")
            except Exception as e:
                print(f"Failed to set render engine: {e}")
                print("Using default render engine")
        
        scene.eevee.taa_render_samples = 64
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
        scene.render.resolution_percentage = 50
        scene.render.filepath = output_path
        
        # Enable ambient occlusion for better depth perception
        scene.eevee.use_gtao = True
        
        # Render
        print(f"Rendering dome scene to: {output_path}")
        bpy.ops.render.render(write_still=True)
        print("Rendering completed!")


    @staticmethod
    def run_demo():
        # Create the dome using the class with 100-meter radius
        dome_hdri = DomeHdriGenerator()
        dome_hdri.cleanup_scene()

        dome = dome_hdri.create(
            radius=100,  # 100 meters as specified
            hdri_path="/home/robot/blender_assets/hdri/kloppenheim_06_4k.exr"
        )
        dome_hdri.set_hdri_brightness(brightness=2.0)

        dome_hdri.floor_punch()

        dome_hdri.set_floor_basin_height(
            rectangular_region=(-25.0, -30.0, 15.0, 20.0), 
            height_to_change=-10.0
        )
        
        # Set up the scene
        dome_hdri.setup_scene_for_dome()
        
        # Render the scene
        import os
        output_directory = os.path.expanduser("./blender_renders")
        os.makedirs(output_directory, exist_ok=True)
        output_file = os.path.join(output_directory, "dome_100m_with_hdri_sunlight_v2.png")
        dome_hdri.render_dome_scene(output_file)
        
        print(f"\nDome render saved to: {output_file}")
    

# Main execution
if __name__ == "__main__":
    DomeHdriGenerator.run_demo()