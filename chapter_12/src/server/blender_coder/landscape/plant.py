import os
import sys
import bpy
import math
import numpy as np


class SinglePlant:
    """
    A class to generate plant, including grass, tree, shrub, etc.
    """
    def __init__(
            self, 
            plant_name: str=""
        ):
        """
        Initializes the geometry node for a single plant.

        Args:
            plant_name (str): The name of the plant.
        """
        self.logger = None
        self.editor_node = None
        self.plant_name = plant_name.strip()
        
        try:
            from logger.logger import Logger
            self.logger = Logger("Landscape").getLogger()
            self.logger.info(f"SinglePlant class initialized.")

            from modeling.editor_node import EditorNode
            self.editor_node = EditorNode(
                editor_name=f"{self.plant_name}_Geometry", 
                editor_type="GEOMETRY", 
                obj=None
            )

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize SinglePlant class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize SinglePlant class, error message: '{str(e)}'")


    def create_geometry_group(self):  
        """
        Create geometry group so as to grow the plants.
        """
        group_input_node = self.editor_node.get_node("Group Input")
        if group_input_node is None:
            group_input_node = self.editor_node.create_node(
                node_type='NodeGroupInput', 
                node_name="SinglePlantGroupInput",
                location=(-900, 0)
            )   
        else:
            group_input_node.name = "SinglePlantGroupInput"
            group_input_node.location = (-900, 0)

        self.editor_node.node_tree.interface.new_socket(
            name="Geometry",
            in_out='INPUT',  # Input socket (for Group Input)
            socket_type='NodeSocketGeometry'  # Type: Geometry (mesh, curve, etc.)
        )
    
    
        group_output_node = self.editor_node.get_node("Group Output")
        if group_output_node is None:
            group_output_node = self.editor_node.create_node(
                node_type='NodeGroupOutput', 
                node_name="SinglePlantGroupOutput",
                location=(900, 0)
            )   
        else:
            group_output_node.name = "SinglePlantGroupOutput"
            group_output_node.location = (900, 0)

        self.editor_node.node_tree.interface.new_socket(
            name="Geometry",
            in_out='OUTPUT',  # Output socket (for Group Output)
            socket_type='NodeSocketGeometry'
        )
             

        on_point_node = self.editor_node.create_node(
            node_type='GeometryNodeInstanceOnPoints', 
            node_name="SinglePlantOnPoints",
            location=(600, -300)
        )     
        on_point_node.inputs[3].default_value = True

        distribute_on_face_node = self.editor_node.create_node(
            node_type='GeometryNodeDistributePointsOnFaces', 
            node_name="SinglePlantDistributePointsOnFaces",
            location=(-600, -300)
        )  
        distribute_on_face_node.distribute_method = 'POISSON'


        rotation_node = self.editor_node.create_node(
            node_type='FunctionNodeRotateRotation', 
            node_name="SinglePlantRotateRotation",
            location=(-300, -600)
        )  

        random_value_node = self.editor_node.create_node(
            node_type='FunctionNodeRandomValue', 
            node_name="SinglePlantRandomValue",
            location=(-600, -900)
        )  
        random_value_node.data_type = 'FLOAT_VECTOR'
        random_value_node.inputs[1].default_value[0] = 0.1
        random_value_node.inputs[1].default_value[1] = 0.1
        random_value_node.inputs[1].default_value[2] = 1.0


        tex_noise_node = self.editor_node.create_node(
            node_type='ShaderNodeTexNoise', 
            node_name="SinglePlantTexNoise",
            location=(-300, -900)
        )  
        tex_noise_node.inputs[2].default_value = 6.0

        color_ramp_node = self.editor_node.create_node(
            node_type='ShaderNodeValToRGB', 
            node_name="SinglePlantColorRamp",
            location=(0, -900)
        )  

        math_multiple_node = self.editor_node.create_node(
            node_type='ShaderNodeMath', 
            node_name="SinglePlantMultiple",
            location=(300, -900)
        )  
        math_multiple_node.operation = 'MULTIPLY'
        math_multiple_node.inputs[1].default_value = 1.0

        collection_node = self.editor_node.create_node(
            node_type='GeometryNodeCollectionInfo', 
            node_name="SinglePlantCollection",
            location=(0, -600)
        )  
        # Check if the collection exists, create it if it doesn't
        if self.plant_name not in bpy.data.collections:
            bpy.data.collections.new(self.plant_name)
        collection_node.inputs[0].default_value = bpy.data.collections[self.plant_name]
        collection_node.inputs[1].default_value = True
        collection_node.inputs[2].default_value = True


        # Connect the input geometry to the distribute points node
        self.editor_node.create_link(
            from_node_output=group_input_node.outputs['Geometry'], 
            to_node_input=distribute_on_face_node.inputs[0]
        )
        
        # Connect distribute points to instance on points
        self.editor_node.create_link(
            from_node_output=distribute_on_face_node.outputs[0], 
            to_node_input=on_point_node.inputs[0]
        )
        
        # Connect instance on points to output
        self.editor_node.create_link(
            from_node_output=on_point_node.outputs[0], 
            to_node_input=group_output_node.inputs['Geometry']
        )

        # Connect rotation nodes
        self.editor_node.create_link(
            from_node_output=distribute_on_face_node.outputs[2], 
            to_node_input=rotation_node.inputs[0]
        )        
        self.editor_node.create_link(
            from_node_output=random_value_node.outputs[0], 
            to_node_input=rotation_node.inputs[1]
        )      
        self.editor_node.create_link(
            from_node_output=rotation_node.outputs[0], 
            to_node_input=on_point_node.inputs[5]
        )      

        # Connect scale nodes
        self.editor_node.create_link(
            from_node_output=tex_noise_node.outputs[0], 
            to_node_input=color_ramp_node.inputs[0]
        )  
        self.editor_node.create_link(
            from_node_output=color_ramp_node.outputs[0], 
            to_node_input=math_multiple_node.inputs[0]
        )  
        self.editor_node.create_link(
            from_node_output=math_multiple_node.outputs[0], 
            to_node_input=on_point_node.inputs[6]
        )      
        
        # Connect collection to instance on points
        self.editor_node.create_link(
            from_node_output=collection_node.outputs[0], 
            to_node_input=on_point_node.inputs[2]
        )    




class PlantGroup:
    """
    A class to generate a group of plants, including grass, tree, shrub, etc.
    """
    def __init__(
            self, 
            terrain_obj=None
        ):
        """
        Initializes the geometry node for plants.

        Args:
            terrain_obj (object): A mountain or terrain instance where the plants grow.
        """
        self.logger = None
        self.editor_node = None
        self.terrain_obj = terrain_obj
        
        try:
            from logger.logger import Logger
            self.logger = Logger("Landscape").getLogger()
            self.logger.info(f"PlantGroup class initialized.")

            from modeling.editor_node import EditorNode
            self.editor_node = EditorNode(
                editor_name="PlantGroupGeometry", 
                editor_type="GEOMETRY", 
                obj=self.terrain_obj
            )

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize PlantGroup class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize PlantGroup class, error message: '{str(e)}'")



    def create_plant_group(
            self,
            plant_list: list=[]
        ):  
        """
        Create the super geometry group to contain multiple single plant's geometry groups.

        Args:
            plant_list (list): A list of single plant's SinglePlant objects.
        """
        group_input_node = self.editor_node.get_node("Group Input")
        if group_input_node is None:
            group_input_node = self.editor_node.create_node(
                node_type='NodeGroupInput', 
                node_name="PlantGroupInput",
                location=(-300, 0)
            )   
        else:
            group_input_node.name = "PlantGroupInput"
            group_input_node.location = (-300, 0)

        self.editor_node.node_tree.interface.new_socket(
            name="Geometry",
            in_out='INPUT',  # Input socket (for Group Input)
            socket_type='NodeSocketGeometry'  # Type: Geometry (mesh, curve, etc.)
        )

        join_geometry_node = self.editor_node.create_node(
            node_type='GeometryNodeJoinGeometry', 
            node_name="PlantJoinGeometry",
            location=(300, 0)
        )     
    
        group_output_node = self.editor_node.get_node("Group Output")
        if group_output_node is None:
            group_output_node = self.editor_node.create_node(
                node_type='NodeGroupOutput', 
                node_name="PlantGroupOutput",
                location=(600, 0)
            )   
        else:
            group_output_node.name = "PlantGroupOutput"
            group_output_node.location = (600, 0)

        self.editor_node.node_tree.interface.new_socket(
            name="Geometry",
            in_out='OUTPUT',  # Output socket (for Group Output)
            socket_type='NodeSocketGeometry'
        )


        self.editor_node.create_link(
            from_node_output=group_input_node.outputs['Geometry'], 
            to_node_input=join_geometry_node.inputs['Geometry']
        )
        self.editor_node.create_link(
            from_node_output=join_geometry_node.outputs['Geometry'], 
            to_node_input=group_output_node.inputs['Geometry']
        )

        
        for idx, single_plant in enumerate(plant_list):
            subgroup_name = f"{single_plant.plant_name}_subgroup"
            subgroup_node = self.editor_node.create_node(
                node_type='GeometryNodeGroup', 
                node_name=subgroup_name,
                location=(0, -300 * (idx + 1))
            )  
            subgroup_node.node_tree = single_plant.editor_node.node_tree

            # Create a new geometry input for this subgroup
            self.editor_node.create_link(
                from_node_output=group_input_node.outputs['Geometry'], 
                to_node_input=subgroup_node.inputs['Geometry']
            )
            self.editor_node.create_link(
                from_node_output=subgroup_node.outputs['Geometry'], 
                to_node_input=join_geometry_node.inputs['Geometry']
            )



    def set_geometry_to_terrain(self):
        if self.terrain_obj is None:
            warn_msg = f"set_geometry_to_terrain(), 'terrain_obj' is None."
            self.logger.warning(warn_msg)
            return
        
        # Clean up the object's modifier
        for idx, modifier in enumerate(self.terrain_obj.modifiers):
            if 'geometry' in modifier.name.lower():
                self.terrain_obj.modifiers.remove(self.terrain_obj.modifiers[modifier.name])
                debug_msg = f"set_geometry_to_terrain(), '{modifier.name}' is removed from '{self.terrain_obj.name}'"
                self.logger.debug(debug_msg)

        # Add the geometry group modifier to the terrain_obj
        geonodes_mod = self.terrain_obj.modifiers.new(name="PlantGeometryGroup", type='NODES')
        geonodes_mod.node_group = self.editor_node.node_tree
        
        # Make sure the modifier is enabled for viewport and render
        geonodes_mod.show_viewport = True
        geonodes_mod.show_render = True



    def control_panel(
            self, 
            plant_name: str="",
            density: float=0.0,
            size: float=0.0,
            noise_range: tuple=(0.0, 0.0)
        ):
        node_tree = None
        try:
            node_tree = self.terrain_obj.modifiers["PlantGeometryGroup"].node_group.nodes
        except Exception as e:
            warn_msg = f"control_panel(), terrain_obj doesn't have the geometry modifier 'PlantGeometryGroup'."
            self.logger.warning(warn_msg)
            return 
        
        for idx, node in enumerate(node_tree):
            debug_msg = f"control_panel(), node[{idx}].name == '{node.name}', node[{idx}].type == '{node.type}'."
            # self.logger.debug(debug_msg)

            if (node.type == 'GROUP') and (plant_name.lower() in node.name.lower()):
                sub_node_tree = node.node_tree.nodes
                for sub_idx, sub_node in enumerate(sub_node_tree):
                    debug_msg = f"control_panel(), subnode[{sub_idx}].name == '{sub_node.name}', node[{sub_idx}].type == '{sub_node.type}'."
                    # self.logger.debug(debug_msg)

                    if (sub_node.type == 'DISTRIBUTE_POINTS_ON_FACES') and (density > 0.0):
                        sub_node.inputs[5].default_value = density

                    if (sub_node.type == 'MATH') and (size > 0.0):
                        sub_node.inputs[1].default_value = size

                    if (sub_node.type == 'VALTORGB') and ((noise_range[0] > 0.0) or (noise_range[1] > 0.0)):
                        sub_node.color_ramp.elements[0].position = noise_range[0]
                        sub_node.color_ramp.elements[1].position = noise_range[1]

                


    @staticmethod
    def usage_demo():
        bpy.ops.object.select_all(action='DESELECT')
        plane_obj = bpy.data.objects.get("PlantPlane")
        if plane_obj:
            bpy.data.objects.remove(plane_obj, do_unlink=True)

        # bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(0, 0, 0))
        bpy.context.object.scale = (6, 6, 1)
        bpy.context.object.name = "PlantPlane"
        active_obj = bpy.context.object

        from landscape.plant import SinglePlant
        chamfered = SinglePlant(plant_name="ND.Chamfered")
        chamfered.create_geometry_group()
        bolt = SinglePlant(plant_name="ND.Bolted")
        bolt.create_geometry_group()
    

        plant_group = PlantGroup(terrain_obj=active_obj)        
        plant_group.create_plant_group(
            plant_list=[chamfered, bolt]
        )
        plant_group.set_geometry_to_terrain()

        plant_group.control_panel(
            plant_name="ND.Chamfered",
            density=0.9,
            size=0.3,
            noise_range=(0.2, 0.6)
        )

        plant_group.control_panel(
            plant_name="ND.Bolted",
            density=9.9,
            size=0.2,
            noise_range=(0.3, 0.7)
        )