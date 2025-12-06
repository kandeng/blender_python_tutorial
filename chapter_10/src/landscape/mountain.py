import os
import sys
import bpy
import math
import numpy as np
from pathlib import Path


class Mountain:
    """
    A class to build a mountain covered by snow and two kinds of rocks,
    using ANT-Landscape build-in addon.

    Reference:
    CGBoost course - Master 3D Environment 
    https://www.cgboost.com/courses/master-3d-environments-in-blender
    第 4 章-ANT景观-孤山, 18:50-34:30
    """
    def __init__(
            self,
            mountain_name:str="",
            mountain_type:str="mountain_1"            
        ):
        self.logger = None
        self.ant_landscape_addon = None
        self.mountain = None
        self.material_texture = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Landscape").getLogger()

            # 1. Create mountain mesh object
            from landscape.ant_landscape_addon import ANTLandscapeAddon
            self.ant_landscape_addon = ANTLandscapeAddon()

            mountain_name = mountain_name.strip()
            if len(mountain_name) == 0:
                self.logger.warning(f"Mountain(), mountain_name is emptry.")
                return

            self.mountain = self.ant_landscape_addon.create_landscape(
                landscape_name=mountain_name,
                landscape_preset_type=mountain_type
            )

            # 2. Load soil, snow, rock textures. 
            from modeling.material_texture import MaterialTexture
            self.material_texture = MaterialTexture(
                object_instance=self.mountain,
                material_name=f"{mountain_name}_material"
            )

            self.logger.info(f"Mountain(), mountain '{mountain_name}' is created, of type '{mountain_type}'.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Mountain class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize Mountain class, error message: '{str(e)}'")



    def set_mountain_attributes(
            self, 
            mountain_name:str="",
            mountain_attributes:dict={}
        ):
        self.ant_landscape_addon.set_terrain_attributes(
            terrain_name=mountain_name,
            terrain_attributes=mountain_attributes            
        )



    def _create_mixin_policy_nodes(
            self,
            color_ramp_node_name: str="Color_Ramp_Node", 
            separate_xyz_node_name: str="Separate_XYZ_Node",
            math_node_name: str="Math_Node",
            combine_xyz_node_name: str="Combine_XYZ_Node",
            geometry_node_name: str="Geometry_Node"
        ):
        node_x = 0
        color_ramp_node = self.material_texture.material_editor.create_node(
            node_type='ShaderNodeValToRGB', 
            node_name=color_ramp_node_name, 
            location=(node_x, 0)
        )

        node_x -= 300
        separate_xyz_node = self.material_texture.material_editor.create_node(
            node_type='ShaderNodeSeparateXYZ', 
            node_name=separate_xyz_node_name, 
            location=(node_x, 0)
        )

        node_x -= 300
        math_node = self.material_texture.material_editor.create_node(
            node_type='ShaderNodeMath', 
            node_name=math_node_name, 
            location=(node_x, 0)
        )
        math_node.operation = 'ADD'
        math_node.use_clamp = False

        node_x -= 300
        combine_xyz_node = self.material_texture.material_editor.create_node(
            node_type='ShaderNodeCombineXYZ', 
            node_name=combine_xyz_node_name, 
            location=(node_x, 100)
        )
        geometry_node = self.material_texture.material_editor.create_node(
            node_type='ShaderNodeNewGeometry', 
            node_name=geometry_node_name, 
            location=(node_x, -100)
        )

        self.material_texture.material_editor.create_link(
            from_node_output = separate_xyz_node.outputs[2],         # Z
            to_node_input = color_ramp_node.inputs[0]                # Fac                
        )

        self.material_texture.material_editor.create_link(
            from_node_output = math_node.outputs[0],                 # Value
            to_node_input = separate_xyz_node.inputs[0]              # Vector              
        )

        self.material_texture.material_editor.create_link(
            from_node_output = combine_xyz_node.outputs[0],          # Vector
            to_node_input = math_node.inputs[0]                      # Value              
        )

        self.material_texture.material_editor.create_link(
            from_node_output = geometry_node.outputs[1],             # Normal
            to_node_input = math_node.inputs[1]                      # Value              
        )



    def _create_mixin_group(
            self,
            mixin_policy_name:str=""
        ) -> object:
        # 1. Create the mixin policy nodes.
        mixin_policy_node_names = {
            "color_ramp_node_name": f"{mixin_policy_name}_Color_Ramp_Node", 
            "separate_xyz_node_name": f"{mixin_policy_name}_Separate_XYZ_Node",
            "math_node_name": f"{mixin_policy_name}_Math_Node",
            "combine_xyz_node_name": f"{mixin_policy_name}_Combine_XYZ_Node",
            "geometry_node_name": f"{mixin_policy_name}_Geometry_Node"
        }
        self._create_mixin_policy_nodes(**mixin_policy_node_names)


        # 2. Create the mixin policy node group.
        group_node_names = list(mixin_policy_node_names.values())
        group_node = self.material_texture.material_editor.create_group(
            group_name=f"{mixin_policy_name}_group",
            group_nodes=group_node_names           
        )

        group_input = group_node.node_tree.nodes["Group Input"]
        group_input.location = (-1200, 0)
        group_output = group_node.node_tree.nodes["Group Output"]
        group_output.location = (400, 0)


        # 3. Create the output sockets, and link the internal nodes to it.
        mixin_policy_group_socket_name = f"{mixin_policy_name}_group_socket"
        _ = self.material_texture.material_editor.get_or_create_group_socket(
            group_name=group_node.name,
            socket_name=mixin_policy_group_socket_name,
            in_or_out="OUTPUT",  
            socket_type="NodeSocketColor"
        ) 

        color_ramp_node_name = mixin_policy_node_names["color_ramp_node_name"]
        color_ramp_node = group_node.node_tree.nodes[color_ramp_node_name]
        group_output_node = group_node.node_tree.nodes["Group Output"]

        group_node.node_tree.links.new(
            color_ramp_node.outputs["Color"],
            group_output_node.inputs[mixin_policy_group_socket_name]
        )   

        # 4. Return the group_node
        info_msg = f"create_mixin_group(), create a node group '{group_node.name}'. "
        self.logger.info(info_msg)
        return group_node



    def create_mixin_shaders(
            self,
            soil_texture_group_node:str="",
            rock_texture_group_node:str="",
            snow_texture_group_node:str=""           
        ):
        # 1. Create primary and subsidiary mixin policy node groups.
        primary_mixin_policy_name = "primary_mixin_policy"
        primary_mixin_group = self._create_mixin_group(
            mixin_policy_name=primary_mixin_policy_name
        ) 
        primary_mixin_group.location = (-300, 100)

        subsidiary_mixin_policy_name = "subsidiary_mixin_policy"
        subsidiary_mixin_group = self._create_mixin_group(
            mixin_policy_name=subsidiary_mixin_policy_name
        ) 
        subsidiary_mixin_group.location = (-300, -100)


        # 2. Set the color ramps of the mixin policy node groups.
        primary_color_ramp_node_name = f"{primary_mixin_policy_name}_Color_Ramp_Node"
        primary_color_ramp_node = primary_mixin_group.node_tree.nodes[primary_color_ramp_node_name]
        elements = primary_color_ramp_node.color_ramp.elements
        elements[0].position = 0.4
        elements[0].color = (0.0, 0.0, 0.0, 1.0)
        elements[1].position = 0.5
        elements[1].color = (1.0, 1.0, 1.0, 1.0)

        subsidiary_color_ramp_node_name = f"{subsidiary_mixin_policy_name}_Color_Ramp_Node"
        subsidiary_color_ramp_node = subsidiary_mixin_group.node_tree.nodes[subsidiary_color_ramp_node_name]
        elements = subsidiary_color_ramp_node.color_ramp.elements
        elements[0].position = 0.5
        elements[0].color = (1.0, 1.0, 1.0, 1.0)
        elements[1].position = 0.6
        elements[1].color = (0.0, 0.0, 0.0, 1.0)


        # 3. Set the Combine_XYZ node values
        primary_combine_xyz_node_name = f"{primary_mixin_policy_name}_Combine_XYZ_Node"
        primary_combine_xyz_node = primary_mixin_group.node_tree.nodes[primary_combine_xyz_node_name]
        primary_combine_xyz_node.inputs[0].default_value = 0.4
        primary_combine_xyz_node.inputs[1].default_value = 0.2
        primary_combine_xyz_node.inputs[2].default_value = 0.2

        subsidiary_combine_xyz_node_name = f"{subsidiary_mixin_policy_name}_Combine_XYZ_Node"
        subsidiary_combine_xyz_node = subsidiary_mixin_group.node_tree.nodes[subsidiary_combine_xyz_node_name]
        subsidiary_combine_xyz_node.inputs[0].default_value = -0.1
        subsidiary_combine_xyz_node.inputs[1].default_value = 0.2
        subsidiary_combine_xyz_node.inputs[2].default_value = 0.2


        # 3. Create and link the multiply node
        math_node_name = f"mixin_policy_multiply"
        math_node = self.material_texture.material_editor.create_node(
            node_type='ShaderNodeMath', 
            node_name=math_node_name, 
            location=(0, 0)
        )
        math_node.operation = 'MULTIPLY'
        math_node.use_clamp = False

        primary_mixin_group_socket_name = f"{primary_mixin_policy_name}_group_socket"
        self.material_texture.material_obj.node_tree.links.new(
            primary_mixin_group.outputs[primary_mixin_group_socket_name],
            math_node.inputs[0]
        )  

        subsidiary_mixin_group_socket_name = f"{subsidiary_mixin_policy_name}_group_socket"
        self.material_texture.material_obj.node_tree.links.new(
            subsidiary_mixin_group.outputs[subsidiary_mixin_group_socket_name],
            math_node.inputs[1]
        )  



    def load_textures(
            self,
            soil_texture_dir:str="",
            rock_texture_dir:str="",
            snow_texture_dir:str=""
        ):
        # 1. create a UV map for the rock so textures can be applied correctly.
        bpy.context.view_layer.objects.active = self.mountain
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent()
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        # 2. apply the two textures. 
        soil_texture_group = self.material_texture.load_texture(
            texture_dirpath=soil_texture_dir
        )
        soil_texture_group.location = (0, 600)    # Locate the shader nodes in Blender interface.

        rock_texture_group = self.material_texture.load_texture(
            texture_dirpath=rock_texture_dir
        )
        rock_texture_group.location = (0, 400)    # Locate the shader nodes in Blender interface.      

        snow_texture_group = self.material_texture.load_texture(
            texture_dirpath=snow_texture_dir
        )
        snow_texture_group.location = (0, 200)    # Locate the shader nodes in Blender interface.    

        self.create_mixin_shaders(
            soil_texture_group_node=soil_texture_group,
            rock_texture_group_node=rock_texture_group,
            snow_texture_group_node=snow_texture_group           
        )


    @staticmethod
    def usage_demo():
        # Clean up the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True) 

        # Create the first mountain.
        texture_root = f"/home/robot/blender_asset/texture"
        texture_directories = [
            f"{texture_root}/rocks_ground_05_2k.blend/textures",
            f"{texture_root}/Rock003_2K-JPG/",
            f"{texture_root}/Snow006_4K-JPG"
        ]

        first_mountain = Mountain(
            mountain_name="first_mountain"        
        )
        bpy.context.object.location = (5.0, 5.0, 0.0) 
        first_mountain.set_mountain_attributes(
            mountain_name="first_mountain",
            mountain_attributes={
                "height": 1.234
            }            
        ) 
        first_mountain.load_textures(
            soil_texture_dir=texture_directories[0],
            rock_texture_dir=texture_directories[1],
            snow_texture_dir=texture_directories[2]
        )

        # Create the second mountain.
        second_mountain = Mountain(
            mountain_name="second_mountain",
            mountain_type="mountain_2"            
        )
        bpy.context.object.location = (-5.0, -5.0, 0.0) 
        second_mountain.set_mountain_attributes(
            mountain_name="second_mountain",
            mountain_attributes={
                "random_seed": 16,
                "non_exist": "Nonsense"
            }            
        )

        # Set up the sun. 
        bpy.context.scene.render.engine = 'CYCLES'
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 2.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (15, 10.0, 50.0) 
        bpy.context.collection.objects.link(sun_obj)