import bpy
import os
import json


class ModifierGenerator:
    """
    Create various modifiers for given a mesh object.
    """
    def __init__(
            self, 
            obj=None,
        ):
        """
        Initializes the modifier object.

        Args:
            obj (object): A mesh object instance that the modifier is used to. 
            modifier_name (str): The name of this modifier.
        """
        self.logger = None
        self.obj = obj
        self.modifier_names = []

        try:
            from logger.logger import Logger
            self.logger = Logger("Modeling").getLogger()

            if self.obj and hasattr(self.obj, 'type') and self.obj.type == 'MESH':
                self.logger.info(f"Create a modifier generator for a mesh object named '{self.obj.name}'.")
            else:
                self.logger.info(f"Create a modifier generator, but need to set a mesh object to it.")
        except Exception as e:
            print("[ERROR] Could not initialize the modifier generator.")

        self.modifier_types = [
            'GREASE_PENCIL_VERTEX_WEIGHT_PROXIMITY', 'DATA_TRANSFER', 'MESH_CACHE', 'MESH_SEQUENCE_CACHE', 
            'NORMAL_EDIT', 'WEIGHTED_NORMAL', 'UV_PROJECT', 'UV_WARP', 'VERTEX_WEIGHT_EDIT', 'VERTEX_WEIGHT_MIX', 
            'VERTEX_WEIGHT_PROXIMITY', 'GREASE_PENCIL_COLOR', 'GREASE_PENCIL_TINT', 'GREASE_PENCIL_OPACITY', 
            'GREASE_PENCIL_VERTEX_WEIGHT_ANGLE', 'GREASE_PENCIL_TIME', 'GREASE_PENCIL_TEXTURE', 'ARRAY', 'BEVEL', 
            'BOOLEAN', 'BUILD', 'DECIMATE', 'EDGE_SPLIT', 'NODES', 'MASK', 'MIRROR', 'MESH_TO_VOLUME', 'MULTIRES', 
            'REMESH', 'SCREW', 'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE', 'VOLUME_TO_MESH', 'WELD', 'WIREFRAME', 
            'GREASE_PENCIL_ARRAY', 'GREASE_PENCIL_BUILD', 'GREASE_PENCIL_LENGTH', 'LINEART', 'GREASE_PENCIL_MIRROR', 
            'GREASE_PENCIL_MULTIPLY', 'GREASE_PENCIL_SIMPLIFY', 'GREASE_PENCIL_SUBDIV', 'GREASE_PENCIL_ENVELOPE', 
            'GREASE_PENCIL_OUTLINE', 'ARMATURE', 'CAST', 'CURVE', 'DISPLACE', 'HOOK', 'LAPLACIANDEFORM', 'LATTICE', 
            'MESH_DEFORM', 'SHRINKWRAP', 'SIMPLE_DEFORM', 'SMOOTH', 'CORRECTIVE_SMOOTH', 'LAPLACIANSMOOTH', 
            'SURFACE_DEFORM', 'WARP', 'WAVE', 'VOLUME_DISPLACE', 'GREASE_PENCIL_HOOK', 'GREASE_PENCIL_NOISE', 
            'GREASE_PENCIL_OFFSET', 'GREASE_PENCIL_SMOOTH', 'GREASE_PENCIL_THICKNESS', 'GREASE_PENCIL_LATTICE', 
            'GREASE_PENCIL_DASH', 'GREASE_PENCIL_ARMATURE', 'GREASE_PENCIL_SHRINKWRAP', 'CLOTH', 'COLLISION', 
            'DYNAMIC_PAINT', 'EXPLODE', 'FLUID', 'OCEAN', 'PARTICLE_INSTANCE', 'PARTICLE_SYSTEM', 'SOFT_BODY', 'SURFACE'
        ]


    def set_object(self, mesh_object):
        # Double-check if the mesh object is ready.
        if not mesh_object or not hasattr(mesh_object, 'type') or mesh_object.type != 'MESH':
            warn_msg = f"set_object(), A valid mesh object must be provided."
            self.logger.warn(warn_msg)
        
        self.obj= mesh_object
        info_msg = f"set_object(), the mesh object name = '{self.obj.name}'."
        self.logger.info(info_msg)


    def add_modifier(
        self,
        modifier_name="",
        modifier_type="displace",
        modifier_attributes={}
    ) -> bpy.types.Modifier:
        """
        Add a modifier to self.obj.

        Args:
            modifier_name (str): The name of the modifier, a mesh object can have multiple modifiers.
            modifier_type (str): The type of the modifier, case insensitive. The valid values refer to 'self.modifier_types'.
            modifier_attributes (dict): A dictionary of this modifier's attribute name and value pairs.

        Returns:
            The object instance of the newly created modifier.
        """
        if not self.obj or self.obj.type != 'MESH':
            warn_msg = f"add_modifier(), The 'self.obj' is None or its type is not 'MESH'."
            self.logger.warn(warn_msg)
            return None
        
        # Check if a modifier with the same name already exists
        for mod in self.obj.modifiers:
            if modifier_name.upper() == mod.name.upper():
                info_msg = f"add_modifier(), A modifier named '{modifier_name}' already exists, " 
                info_msg += f"return the existing modifier."
                self.logger.info(info_msg)
                return mod
        
        # Unify modifier type to Blender-recognized 'DISPLACE'
        if modifier_type.upper() not in self.modifier_types:
            warn_msg = f"add_modifier(), Unsupported modifier type, must be one of: \n"
            modifier_types_str = json.dumps(self.modifier_types, indent=2, ensure_ascii=False)
            warn_msg += f"{modifier_types_str} \n" 
            self.logger.warn(warn_msg)
            return None

        # Create displacement modifier
        new_modifier = self.obj.modifiers.new(
            name=modifier_name,
            type=modifier_type.upper()  # Blender's internal type for displacement modifier
        )
        
        # Apply initial attributes
        if modifier_attributes:
            self.set_modifier_attributes(modifier_name, modifier_attributes)
        
        self.modifier_names.append(modifier_name)
        return new_modifier
    

    def set_modifier_attributes(
        self,
        modifier_name="",
        modifier_attributes={}
    ) -> bool:
        """
        Modify attributes of an existing modifier.

        Args:
            modifier_name (str): The name of this modifier. 
            modifier_attributes (dict): A dictionary of this modifier's attribute name and value pairs.

        Returns:
            A boolean, whether or not the operation was successful.
        """
        if len(modifier_attributes) == 0:
            warn_msg = f"set_modifier_attributes(), No attribute dictionary provided, no operation performed."
            self.logger.warn(warn_msg)
            return False
        
        # Get target modifier
        modifier = self.obj.modifiers.get(modifier_name)
        if not modifier:
            warn_msg = f"set_modifier_attributes(), No modifier named '{modifier_name}' exists in object '{self.obj.name}'."
            self.logger.warn(warn_msg)
            return False
        
        # Apply attributes
        for attr_name, attr_value in modifier_attributes.items():
            if hasattr(modifier, attr_name):
                setattr(modifier, attr_name, attr_value)
            else:
                warn_msg = f"set_modifier_attributes(), Modifier has no attribute '{attr_name}', skipped."
                self.logger.warn(warn_msg)
        
        return True
    

    @staticmethod
    def usage_demo():
        # 1. Create the environment.
        # 
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
        plane = bpy.context.active_object
        plane.name = "DemoPlane"

        # 2. Initialize modifier 
        #
        modifier_gen = ModifierGenerator(obj=plane)
        modifier_gen.set_object(plane)

        # 3. Add subdivision surface modifier 
        # 
        subsurf_attrs = {
            "levels": 3, 
            "render_levels": 4
        }
        subsurf_mod = modifier_gen.add_modifier(
            modifier_name="SubsurfMod",
            modifier_type="SUBSURF",
            modifier_attributes=subsurf_attrs
        )

        # 4. Add noise modifier (to enhance displacement effect)
        # 
        smooth_attrs = {
            "factor": 0.599
        }
        smooth_mod = modifier_gen.add_modifier(
            modifier_name="SmoothMod",
            modifier_type="SMOOTH",
            modifier_attributes=smooth_attrs
        )

        # 5. Add displacement modifier and set initial attributes
        # 
        noise_tex = bpy.data.textures.new(name="Noise_Texture", type='NOISE')
        noise_tex.type = 'NOISE'  # Corrected attribute name
        noise_tex.intensity = 0.599

        displace_attrs = {
            "strength": 2.0,          # Displacement strength
            "mid_level": 0.5,         # Mid-level value
            "texture_coords": 'LOCAL', # Texture coordinate mode
            "texture": noise_tex       # Associate displacement texture
        }
        displace_mod = modifier_gen.add_modifier(
            modifier_name="DisplaceMod",
            modifier_type="DISPLACE",
            modifier_attributes=displace_attrs
        )

        # 6. Modify attributes of the displacement modifier
        #
        update_attrs = {
            "strength": 2.99,          # Increase displacement strength
            "texture_coords": 'GLOBAL' # Change to global coordinates
        }
        modifier_gen.set_modifier_attributes(
            modifier_name="DisplaceMod",
            modifier_attributes=update_attrs
        )

        print(f"[INFO] Mesh object '{modifier_gen.obj.name}' has following modifiers: {modifier_gen.modifier_names}")
        print("[INFO] Modifier creation and configuration completed. \n\n")


if __name__ == "__main__":
    ModifierGenerator.usage_demo()