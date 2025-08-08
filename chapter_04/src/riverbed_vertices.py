import bpy
import random

def create_pitted_riverbed_iteratively(
    plane_width=10,
    plane_length=20,
    subdivisions=99,
    min_pit_depth=0.5, # Smaller value for each individual dig
    max_pit_depth=1.5,
    pit_radius=1.0    # The radius of each "dig"
):
    """
    Creates a pitted riverbed by applying a proportional editing move to each vertex.

    Args:
        plane_width (int): The width of the plane (X-axis).
        plane_length (int): The length of the plane (Y-axis).
        subdivisions (int): The number of cuts for subdivision.
        min_pit_depth (float): The minimum depth for each pit.
        max_pit_depth (float): The maximum depth for each pit.
        pit_radius (float): The radius for each proportional editing operation.
    """
    # --- 1. Create a rectangular plane ---
    bpy.ops.object.select_all(action='SELECT')
    if bpy.context.active_object:
        bpy.ops.object.delete(use_global=False)

    bpy.ops.mesh.primitive_plane_add(
        size=1,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 0)
    )
    plane = bpy.context.active_object
    plane.name = "PittedRiverbedPlane"
    plane.scale = (plane_width, plane_length, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # --- 2. Subdivide the plane ---
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=subdivisions)
    bpy.ops.object.mode_set(mode='OBJECT')

    # --- 3. Identify riverbed vertices ---
    riverbed_indices = []
    min_y = -plane_length / 4
    max_y = plane_length / 4
    river_widths = []
    for y_coord in range(int(min_y) * 10, int(max_y) * 10 + 1):
        sub_y_coord = y_coord / 10.0
        random_x_left = random.uniform(-1.5, -0.5)
        random_x_right = random.uniform(0.5, 2.0)
        river_widths.append((random_x_left, random_x_right, float(sub_y_coord)))

    for vert in plane.data.vertices:
        closest_point = min(river_widths, key=lambda p: abs(p[2] - vert.co.y))
        riverbed_left = closest_point[0]
        riverbed_right = closest_point[1]
        if riverbed_left < vert.co.x < riverbed_right:
            riverbed_indices.append(vert.index)

    if not riverbed_indices:
        print("No vertices found for the riverbed. Aborting.")
        return

    print(f"\n[INFO] Identified {len(riverbed_indices)} vertices for the riverbed.")
    print(f"[INFO] Starting to dig pits one by one... (This may take a moment)")

    # --- 4. Lower each vertex with its own proportional editing operation ---
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.tool_settings.mesh_select_mode = (True, False, False)

    # Store the active tool settings
    original_falloff = bpy.context.scene.tool_settings.proportional_edit_falloff
    bpy.context.scene.tool_settings.proportional_edit_falloff = 'SMOOTH'

    for i, vert_index in enumerate(riverbed_indices):
        if i % 100 == 0:
            print(f"  Digging pit {i} of {len(riverbed_indices)}...")

        # Select only the current vertex
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        plane.data.vertices[vert_index].select = True
        bpy.ops.object.mode_set(mode='EDIT')

        # Apply a small, random downward translation with proportional editing
        z_depth = random.uniform(min_pit_depth, max_pit_depth)
        z_target = plane.data.vertices[vert_index].co.z - z_depth
        if (z_target < -1.0 * max_pit_depth):
            z_target = max(-1.0 * max_pit_depth, z_target)
        elif ((plane.data.vertices[vert_index].co.z - z_depth) > -1.0 * min_pit_depth):
            z_target = min(-1.0 * min_pit_depth, z_target)

        z_displace = z_target - plane.data.vertices[vert_index].co.z
        bpy.ops.transform.translate(
            value=(0, 0, z_displace),
            orient_type='GLOBAL',
            use_proportional_edit=True, 
            proportional_edit_falloff='SMOOTH',  # Use linear for more uniform effect
            proportional_size=pit_radius,
            release_confirm=True
        )

    # --- 5. Cleanup ---
    bpy.context.scene.tool_settings.proportional_edit_falloff = original_falloff
    bpy.ops.object.mode_set(mode='OBJECT')
    print("Finished digging all pits.")

# --- Main execution ---
if __name__ == "__main__":
    create_pitted_riverbed_iteratively()
    print("\nScript finished: A pitted riverbed has been created.")