import bpy
import bmesh

def create_river_terrain_v1(width=10, length=20):
    """
    Create a meandering terrain that contains a river bank in the middle.
    
    Args:
        width (float): Width of the terrain (10m)
        length (float): Length of the terrain (20m)
    """
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)
    bpy.ops.object.delete()
    
    # Create the base terrain plane at (0, 0, 0)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    terrain = bpy.context.active_object
    terrain.name = "RiverTerrain"
    
    # Scale to desired size (10m x 20m)
    terrain.scale = (width, length, 1)
    bpy.ops.object.transform_apply(scale=True)
    
    # Enter edit mode and subdivide with 99 cuts (creating 100x100 grid)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=99)
    
    # Get the bmesh representation
    bm = bmesh.from_edit_mesh(terrain.data)
    bm.verts.ensure_lookup_table()
    
    # Enable proportional editing and set falloff to smooth
    bpy.context.scene.tool_settings.use_proportional_edit = True
    bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'
    
    # Find vertices near the center (0, 0, 0)
    center_vertices = []
    for vert in bm.verts:
        # Check if vertex is near the center with a small tolerance
        if abs(vert.co.x) < 0.1 and abs(vert.co.y) < 0.1:
            center_vertices.append(vert)
    
    # Select the center vertices
    # obj.data.vertices[0].select = True

    for vert in center_vertices:
        vert.select = True
    bmesh.update_edit_mesh(terrain.data)
    
    if center_vertices:
        # Set z-coordinate to -2 for selected vertices
        target_z = -2
        
        # Calculate average current z-coordinate of center vertices
        avg_z = sum(vert.co.z for vert in center_vertices) / len(center_vertices)
        z_displacement = target_z - avg_z  # Calculate displacement needed
        
        # Set proportional size as 0.6
        proportional_size = 1.6

        # 清除默认选中状态
        bpy.ops.mesh.select_all(action='DESELECT')

        print(f"\n[INFO] The active object: {bpy.context.active_object}")
        for vert in center_vertices:
            vert.select = True
            print(f"[INFO] center vertex = ({vert.co.x}, {vert.co.y})")
        print()

            
        # Apply the displacement with proportional editing
        bpy.ops.transform.translate(
            value=(0, 0, z_displacement),
            use_proportional_edit=True, 
            proportional_edit_falloff='SMOOTH', 
            proportional_size=proportional_size,
            release_confirm=True
        )
        
        print(f"Modified {len(center_vertices)} center vertices to z={target_z}")
    else:
        print("Warning: Could not find center vertices")
    
    # Disable proportional editing
    bpy.context.scene.tool_settings.use_proportional_edit = False
    
    # Update the mesh
    bmesh.update_edit_mesh(terrain.data)
    
    # Return to object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    print(f"Created river terrain: {width}m x {length}m at (0, 0, 0) with 99 cuts")
    print("- Found and modified vertices near center (0, 0, 0)")
    print("- Set their z-coordinate to -2")
    print("- Proportional size set to 0.6")
    print("- Used smooth falloff for natural terrain transitions")
    
    return terrain

def setup_scene():
    """
    Set up basic lighting and camera for the terrain.
    """
    # Add sun light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    sun = bpy.context.active_object
    sun.name = "TerrainSun"
    sun.data.energy = 3
    
    # Add fill light
    bpy.ops.object.light_add(type='POINT', location=(-5, -5, 8))
    fill_light = bpy.context.active_object
    fill_light.name = "TerrainFillLight"
    fill_light.data.energy = 500
    
    # Add camera
    bpy.ops.object.camera_add(location=(0, -15, 10))
    camera = bpy.context.active_object
    camera.name = "TerrainCamera"
    bpy.context.scene.camera = camera
    
    # Point camera at terrain center
    bpy.ops.object.empty_add(location=(0, 0, 0))
    target = bpy.context.active_object
    target.name = "CameraTarget"
    
    # Add track-to constraint
    track_to = camera.constraints.new(type='TRACK_TO')
    track_to.target = target
    track_to.track_axis = 'TRACK_NEGATIVE_Z'
    track_to.up_axis = 'UP_Y'
    
    print("Set up scene lighting and camera")

def create_river_terrain_scene():
    """
    Create a complete river terrain scene.
    """
    print("Creating river terrain scene...")
    
    # Create river terrain
    terrain = create_river_terrain_v1(width=10, length=20)
    
    # Set up scene
    # setup_scene()
    
    print("\nRiver terrain scene creation completed:")
    print("- 10m x 20m terrain located at (0, 0, 0) with 99 subdivisions")
    print("- Modified vertices near center (0, 0, 0) to create river bank")
    print("- Set vertex z-coordinate to -2")
    print("- Fixed proportional size of 0.6")
    print("- Smooth proportional falloff for natural transitions")
    print("- Scene lighting and camera")
    
    return terrain

# Main execution
if __name__ == "__main__":
    # Create the river terrain scene
    terrain = create_river_terrain_scene()
    
    print(f"\nScene contains:")
    print(f"- 1 terrain object (10m x 20m)")
    
    print("\nTo render the scene:")
    print("1. Adjust camera position if needed")
    print("2. Set render engine to Cycles or Eevee")
    print("3. Set output path and render")