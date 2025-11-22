import bpy
import json

class EditorNode:
    """
    A class for the creation, linking and property setting of material/shader, compositing, geometry nodes.
    
    1. material/shader for object
        material = bpy.data.materials.new(name="Object_Material")
        principled_node = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')

    2. material/shader for world
        world = bpy.context.scene.world
        background_node = world.node_tree.nodes.new(type='ShaderNodeBackground')

    3. compositing 
        scene = bpy.context.scene
        render_layers_node = scene.node_tree.nodes.new(type='CompositorNodeRLayers')

    4. geometry
        geo_node_tree = bpy.data.node_groups.new(name="My_Geometry_Nodes", type='GeometryNodeTree')
        input_node = geo_node_tree.nodes.new(type='NodeGroupInput')
    """

    def __init__(
            self, 
            editor_name="",
            editor_type="",
            obj=None
        ):
        """
        Configures the output path, file format, and codec.

        Args:
            editor_name (str): The name of this editor. 
                The name will display in the logs, for debugging convenience.
            editor_type (str): The type of this editor. 
                The valid values are ('MATERIAL', 'WORLD', 'COMPOSITING', 'GEOMETRY').
            obj (object): An object instance that the materials and geometry are applied to. 
                It is not useful for 'WORLD' and 'COMPOSITING' types.
        """
        if editor_name is None: 
            editor_name = ""
        self.editor_name = editor_name.strip()

        if editor_type is None: 
            editor_type = ""
        self.editor_type = editor_type.strip()

        self.obj = obj         # Not useful for 'WORLD' and 'COMPOSITING' type.
        self.node_tree = None

        self.logger = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Modeling").getLogger()

            # Create the node_tree from scratch
            self.reset()

            info_msg = f"EditorNode class initialized, "
            info_msg += f"name='{self.editor_name}', type='{self.editor_type}'."
            self.logger.info(info_msg)

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize EditorNode class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize EditorNode class, error message: '{str(e)}'")


    def _create_node_tree(self):    
        if self.editor_type.upper() == "MATERIAL":
            if self.obj is None:
                warn_msg = f"_create_node_tree(), self.obj is None."
                self.logger.debug(warn_msg)
                return 

            material_name = f"{self.editor_name}_material"
            material_obj = None
            """
            if self.obj.data.materials:
                # Use the first material slot's material
                material_obj = self.obj.data.materials[0]
                self.obj.data.materials.clear()            
            """

            # Create a new default material if none exists
            material_obj = bpy.data.materials.new(name=material_name)
            material_obj.use_nodes = True
            self.obj.data.materials.append(material_obj)            

            # self.logger.debug(f"_create_node_tree(), material_obj='{material_obj.name}'")
            self.node_tree = material_obj.node_tree

        elif self.editor_type.upper() == "WORLD":
            # Get or create the active world
            world = bpy.context.scene.world
            world_name = f"{self.editor_name}_world"
            if world is None:
                world = bpy.data.worlds.new(name=world_name)
                bpy.context.scene.world = world

            # Enable nodes for the world (required to use a shader graph)
            world.use_nodes = True

            # Clear existing nodes (optional but useful for a clean setup)
            self.node_tree = world.node_tree
            self.node_tree.nodes.clear()

        elif self.editor_type.upper() == "COMPOSITING":
            scene = bpy.context.scene
            scene.use_nodes = True
            self.node_tree = scene.node_tree

            # Clear existing nodes
            self.node_tree.nodes.clear()

        elif self.editor_type.upper() == "GEOMETRY":
            """
            if (self.obj is None) or (self.obj.type != 'MESH'):
                warn_msg = f"_create_node_tree(), self.obj is None, or its type is not 'MESH'."
                self.logger.warning(warn_msg)
                return 
            """

            # Create a new Geometry Node Tree (node group)
            geometry_name = f"{self.editor_name}_geometry"
            self.node_tree = bpy.data.node_groups.new(
                name=geometry_name, 
                type='GeometryNodeTree'
            )
            
        else:
            warn_msg = f"Unknown editor type: '{self.editor_type}'"
            self.logger.warning(warn_msg)
            

    def reset(self):
        try:
            # Clear default nodes
            if self.node_tree:
                for node in self.node_tree.nodes:
                    self.node_tree.nodes.remove(node)

                for link in self.node_tree.links:
                    self.node_tree.links.remove(link)

            # Recreate the node tree.
            self._create_node_tree()  
            self.logger.info(f"reset(), Reset EditorNode nodes.")

        except Exception as e:
            warn_msg = f"reset(), Could not reset EditorNode class, "
            warn_msg += f"error message: '{str(e)}'."
            self.logger.warning(warn_msg)
 


    def set_object(
            self, 
            mesh_obj=None
        ):
        # Double-check if the mesh object is ready.
        if not mesh_obj or not hasattr(mesh_obj, 'type') or mesh_obj.type != 'MESH':
            warn_msg = f"set_object(), the input mesh object is not valid, either none or of wrong type."
            self.logger.warning(warn_msg)
        
        self.obj= mesh_obj
        info_msg = f"set_object(), obj_name='{self.obj.name}'."
        self.logger.info(info_msg)


    def create_node(
            self, 
            node_name="", 
            node_type="", 
            node_attributes={}, 
            location=(0, 0)
        ):
        """
        Creates a new shader node and sets its attributes.

        Args:
            node_name (str): The name of this node. If its name is "", a random name will be given to the node.
                The node name is useful when retrieving this node object.
            node_type (str): The type of this node. If its type is "", this function will do nothing. 
                The valid values are ( ...).
            node_attributes (dict): A dictionary of this node's attribute names and values.
            location (tuple): The location of this node in the Blender editor UI. 

        Returns:
            The object instance of the newly created editor node.
        """
        if not self.node_tree:
            warn_msg =f"create_node(), Node tree not set."
            self.logger.warning(warn_msg)
            return None
        
        if len(node_type) == 0:
            warn_msg =f"create_node(), Input node_type is an empty string."
            self.logger.warning(warn_msg)
            return None       

        if len(node_name) == 0:
            node_name = f"{node_type}_node"
            warn_msg =f"create_node(), Input node_name is an empty string, rename it to '{node_name}'."
            self.logger.warning(warn_msg)            

        new_node = self.node_tree.nodes.new(type=node_type)
        new_node.name = node_name
        new_node.location = location
        
        if len(node_attributes) > 0:
            self.set_node_attribute(node_name, node_attributes)
        
        info_msg = f"create_node(), node_name='{node_name}', node_type='{node_type}'."
        self.logger.info(info_msg)

        return new_node


    def get_node(
            self,
            node_name=""
        ):
        """
        Given the name of an editor node, return its object instance.

        Args:
            node_name (str): The name of an editor node. 
        
        Returns:
            The object instance of the editor node, or None.
        """
        # return self.node_tree.nodes.get(node_name)
        for idx, node in enumerate(self.node_tree.nodes):
            # self.logger.debug(f"get_node(), node.name=='{node.name}'")
            if node.name == node_name:
                info_msg = f"get_node(), find a node named '{node_name}'."
                self.logger.info(info_msg)
                return node
        return None
    

    def set_node_attribute(
            self, 
            node_name="", 
            node_attributes={}
        ):
        """
        Updates the attributes of an existing node.

        Args:
            node_name (str): The name of an editor node. 
            node_attributes: The key-value pairs of the node's attributes.
        """
        if not self.node_tree:
            warn_msg =f"set_node_attribute(), Node tree not set."
            self.logger.warning(warn_msg)
            return

        target_node = self.get_node(node_name)
        if target_node:
            for attr_name, attr_value in node_attributes.items():
                if attr_name in target_node.inputs:
                    target_node.inputs[attr_name].default_value = attr_value
                elif hasattr(target_node, attr_name):
                    setattr(target_node, attr_name, attr_value)
            
            info_msg = f"set_node_attribute(), Attributes for node '{node_name}' updated."
            self.logger.info(info_msg)

            debug_msg = f"set_node_attribute(), Attributes for node '{node_name}' updated to:"
            attr_json_str = json.dumps(node_attributes, indent=2, ensure_ascii=False)
            debug_msg += f"\n{attr_json_str}"
            self.logger.debug(debug_msg)

        else:
            warn_msg = f"Editor node '{node_name}' not found."
            self.logger.warning(warn_msg)


    def create_link(
            self, 
            from_node_output=None, 
            to_node_input=None
        ):
        """
        Creates a new link between two nodes.

        Args:
            link_name (str): The name of this link.
            from_node_output (obj): The object instance of an output socket of the from_node. 
            to_node_input (obj): The object instance of an input socket of the to_node.    

        Returns:
            The object instance of the newly created link.   
        """
        if not self.node_tree:
            warn_msg =f"create_link(), Node tree not set."
            self.logger.warning(warn_msg)
            return None

        if from_node_output and to_node_input:
            new_link = self.node_tree.links.new(from_node_output, to_node_input)

            info_msg = f"create_link(), Create a link, "
            info_msg += f"from '{from_node_output.node.name}.{from_node_output.name}', "
            info_msg += f"to '{to_node_input.node.name}.{to_node_input.name}'."
            self.logger.info(info_msg)
            return new_link
        
        else:
            warn_msg = f"create_link(), Could not create link, "
            if from_node_output is None and to_node_input is None:
                warn_msg += f"both 'from_node_output' and 'to_node_input' are None."
            elif from_node_output and to_node_input is None:
                warn_msg += f"from '{from_node_output.node.name}.{from_node_output.name}', to a None 'to_node'."
            elif from_node_output is None and to_node_input:
                warn_msg += f"from a None 'from_node', to '{to_node_input.node.name}.{to_node_input.name}'."
            else:
                warn_msg += f"from '{from_node_output.node.name}.{from_node_output.name}', "
                warn_msg += f"to '{to_node_input.node.name}.{to_node_input.name}', for unknown reason."      

            self.logger.warning(warn_msg)      
            return None
        

    def get_link(
            self,
            link_name=""
        ):
        """
        Given the name of an editor node, return its object instance.

        Args:
            link_name (str): The name of a link between two editor nodes. 

        Returns:
            The object instance of the link, or None.
        """
        # link_obj = self.node_tree.links.get(link_name)
        for link in self.node_tree.links:
            if link.name == link_name:
                return link
        return None


    @staticmethod
    def usage_demo():
        """
        A static method to demonstrate the functionality of the TextureGenerator class.
        """
        print("[INFO] --- Running TextureGenerator Demo ---")
        bpy.ops.object.select_all(action='DESELECT')
        
        cube_obj = bpy.data.objects.get("MultiShaderCube")
        if cube_obj:
            bpy.data.objects.remove(cube_obj, do_unlink=True)
        
        bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        bpy.context.object.name = "MultiShaderCube"
        active_obj = bpy.context.object

        generator = EditorNode(
            editor_name="DemoEditor", 
            editor_type="material", 
            obj=active_obj
        )

        """
        world_generator = EditorNode(
            editor_name="WorldEditor", 
            editor_type="world", 
            obj=active_obj
        )
        """

        output_node = generator.get_node(
            node_name="Material Output"
        )
        principled_node = generator.get_node(
            node_name="Principled BSDF"
        )
        
        emission_node = generator.create_node(
            node_type='ShaderNodeEmission', 
            node_name="DemoEmissionNode", 
            node_attributes={'Strength': 5.0}, 
            location=(-200, -200)
        )     
        mix_shader_node = generator.create_node(
            node_type='ShaderNodeMixShader', 
            node_name="DemoMixShader",
            node_attributes={'Factor': 0.5}, 
            location=(100, 0)
        )

        generator.create_link(
            from_node_output=principled_node.outputs[0], 
            to_node_input=mix_shader_node.inputs[1]
        )
        generator.create_link(
            from_node_output=emission_node.outputs[0], 
            to_node_input=mix_shader_node.inputs[2]
        )
        generator.create_link(
            from_node_output=mix_shader_node.outputs[0], 
            to_node_input=output_node.inputs[0]
        )        
        

        # --- Verification Step ---
        print("\n\n[INFO] --- Verifying links after rewiring ---")
        emission_node_final = generator.get_node("DemoEmissionNode")

        if emission_node_final:
            print("[INFO] Found 'DemoEmissionNode'. Checking its output links:")
            if not emission_node_final.outputs[0].links:
                print("[INFO] No outgoing links found from the Emission socket.")
            else:
                for link in emission_node_final.outputs[0].links:
                    from_node = link.from_node.name
                    from_socket = link.from_socket.name
                    to_node = link.to_node.name
                    to_socket = link.to_socket.name
                    print(f"  - Link still exists: From '{from_node}.{from_socket}' to '{to_node}.{to_socket}'")
        else:
            print("[ERROR] Could not find 'DemoEmissionNode' for verification.")

        print("[INFO] --- EditorNode Demo Finished ---\n\n")
        

