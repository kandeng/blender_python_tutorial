import bpy
from math import radians
import os
import sys
import json


class Rock:
    """
    A class to create and manipulate individual rock objects using Blender's
    built-in rock generator addon.

    Reference:
    Rocky River Realistic Nature Animation - Part 1 (Blender Tutorial)
    https://www.youtube.com/watch?v=vWFN5srwBy0
    19:36 Adding Some Rocks
    """

    def __init__(
            self,
            rock_name:str="",
            scale:tuple=(1.0, 1.0, 1.0), 
            skew:tuple=(0.0, 0.0, 0.0)
        ):
        """
        Initializes the RockGenerator and ensures the necessary addon is enabled.
        """
        self.logger = None
        self.rock_object = None
        self.material_texture = None
        # self._enable_extra_objects_addon()

        try:
            from logger.logger import Logger
            self.logger = Logger("Modeling").getLogger()
            self._create_rock(
                rock_name=rock_name
            )

            from modeling.material_texture import MaterialTexture
            self.material_texture = MaterialTexture(
                object_instance=self.rock_object,
                material_name=f"{rock_name}_material"
            )

        except ImportError:
            print("[ERROR] Could not import TextureShader class. ")



    # Looks like the add-on's name, "add_mesh_extra_objects", is not right.
    # We have tried the following module names, all failed, including, 
    # "extra_mesh_objects", "add_mesh_extra_objects" "add_extra_mesh_objects", "add_mesh_rock", 
    # "extra_mesh_objects.add_mesh_rocks", "extra_mesh_objects/add_mesh_rocks", "VIEW3D_MT_mesh_extras_add"
    def _enable_extra_objects_addon(self):
        # A private helper to ensure the 'Add Mesh: Extra Objects' addon is enabled. 
        try:
            bpy.ops.preferences.addon_enable(module="add_mesh_rock")
            print("[INFO] 'Add Mesh: Extra Objects' addon is enabled.")
        except Exception as e:
            print(f"[ERROR] Could not enable the required addon: {e}")
            print("[ERROR] The rock generator will not function.")    


    def _create_rock(
            self, 
            rock_name:str="",
            scale:tuple=(1.0, 1.0, 1.0), 
            skew:tuple=(0.0, 0.0, 0.0)
        ):
        """
        Creates a new rock at the origin with a specific initial scale.
        The new rock becomes the active rock for other methods.

        Args:
            scale (tuple): The initial scale of the rock on the (X, Y, Z) axes.
            skew (tuple): The skewing factor along the (X, Y, Z) axes, with value range (0.0, 1.0).
        """
        try:
            """
            # Try to use the rock generator if available
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.normals_make_consistent()
            bpy.ops.object.editmode_toggle()            
            """
            
            bpy.ops.mesh.add_mesh_rock(
                scale_fac=scale,
                skew_X=skew[0], 
                skew_Y=skew[1], 
                skew_Z=skew[2]
            )

            self.rock_object = bpy.context.active_object
            self.rock_object.name = rock_name
            self.logger.info(f"_create_rock(), created rock: {self.rock_object.name}")

        except RuntimeError as e:
            self.logger.warning(f"_create_rock(), failed to create rock. Error message: '{str(e)}'")
            self.rock_object = None



    def _mix_shader_groups(
            self,
            primary_texture_group_node:object=None,
            subsidiary_texture_group_node:object=None               
        ):
        # 0. Get the material's output node.
        material_editor = self.material_texture.material_editor
        output_node = self.material_texture.material_editor.get_node_or_group(
            node_name="Material Output"
        )
        if output_node is None:
            warn_msg = f"load_texture(), the activate material '{self.material_obj.name}' doesn't have 'Output_Node'."
            self.logger.warning(warn_msg)
            return 
        output_node.location = (900, 0)

        # 1. Create and link the mix shader node.
        mix_shader_node_name = "mix_Principled_BSDFs"
        mix_shader = material_editor.create_node(
            node_type='ShaderNodeMixShader', 
            node_name=mix_shader_node_name, 
            location=(600, 0)
        )

        material_editor.create_link(
            from_node_output=mix_shader.outputs["Shader"], 
            to_node_input=output_node.inputs["Surface"]
        )

        material_editor.create_link(
            from_node_output=primary_texture_group_node.outputs["principled_bsdf_socket"],
            to_node_input=mix_shader.inputs[1],
        ) 
        material_editor.create_link(
            from_node_output=subsidiary_texture_group_node.outputs["principled_bsdf_socket"],
            to_node_input=mix_shader.inputs[2],
        ) 


        # 2. Create and link the vector mix node
        mix_displacement_node_name = "mix_Displacements"
        mix_displacement = material_editor.create_node(
            node_type='ShaderNodeMix', 
            node_name=mix_displacement_node_name, 
            location=(600, 300)
        )

        material_editor.create_link(
            from_node_output=mix_displacement.outputs["Result"], 
            to_node_input=output_node.inputs["Displacement"]
        )

        material_editor.create_link(
            from_node_output=primary_texture_group_node.outputs["displace_map_socket"],
            to_node_input=mix_displacement.inputs["A"],
        ) 
        material_editor.create_link(
            from_node_output=subsidiary_texture_group_node.outputs["displace_map_socket"],
            to_node_input=mix_displacement.inputs["B"],
        ) 


        # 3. Create and link the color ramp node
        color_ramp_node_name = "Color_Ramp_Node"
        color_ramp_node = material_editor.create_node(
            node_type='ShaderNodeValToRGB', 
            node_name=color_ramp_node_name, 
            location=(200, 0)
        ) 
        # color_ramp_node.inputs[0].default_value = 0.5      # Fac

        # Set the first color to black
        elements = color_ramp_node.color_ramp.elements
        elements[0].position = 0.5
        elements[0].color = (0.0, 0.0, 0.0, 1.0)
        
        # Set the second color to blue
        elements[1].position = 0.75
        elements[1].color = (1.0, 1.0, 1.0, 1.0)

        material_editor.create_link(
            from_node_output=color_ramp_node.outputs[0],      # Color
            to_node_input=mix_shader.inputs[0]             # Fac
        )     


        # 4. Create and link the noise texture node. 
        noise_texture_node_name = "Noise_Texture_Node"
        noise_texture_node = material_editor.create_node(
            node_type='ShaderNodeTexNoise', 
            node_name=noise_texture_node_name, 
            location=(0, 0)
        )  
        noise_texture_node.inputs[2].default_value = 2.0      # Scale
        noise_texture_node.inputs[3].default_value = 15.0     # Detail
        noise_texture_node.inputs[4].default_value = 0.8      # Roughness
        noise_texture_node.inputs[5].default_value = 0.1      # Lacuna
        noise_texture_node.inputs[8].default_value = 0.1      # Distortion

        material_editor.create_link(
            from_node_output=noise_texture_node.outputs[0],     # Fac
            to_node_input=color_ramp_node.inputs[0]          # Fac
        )    


        # 5. Create and link the texture mapping node
        noise_mapping_node_name = "Noise_Mapping"
        noise_mapping_node = material_editor.create_node(
            node_type='ShaderNodeMapping', 
            node_name=noise_mapping_node_name, 
            location=(-200, 0)
        )

        material_editor.create_link(
            from_node_output=noise_mapping_node.outputs[0],      # Vector 
            to_node_input=noise_texture_node.inputs[0]        # Vector
        )


        # 6. Create and link the noise texture coordinate node.
        noise_tex_coord_node_name = "Noise_Texture_Coordinate"
        noise_tex_coord_node = material_editor.create_node(
            node_type='ShaderNodeTexCoord', 
            node_name=noise_tex_coord_node_name, 
            location=(-400, 0)
        )

        material_editor.create_link(
            from_node_output=noise_tex_coord_node.outputs[3],    # Object 
            to_node_input=noise_mapping_node.inputs[0]        # Vector
        )


    def load_textures(
            self,
            primary_texture_dir:str="",
            subsidiary_texture_dir:str=""
        ):
        # 1. create a UV map for the rock so textures can be applied correctly.
        bpy.context.view_layer.objects.active = self.rock_object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.object.shade_smooth()
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 2. apply the two textures. 
        primary_texture_group = self.material_texture.load_texture(
            texture_dirpath=primary_texture_dir
        )
        primary_texture_group.location = (200, 400)    # Locate the shader nodes in Blender interface.

        subsidiary_texture_group = self.material_texture.load_texture(
            texture_dirpath=subsidiary_texture_dir
        )
        subsidiary_texture_group.location = (200, 200)    # Locate the shader nodes in Blender interface.       

        self._mix_shader_groups(
            primary_texture_group_node=primary_texture_group,
            subsidiary_texture_group_node=subsidiary_texture_group           
        )


    def scale_rock(
            self, 
            scale_fac:float=1.0
        ):
        if not self.rock_object:
            self.logger.warning(f"scale_rock(), No rock object to scale. Please use create_rock() first.")
            return
        
        self.rock_object.scale = (scale_fac, scale_fac, scale_fac)
        self.logger.info(f"scale_rock(), Scaling {self.rock_object.name} by {scale_fac}. ")


    def move_rock(
            self, 
            location:tuple=(0, 0, 0)
        ):
        if not self.rock_object:
            self.logger.warning(f"move_rock(), No rock object to move. Please use create_rock() first.")
            return

        self.rock_object.location = location
        self.logger.info(f"move_rock(), Moving {self.rock_object.name} to {location}.")


    def rotate_rock(
            self, 
            angle:tuple=(0, 0, 0)
        ):
        """
        angle is a tuple in degree, we will convert it to radians internally. 
        """
        if not self.rock_object:
            self.logger.warning(f"rotate_rock(), No rock object to move. Please use create_rock() first.")
            return

        angle_radius = [radians(ang) for ang in angle]
        self.rock_object.rotation_euler = angle_radius
        self.logger.info(f"rotate_rock(), Rotating {self.rock_object.name} by {angle} degree.")



    # --- Execution example ---
    @staticmethod
    def usage_demo():

        # 1. Start with a clean scene for a demo.
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        # bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))


        # 2. Set up the sun. 
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 3.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (0.0, 0.0, 5.0) 
        bpy.context.collection.objects.link(sun_obj)


        # 3. Create the first rock and apply textures.
        texture_directories = [
            "/home/robot/movie_blender_studio/asset/texture/Rock003_2K-JPG/",
            "/home/robot/movie_blender_studio/asset/texture/Moss002_2K-JPG"
        ]

        first_rock = Rock(
            rock_name="first_rock",
            scale=(10.0, 8.5, 5.8), 
            skew=(0.0, 1.0, 0.0)            
        )

        first_rock.move_rock(location=(2, -3, 0))
        first_rock.rotate_rock(angle=(30.0, 0.0, 45.0))

        first_rock.load_textures(
            primary_texture_dir=texture_directories[0],
            subsidiary_texture_dir=texture_directories[1]
        )


        # 4. Create the second rock and apply textures.
        second_rock = Rock(
            rock_name="second_rock",
            scale=(3.5, 4.0, 2.2), 
            skew=(1.0, 1.0, 1.0)               
        )

        second_rock.scale_rock(scale_fac=2.2)
        second_rock.move_rock(location=(-4, 1, 0))
        second_rock.rotate_rock(angle=(0.0, 15.0, -25.0))

        second_rock.load_textures(
            primary_texture_dir=texture_directories[0],
            subsidiary_texture_dir=texture_directories[1]
        )


        # 5. Print out all the object in viewport
        #    Get the collection of all visible objects in the current context
        visible_objects = bpy.context.visible_objects

        # Check if there are any visible objects
        if visible_objects:
            print("\n--- Visible Objects in Viewport ---")
            # Iterate through the collection and print each object's name
            for obj in visible_objects:
                print(obj.name)
        else:
            print("No visible objects found in the viewport.")
        print("\n[SUCCESS] Rock.usage_demo() finished.")



if __name__ == "__main__":
    Rock.usage_demo()