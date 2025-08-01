import bpy
import os

def setup_wood_floor(texture_dir):
    """
    Create a floor with wood texture using color, displacement, roughness, and normal maps
    """
    # Clear existing objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Create a large plane for the floor
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "WoodFloor"
    
    # Subdivide the plane for displacement mapping
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=50)  # High subdivision for displacement
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create UV map for the floor
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Create a new material for the wood floor
    material = bpy.data.materials.new(name="WoodFloorMaterial")
    material.use_nodes = True
    
    # Clear default nodes
    material.node_tree.nodes.clear()
    
    # Get node tree references
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    
    # Create shader nodes
    # Output node
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (1200, 0)
    
    # Principled BSDF node
    principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_node.location = (800, 0)
    principled_node.inputs['Roughness'].default_value = 0.8
    
    # Check for texture files in the directory
    texture_files = {}
    if os.path.exists(texture_dir):
        for file in os.listdir(texture_dir):
            file_path = os.path.join(texture_dir, file)
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                if 'color' in file.lower() or 'albedo' in file.lower():
                    texture_files['color'] = file_path
                elif 'displacement' in file.lower() or 'height' in file.lower():
                    texture_files['displacement'] = file_path
                elif 'roughness' in file.lower():
                    texture_files['roughness'] = file_path
                elif 'normal' in file.lower() and 'gl' in file.lower():
                    texture_files['normal_gl'] = file_path
                elif 'metalness' in file.lower() or 'metallic' in file.lower():
                    texture_files['metalness'] = file_path
    
    # UV map node
    uv_map = nodes.new(type='ShaderNodeUVMap')
    uv_map.location = (0, 400)
    uv_map.uv_map = "UVMap"
    
    # Mapping node for scaling textures
    mapping_node = nodes.new(type='ShaderNodeMapping')
    mapping_node.location = (200, 400)
    # Scale the texture to make it more visible
    mapping_node.inputs['Scale'].default_value = (2.0, 2.0, 2.0)
    
    # Connect UV to mapping
    links.new(uv_map.outputs['UV'], mapping_node.inputs['Vector'])
    
    # Color texture
    if 'color' in texture_files:
        color_texture = nodes.new(type='ShaderNodeTexImage')
        color_texture.location = (400, 400)
        color_texture.image = bpy.data.images.load(texture_files['color'])
        links.new(mapping_node.outputs['Vector'], color_texture.inputs['Vector'])
        links.new(color_texture.outputs['Color'], principled_node.inputs['Base Color'])
        print(f"Loaded color map: {texture_files['color']}")
    else:
        # Default color if no texture found
        principled_node.inputs['Base Color'].default_value = (0.2, 0.1, 0.05, 1)  # Brown color
        print("No color map found, using default brown color")
    
    # Roughness texture
    if 'roughness' in texture_files:
        roughness_texture = nodes.new(type='ShaderNodeTexImage')
        roughness_texture.location = (400, 200)
        roughness_texture.image = bpy.data.images.load(texture_files['roughness'])
        # Important: Set colorspace to Non-Color for roughness maps
        roughness_texture.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping_node.outputs['Vector'], roughness_texture.inputs['Vector'])
        links.new(roughness_texture.outputs['Color'], principled_node.inputs['Roughness'])
        print(f"Loaded roughness map: {texture_files['roughness']}")
    else:
        # Default roughness value
        principled_node.inputs['Roughness'].default_value = 0.8
        print("No roughness map found, using default value")
    
    # Normal map
    if 'normal_gl' in texture_files:
        # Normal map texture
        normal_texture = nodes.new(type='ShaderNodeTexImage')
        normal_texture.location = (400, 0)
        normal_texture.image = bpy.data.images.load(texture_files['normal_gl'])
        # Important: Set colorspace to Non-Color for normal maps
        normal_texture.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping_node.outputs['Vector'], normal_texture.inputs['Vector'])
        
        # Normal map node
        normal_map_node = nodes.new(type='ShaderNodeNormalMap')
        normal_map_node.location = (600, 0)
        # For GL normal maps, we typically don't need to change the space
        links.new(normal_texture.outputs['Color'], normal_map_node.inputs['Color'])
        links.new(normal_map_node.outputs['Normal'], principled_node.inputs['Normal'])
        print(f"Loaded GL normal map: {texture_files['normal_gl']}")
    else:
        print("No GL normal map found")
    
    # Displacement map
    if 'displacement' in texture_files:
        displacement_texture = nodes.new(type='ShaderNodeTexImage')
        displacement_texture.location = (400, -200)
        displacement_texture.image = bpy.data.images.load(texture_files['displacement'])
        # Important: Set colorspace to Non-Color for displacement maps
        displacement_texture.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping_node.outputs['Vector'], displacement_texture.inputs['Vector'])
        
        # Displacement node
        displacement_node = nodes.new(type='ShaderNodeDisplacement')
        displacement_node.location = (600, -200)
        displacement_node.inputs['Scale'].default_value = 0.1  # Adjust displacement strength
        displacement_node.inputs['Midlevel'].default_value = 0.5
        links.new(displacement_texture.outputs['Color'], displacement_node.inputs['Height'])
        links.new(displacement_node.outputs['Displacement'], output_node.inputs['Displacement'])
        print(f"Loaded displacement map: {texture_files['displacement']}")
    else:
        print("No displacement map found")
    
    # Metalness map (optional)
    if 'metalness' in texture_files:
        metalness_texture = nodes.new(type='ShaderNodeTexImage')
        metalness_texture.location = (400, -400)
        metalness_texture.image = bpy.data.images.load(texture_files['metalness'])
        metalness_texture.image.colorspace_settings.name = 'Non-Color'
        links.new(mapping_node.outputs['Vector'], metalness_texture.inputs['Vector'])
        links.new(metalness_texture.outputs['Color'], principled_node.inputs['Metallic'])
        print(f"Loaded metalness map: {texture_files['metalness']}")
    else:
        # Wood is not metallic, so default to 0
        principled_node.inputs['Metallic'].default_value = 0.0
        print("No metalness map found, using default value (0.0)")
    
    # Connect Principled BSDF to Material Output
    links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    # Apply material to floor
    if floor.data.materials:
        floor.data.materials[0] = material
    else:
        floor.data.materials.append(material)
    
    # Enable displacement in material settings
    material.displacement_method = 'BOTH'  # Use both bump and displacement
    
    # Add a sun light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.name = "SunLight"
    sun.data.energy = 3
    
    # Set up camera
    bpy.ops.object.camera_add(location=(5, -5, 5))
    camera = bpy.context.active_object
    camera.name = "FloorCamera"
    bpy.context.scene.camera = camera
    
    # Add track-to constraint to camera
    track_to = camera.constraints.new(type='TRACK_TO')
    track_to.target = floor
    track_to.track_axis = 'TRACK_NEGATIVE_Z'
    track_to.up_axis = 'UP_Y'
    
    print("Wood floor scene created with:")
    if 'color' in texture_files:
        print(f"- Color map: {os.path.basename(texture_files['color'])}")
    if 'displacement' in texture_files:
        print(f"- Displacement map: {os.path.basename(texture_files['displacement'])}")
    if 'roughness' in texture_files:
        print(f"- Roughness map: {os.path.basename(texture_files['roughness'])}")
    if 'normal_gl' in texture_files:
        print(f"- GL Normal map: {os.path.basename(texture_files['normal_gl'])}")
    if 'metalness' in texture_files:
        print(f"- Metalness map: {os.path.basename(texture_files['metalness'])}")

def render_scene(output_path):
    """
    Render the scene
    """
    # Set render settings
    scene = bpy.context.scene
    # scene.render.engine = 'BLENDER_EEVEE'

    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError as e:
        print(str(e))
        scene.render.engine = 'BLENDER_EEVEE_NEXT'

    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 50
    scene.render.filepath = output_path
    
    # Enable screen space reflections for better material preview
    # Property names may vary in different Blender versions
    if hasattr(scene.eevee, 'use_ssr'):
        scene.eevee.use_ssr = True
        scene.eevee.use_ssr_refraction = True
    elif hasattr(scene.eevee, 'screen_space_reflections'):
        scene.eevee.screen_space_reflections = True
        scene.eevee.use_ssr_refraction = True
    
    # Render
    print(f"Rendering scene to: {output_path}")
    bpy.ops.render.render(write_still=True)
    print("Rendering completed!")

# Main execution
if __name__ == "__main__":
    # Texture directory
    texture_directory = "/home/robot/blender_assets/texture/WoodFloor043_4K"
    
    # Output path
    output_directory = os.path.expanduser("./blender_renders")
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, "wood_floor_render.png")
    
    # Create scene
    setup_wood_floor(texture_directory)
    
    # Render scene
    render_scene(output_file)
    
    print(f"Wood floor render saved to: {output_file}")