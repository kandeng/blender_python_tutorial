import bpy
import os

def create_mountain_with_nature_generator():
    """
    Create a mountain using The_Nature_Generator addon.
    """
    # Enable the addon
    try:
        bpy.ops.preferences.addon_enable(module="The_Nature_Generator")
        print("The_Nature_Generator addon enabled successfully.")
    except Exception as e:
        print(f"Failed to enable The_Nature_Generator addon: {e}")
        return None

    # Try to find and apply a mountain generator node group directly
    node_group = None
    for ng in bpy.data.node_groups:
        if "Mountain" in ng.name and "Generator" in ng.name:
            node_group = ng
            break
    
    # If no mountain generator found, try any NG_T_ group
    if not node_group:
        for ng in bpy.data.node_groups:
            if ng.name.startswith("NG_T_"):
                node_group = ng
                break

    if node_group:
        # Create a new mesh object to work with
        bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        obj = bpy.context.active_object
        obj.name = "Nature_Mountain"
        
        # Add the geometry nodes modifier
        modifier = obj.modifiers.new(name="Nature_Generator_Mountain", type='NODES')
        modifier.node_group = node_group
        
        # Apply the modifier to generate the mountain
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        print(f"Applied '{node_group.name}' modifier to create mountain.")
        return obj
    else:
        print("No suitable node group found in The_Nature_Generator addon.")
        return None

def import_mountain_asset():
    """
    Import a mountain asset from The_Nature_Generator's asset library.
    """
    try:
        # Get the addon path correctly
        import sys
        addon_module = sys.modules.get("The_Nature_Generator")
        if not addon_module:
            print("Addon module not found in sys.modules")
            return None
            
        addon_path = os.path.dirname(addon_module.__file__)
        asset_lib_path = os.path.join(addon_path, "asset_library", "Nature_Generator_Assets.blend")
        
        print(f"Looking for asset library at: {asset_lib_path}")
        
        if os.path.exists(asset_lib_path):
            # Find mountain generator assets
            with bpy.data.libraries.load(asset_lib_path) as (data_from, data_to):
                mountain_objects = [name for name in data_from.objects 
                                  if "mountain" in name.lower() and "generator" in name.lower()]
                terrain_objects = [name for name in data_from.objects 
                                 if "terrain" in name.lower() and "generator" in name.lower()]
                
                # Prioritize mountains over generic terrains
                available_objects = mountain_objects if mountain_objects else terrain_objects
                
            if available_objects:
                print(f"Found terrain/mountain objects: {available_objects}")
                
                # Import the first mountain-like object found
                with bpy.data.libraries.load(asset_lib_path, link=False) as (data_from, data_to):
                    data_to.objects = [available_objects[0]]
                    
                # Link to scene
                if data_to.objects:
                    imported_obj = data_to.objects[0]
                    if imported_obj:
                        bpy.context.collection.objects.link(imported_obj)
                        imported_obj.location = (0, 0, 0)
                        
                        # If it's a generator, we might need to apply it
                        # Check if it has geometry nodes modifiers
                        for mod in imported_obj.modifiers:
                            if mod.type == 'NODES' and mod.node_group:
                                print(f"Applying geometry nodes modifier: {mod.name}")
                                bpy.context.view_layer.objects.active = imported_obj
                                bpy.ops.object.modifier_apply(modifier=mod.name)
                                
                        print(f"Imported and applied mountain asset: {imported_obj.name}")
                        return imported_obj
            else:
                print("No mountain/terrain assets found in the library.")
                return None
        else:
            print("Asset library file not found.")
            return None
    except Exception as e:
        print(f"Error importing mountain asset: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_terrain_from_modifier():
    """
    Create terrain by adding a modifier to a plane.
    """
    try:
        # Create a plane
        bpy.ops.mesh.primitive_plane_add(size=10, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        obj = bpy.context.active_object
        obj.name = "Generated_Mountain"
        
        # Try to find a terrain/mountain node group
        node_group = None
        for ng in bpy.data.node_groups:
            if "Mountain" in ng.name and "Generator" in ng.name:
                node_group = ng
                break
        
        if not node_group:
            for ng in bpy.data.node_groups:
                if ng.name.startswith("NG_T_"):
                    node_group = ng
                    break
                    
        if node_group:
            # Add geometry nodes modifier
            modifier = obj.modifiers.new(name="Terrain_Generator", type='NODES')
            modifier.node_group = node_group
            
            # Subdivide the plane for better terrain resolution
            bpy.ops.object.modifier_add(type='SUBSURF')
            obj.modifiers["Subdivision"].levels = 4
            obj.modifiers["Subdivision"].render_levels = 5
            
            # Apply modifiers
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier="Subdivision")
            bpy.ops.object.modifier_apply(modifier="Terrain_Generator")
            
            print(f"Created terrain with {node_group.name}")
            return obj
        else:
            print("No terrain generator node groups found")
            return None
    except Exception as e:
        print(f"Error creating terrain from modifier: {e}")
        return None

if __name__ == "__main__":
    # Try different approaches in order of preference
    mountain_obj = None
    
    # Approach 1: Try to directly use node groups
    if not mountain_obj:
        print("Trying to create mountain with node groups...")
        mountain_obj = create_mountain_with_nature_generator()
    
    # Approach 2: Try to import and apply an asset
    if not mountain_obj:
        print("Trying to import mountain asset...")
        mountain_obj = import_mountain_asset()
        
    # Approach 3: Create a plane and add terrain modifier
    if not mountain_obj:
        print("Trying to create terrain from modifier...")
        mountain_obj = create_terrain_from_modifier()
        
    if mountain_obj:
        print("Mountain created successfully!")
    else:
        print("Failed to create mountain with The_Nature_Generator.")