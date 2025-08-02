import bpy
import bmesh
import os

class CreateDomeWithHdri:
    """
    A class to create a dome mesh object with HDRI texture applied directly to the mesh.
    
    Process:
    1. Generate a UV sphere at (0, 0, 0) with specified radius (e.g., 100 meters)
    2. Select all vertices with Z < (radius/10) and flatten them (Z=0)
    3. Result: Upper part of sphere with a flat circular floor
    4. Apply HDRI texture directly to the dome mesh with custom shader setup
    """
    
    def __init__(self, radius=100, hdri_path=None):
        """
        Initialize the dome creation parameters.
        
        Args:
            radius (float): Radius of the dome in meters (default: 100)
            hdri_path (str): Path to HDRI texture file
        """
        self.radius = radius
        self.hdri_path = hdri_path or "/home/robot/blender_assets/hdri/furstenstein_4k.exr"
        self.dome_object = None
    
    def create_sphere(self):
        """
        Create a UV sphere at (0, 0, 0) with the specified radius.
        """
        # Create a UV sphere at origin with specified radius
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=self.radius,
            segments=64,  # Higher resolution for better texture mapping
            ring_count=32,
            location=(0, 0, 0)
        )
        
        # Get the sphere object
        self.dome_object = bpy.context.active_object
        self.dome_object.name = "DomeWithHdri"
        
        print(f"Created UV sphere at (0, 0, 0) with radius: {self.radius} meters")
    
    def flatten_lower_vertices(self):
        """
        Select all vertices with Z < (radius/10) and flatten them by setting Z=0
        while preserving X and Y coordinates.
        """
        if not self.dome_object:
            raise RuntimeError("No dome object created. Call create_sphere() first.")
        
        # Calculate the Z threshold (1/10 of radius)
        z_threshold = self.radius / 10
        print(f"Flattening vertices with Z < {z_threshold}")
        
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
            if vert.co.z < z_threshold:
                vert.co.z = 0
                flattened_count += 1
        
        # Update the mesh
        bmesh.update_edit_mesh(self.dome_object.data)
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        print(f"Flattened {flattened_count} vertices with Z < {z_threshold}")
    
    def create_uv_map(self):
        """
        Create UV map for the dome to properly apply textures.
        """
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
        
        print("Created UV map for the dome")
    
    def add_modifiers_and_shading(self):
        """
        Add subsurface modifier and smooth shading to the dome.
        """
        if not self.dome_object:
            raise RuntimeError("No dome object created. Call create_sphere() first.")
        
        # Add a subsurface modifier for smoother shading
        subsurf_mod = self.dome_object.modifiers.new(name="Subsurf", type='SUBSURF')
        subsurf_mod.levels = 2
        subsurf_mod.render_levels = 3
        
        # Add smooth shading
        bpy.context.view_layer.objects.active = self.dome_object
        bpy.ops.object.shade_smooth()
        
        print("Added subsurface modifier and smooth shading")
    
    def apply_hdri_to_dome(self):
        """
        Apply HDRI texture directly to the dome mesh with custom shader setup.
        """
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
        output_node.location = (600, 0)
        
        # Mix shader node
        mix_shader = nodes.new(type='ShaderNodeMixShader')
        mix_shader.location = (400, 0)
        mix_shader.inputs['Fac'].default_value = 0.5  # 50/50 mix
        
        # Emission node with strength 50
        emission = nodes.new(type='ShaderNodeEmission')
        emission.location = (200, 100)
        emission.inputs['Strength'].default_value = 50.0  # Set to 50 as requested
        
        # Diffuse BSDF node
        diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        diffuse.location = (200, -100)
        
        # Environment texture node
        env_texture = nodes.new(type='ShaderNodeTexEnvironment')
        env_texture.location = (0, 0)
        
        # Load HDRI if it exists
        if os.path.exists(self.hdri_path):
            env_texture.image = bpy.data.images.load(self.hdri_path)
            print(f"Loaded HDRI: {self.hdri_path}")
        else:
            print(f"HDRI not found: {self.hdri_path}")
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
        print(f"Set mapping Z-location to: {mapping.inputs['Location'].default_value[2]}")
        
        # Create links
        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], env_texture.inputs['Vector'])
        
        if env_texture.image:
            links.new(env_texture.outputs['Color'], emission.inputs['Color'])
            links.new(env_texture.outputs['Color'], diffuse.inputs['Color'])
        else:
            # Fallback colors if no HDRI
            emission.inputs['Color'].default_value = (0.2, 0.2, 0.8, 1)  # Blue
            diffuse.inputs['Color'].default_value = (0.2, 0.2, 0.8, 1)   # Blue
        
        links.new(emission.outputs['Emission'], mix_shader.inputs[1])
        links.new(diffuse.outputs['BSDF'], mix_shader.inputs[2])
        links.new(mix_shader.outputs['Shader'], output_node.inputs['Surface'])
        
        # Apply material to dome
        if self.dome_object.data.materials:
            self.dome_object.data.materials[0] = material
        else:
            self.dome_object.data.materials.append(material)
        
        print("Applied HDRI texture directly to dome with custom shader setup")
        print("- Texture coordinate node")
        print("- Mapping node")
        print("- Environment texture node")
        print("- Emission node (strength: 50)")
        print("- Diffuse BSDF node")
        print("- Mix shader node")
        print(f"- Mapping Z-location set to: -(radius/5) = -{self.radius/5}")
    
    def cleanup_scene(self):
        """
        Remove any existing mesh objects from the scene.
        """
        # Clear existing mesh objects
        bpy.ops.object.select_all(action='DESELECT')
        # Select only mesh objects
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.select_set(True)
        # Delete selected objects
        if bpy.context.selected_objects:
            bpy.ops.object.delete()
        
        print("Cleaned up existing mesh objects")
    
    def create(self):
        """
        Execute the complete dome creation process.
        
        Returns:
            bpy.types.Object: The created dome object
        """
        # Clean up existing objects
        self.cleanup_scene()
        
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
        
        # Print summary
        z_threshold = self.radius / 10
        print(f"\nDome creation completed:")
        print(f"- Radius: {self.radius} meters")
        print(f"- HDRI: {self.hdri_path}")
        print(f"- Process:")
        print(f"  1. Generated a UV sphere at (0, 0, 0) with radius {self.radius} meters")
        print(f"  2. Selected all vertices with Z < {z_threshold}")
        print(f"  3. Set their Z-coordinate to 0 while preserving X and Y coordinates")
        print(f"  4. Created upper part of sphere with a flat circular floor")
        print(f"  5. Applied HDRI texture directly to the dome mesh with custom shader setup")
        print(f"  6. Set mapping Z-location to -(radius/5) = -{self.radius/5}")
        
        return self.dome_object

def setup_scene_for_dome(dome_object):
    """
    Set up lighting and camera for the dome.
    
    Args:
        dome_object (bpy.types.Object): The dome object to focus on
    """
    # Add a sun light
    bpy.ops.object.light_add(type='SUN', location=(100, 100, 100))
    sun = bpy.context.active_object
    sun.name = "DomeSunLight"
    sun.data.energy = 2
    
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
    track_to.target = dome_object
    track_to.track_axis = 'TRACK_NEGATIVE_Z'
    track_to.up_axis = 'UP_Y'
    
    print("Set up lighting and camera for the dome")

def render_dome_scene(output_path):
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

# Main execution
if __name__ == "__main__":
    # Create the dome using the class with 100-meter radius
    dome_creator = CreateDomeWithHdri(
        radius=100,  # 100 meters as specified
        hdri_path="/home/robot/blender_assets/hdri/furstenstein_4k.exr"
    )
    dome = dome_creator.create()
    
    # Set up the scene
    setup_scene_for_dome(dome)
    
    # Render the scene
    import os
    output_directory = os.path.expanduser("./blender_renders")
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, "dome_100m_with_hdri_on_mesh_v3.png")
    render_dome_scene(output_file)
    
    print(f"\nDome render saved to: {output_file}")