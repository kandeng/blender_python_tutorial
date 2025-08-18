import bpy
from typing import Union, Dict, Any

class ModifierGenerator:
    def __init__(self):
        """
        Initialize the modifier generator
        :param target_object: The target object to which modifiers will be added
        """
        self.obj = None

        
    def set_object(self, mesh_object):
        # Double-check if the mesh object is ready.
        if not mesh_object or not hasattr(mesh_object, 'type') or mesh_object.type != 'MESH':
            raise ValueError("A valid mesh object must be provided.")
        
        self.obj= mesh_object
        print(f"[INFO] ApplyTexture initialized for mesh '{self.obj.name}'.")


    def create_modifier(
        self,
        modifier_type: Union["disp", "displace", "displacement"] = "displace",
        modifier_name: str = "My_modifier",
        modifier_attributes: Dict[str, Any] = None
    ) -> bpy.types.Modifier:
        """
        Create a displacement modifier
        :param modifier_type: Modifier type (only displacement-related types supported)
        :param modifier_name: Name of the modifier
        :param modifier_attributes: Initial attribute dictionary
        :return: The created modifier object
        """
        if not self.obj or self.obj.type != 'MESH':
            err_msg = f"[ERROR] The 'self.obj' is None or its type is not 'MESH', "
            err_msg = err_msg + "after then you can use 'create_modifier()'."
            print(err_msg)
            return

        # Unify modifier type to Blender-recognized 'DISPLACE'
        valid_types = {"disp", "displace", "displacement"}
        if modifier_type.lower() not in valid_types:
            raise ValueError(f"Unsupported modifier type, must be one of: {valid_types}")
        
        # Check if a modifier with the same name already exists
        if modifier_name in self.obj.modifiers:
            print(f"[WARN] A modifier named '{modifier_name}' already exists, returning existing modifier")
            return self.obj.modifiers[modifier_name]
        
        # Create displacement modifier
        modifier = self.obj.modifiers.new(
            name=modifier_name,
            type='DISPLACE'  # Blender's internal type for displacement modifier
        )
        
        # Apply initial attributes
        if modifier_attributes:
            self.set_modifier_attributes(modifier_name, modifier_attributes)
        
        return modifier

    def set_modifier_attributes(
        self,
        modifier_name: str = "My_modifier",
        modifier_attributes: Dict[str, Any] = None
    ) -> bool:
        """
        Modify attributes of an existing modifier
        :param modifier_name: Name of the modifier to modify
        :param modifier_attributes: Dictionary of attributes to set
        :return: Whether the operation was successful
        """
        if not modifier_attributes:
            print("No attribute dictionary provided, no operation performed")
            return False
        
        # Get target modifier
        modifier = self.obj.modifiers.get(modifier_name)
        if not modifier:
            raise ValueError(f"No modifier named '{modifier_name}' exists in object '{self.obj.name}'")
        
        # Apply attributes
        for attr_name, attr_value in modifier_attributes.items():
            if hasattr(modifier, attr_name):
                setattr(modifier, attr_name, attr_value)
            else:
                print(f"Warning: Modifier has no attribute '{attr_name}', skipped")
        
        return True


# Usage example
def run_demo():
    # Clear default objects in the scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Create a demonstration plane
    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "Demo_Plane"

    # Add subdivision surface modifier (to enhance displacement effect)
    subsurf = plane.modifiers.new(name="Subdivision", type='SUBSURF')
    subsurf.levels = 3
    subsurf.render_levels = 4

    # Create noise texture (for displacement)
    noise_tex = bpy.data.textures.new(name="Noise_Texture", type='NOISE')
    
    # Fixed: Use 'type' instead of 'noise_type' for Blender 2.8+ compatibility
    noise_tex.type = 'NOISE'  # Corrected attribute name
    noise_tex.intensity = 0.599
    # noise_scale = 5.0          # This should now work correctly

    # Initialize modifier generator
    modifier_gen = ModifierGenerator()
    modifier_gen.set_object(plane)

    # 1. Create displacement modifier and set initial attributes
    initial_attrs = {
        "strength": 2.0,          # Displacement strength
        "mid_level": 0.5,         # Mid-level value
        "texture_coords": 'LOCAL', # Texture coordinate mode
        "texture": noise_tex       # Associate displacement texture
    }
    displace_mod = modifier_gen.create_modifier(
        modifier_type="disp",
        modifier_name="Terrain_Displace",
        modifier_attributes=initial_attrs
    )

    # 2. Later modify attributes of the displacement modifier
    update_attrs = {
        "strength": 2.99,          # Increase displacement strength
        "texture_coords": 'GLOBAL' # Change to global coordinates
    }
    modifier_gen.set_modifier_attributes(
        modifier_name="Terrain_Displace",
        modifier_attributes=update_attrs
    )

    print("Modifier creation and configuration completed")


