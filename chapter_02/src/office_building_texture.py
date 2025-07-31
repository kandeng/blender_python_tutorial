import bpy
import os

def setup_office_building_cube(texture_dir):
    """
    Create a cube and apply office building textures with complex shading nodes
    """
    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Create a cube for our office building
    bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 2))
    building = bpy.context.active_object
    building.name = "OfficeBuilding"
    
    # Subdivide the cube for better texture mapping
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=10)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create UV map for the cube
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create a new material for the office building
    material = bpy.data.materials.new(name="OfficeBuildingMaterial")
    material.use_nodes = True
    material.node_tree.nodes.clear()
    
    # Get the node tree
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Create nodes
    # Output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (1200, 0)
    
    # Principled BSDF node for more realistic opaque materials
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.location = (800, 0)
    principled_node.inputs['Roughness'].default_value = 0.7
    # Use 'Specular IOR Level' instead of 'Specular' in newer Blender versions
    if 'Specular IOR Level' in principled_node.inputs:
        principled_node.inputs['Specular IOR Level'].default_value = 0.3
    elif 'Specular' in principled_node.inputs:
        principled_node.inputs['Specular'].default_value = 0.3
    
    # Image texture node for main facade
    image_texture = nodes.new(type='ShaderNodeTexImage')
    image_texture.location = (400, 100)
    
    # Check for texture files in the directory
    texture_files = []
    if os.path.exists(texture_dir):
        for file in os.listdir(texture_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.exr')):
                texture_files.append(file)
    
    # Try to load a color texture if available
    base_color_texture = None
    for file in texture_files:
        if 'color' in file.lower() or 'diffuse' in file.lower() or 'albedo' in file.lower():
            base_color_texture = os.path.join(texture_dir, file)
            break
    
    # If no specific color texture found, use the first image
    if not base_color_texture and texture_files:
        base_color_texture = os.path.join(texture_dir, texture_files[0])
    
    # Load the texture if found
    if base_color_texture and os.path.exists(base_color_texture):
        image_texture.image = bpy.data.images.load(base_color_texture)
        print(f"Loaded texture: {base_color_texture}")
    else:
        # Create a default color if no texture found
        image_texture.image = None
        print("No texture found, using default color")
        principled_node.inputs['Base Color'].default_value = (0.1, 0.1, 0.4, 1)  # Dark blue color
    
    # UV map node
    uv_map = nodes.new(type='ShaderNodeUVMap')
    uv_map.location = (200, 200)
    uv_map.uv_map = "UVMap"
    
    # Normal map node (if normal map exists)
    normal_map = nodes.new(type='ShaderNodeNormalMap')
    normal_map.location = (600, -200)
    
    # Image texture for normal map
    normal_texture = nodes.new(type='ShaderNodeTexImage')
    normal_texture.location = (400, -200)
    
    # Check for normal map
    normal_map_file = None
    for file in texture_files:
        if 'normal' in file.lower() or 'nmap' in file.lower():
            normal_map_file = os.path.join(texture_dir, file)
            break
    
    # Load normal map if found
    if normal_map_file and os.path.exists(normal_map_file):
        normal_texture.image = bpy.data.images.load(normal_map_file)
        normal_texture.image.colorspace_settings.name = 'Non-Color'
        print(f"Loaded normal map: {normal_map_file}")
    
    # Emission node for windows
    emission_node = nodes.new(type='ShaderNodeEmission')
    emission_node.location = (600, -400)
    emission_node.inputs['Color'].default_value = (0.1, 0.2, 0.8, 1)  # Blue for lit windows
    emission_node.inputs['Strength'].default_value = 2.0
    
    # Noise texture for window pattern
    noise_texture = nodes.new(type='ShaderNodeTexNoise')
    noise_texture.location = (400, -400)
    noise_texture.inputs['Scale'].default_value = 10.0
    noise_texture.inputs['Detail'].default_value = 4.0
    
    # Color ramp for emission mask
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (500, -400)
    color_ramp.color_ramp.elements[0].position = 0.7
    color_ramp.color_ramp.elements[1].position = 0.9
    
    # Group node example (create a simple group for window patterns)
    # In practice, you would create a more complex node group
    window_pattern_group = bpy.data.node_groups.new(type='ShaderNodeTree', name='WindowPattern')
    window_pattern_group.nodes.new(type='ShaderNodeTexNoise')
    window_pattern_group.nodes.new(type='ShaderNodeValToRGB')
    
    # Group node in the main material
    group_node = nodes.new(type='ShaderNodeGroup')
    group_node.location = (200, -400)
    group_node.node_tree = window_pattern_group
    
    # Vector nodes for texture transformations
    mapping_node = nodes.new(type='ShaderNodeMapping')
    mapping_node.location = (0, 200)
    
    # Connect nodes
    # UV mapping
    links.new(uv_map.outputs['UV'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], image_texture.inputs['Vector'])
    
    # Base color connection
    if image_texture.image:
        links.new(image_texture.outputs['Color'], principled_node.inputs['Base Color'])
    
    # Normal map connections
    if normal_texture.image:
        links.new(normal_texture.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], principled_node.inputs['Normal'])
    
    # Emission connections for windows
    links.new(noise_texture.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], emission_node.inputs['Strength'])
    
    # Mix shader to combine principled material with emission for windows
    mix_shader = nodes.new(type='ShaderNodeMixShader')
    mix_shader.location = (1000, 0)
    
    # Create a transparent shader for the mix (not used now, but keeping for node completeness)
    transparent_shader = nodes.new(type='ShaderNodeBsdfTransparent')
    transparent_shader.location = (800, -200)
    
    # Connect shaders to mix shader
    links.new(principled_node.outputs['BSDF'], mix_shader.inputs[1])
    links.new(emission_node.outputs['Emission'], mix_shader.inputs[2])
    links.new(color_ramp.outputs['Color'], mix_shader.inputs['Fac'])
    
    # Final connection to output
    links.new(mix_shader.outputs['Shader'], output_node.inputs['Surface'])
    
    # Apply material to the building
    if building.data.materials:
        building.data.materials[0] = material
    else:
        building.data.materials.append(material)
    
    # Remove the ground plane creation (as requested)
    
    # Add a sun light
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 10))
    sun = bpy.context.active_object
    sun.name = "Sun"
    sun.data.energy = 3
    
    # Set up camera
    bpy.ops.object.camera_add(location=(8, -8, 5))
    camera = bpy.context.active_object
    camera.name = "BuildingCamera"
    bpy.context.scene.camera = camera
    
    # Add a track-to constraint to the camera
    track_to = camera.constraints.new(type='TRACK_TO')
    track_to.target = building
    track_to.track_axis = 'TRACK_NEGATIVE_Z'
    track_to.up_axis = 'UP_Y'
    
    print("Office building scene created with the following nodes:")
    print("- Image texture node")
    print("- UV map node")
    print("- Principled BSDF node (for opaque material)")
    print("- Emission node")
    print("- Color nodes")
    print("- Vector nodes (Mapping)")
    print("- Group node (WindowPattern)")
    print("- Normal map node")
    print("- Noise texture node")
    print("- Color ramp node")
    
    if base_color_texture:
        print(f"Applied texture: {base_color_texture}")
    else:
        print("Using default color (no texture found)")

def render_scene(output_path):
    """
    Render the scene
    """
    # Set render settings
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError as e:
        print(str(e))
        scene.render.engine = 'BLENDER_EEVEE_NEXT'

    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 1920  # 640
    scene.render.resolution_y = 1080  # 480
    scene.render.resolution_percentage = 50
    scene.render.filepath = output_path
    
    # Render
    print(f"Rendering scene to: {output_path}")
    bpy.ops.render.render(write_still=True)
    print("Rendering completed!")

# Main execution
if __name__ == "__main__":
    # Texture directory
    texture_directory = "/home/robot/blender_assets/texture/Facade017_4K"
    
    # Output path
    output_directory = os.path.expanduser("./blender_renders")
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, "office_building_render.png")
    
    # Create scene
    setup_office_building_cube(texture_directory)
    
    # Render scene
    render_scene(output_file)
    
    print(f"Office building render saved to: {output_file}")