import bpy
import json

class EditorNode:
    """
    A super class for texturing, shading, compositing, geometry node,
    simplifies the creation and property setting for the node trees.
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
                The valid values are ('MATERIAL', 'COMPOSITING', 'GEOMETRY', 'WORLD').
            obj (object): An object instance that the texture and shader materials are applied to. Not useful for 'COMPOSITING' type.
        """
        self.logger = None
        self.editor_name = editor_name
        self.editor_type = editor_type

        self.obj = obj         # Not useful for 'COMPOSITING' type.
        self.material = None   # Only useful for 'MATERIAL' type.

        self.node_tree = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger(self.editor_name).getLogger()

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
                self.logger.warn(warn_msg)
                return 

            material_name = f"{self.editor_name}_material"
            if self.obj.data.materials:
                # Use the first material slot's material
                self.material = self.obj.data.materials[0]
            else:
                # Create a new default material if none exists
                self.material = bpy.data.materials.new(name=material_name)
                self.obj.data.materials.append(self.material)            

            self.material.use_nodes = True
            self.node_tree = self.material.node_tree
                
            if self.obj.data.materials:
                self.obj.data.materials.clear()
                self.obj.data.materials.append(self.material)

        elif self.editor_type.upper() == "COMPOSITING":
            scene = bpy.context.scene
            scene.use_nodes = True
            self.node_tree = scene.node_tree

        else:
            warn_msg = f"Unknown editor type: '{self.editor_type}'"
            self.logger.warn(warn_msg)
            


    def reset(
            self, 
            editor_name="",
            editor_type=""
        ):
        """
        Remove the current node tree. And create a new one from scratch.

        Args:
            editor_name (str): The name of this editor. If its value is "", still use the previous one.
                The name will display in the logs, for debugging convenience.
            editor_type (str): The type of this editor. If its value is "", still use the previous one. 
                The valid values are ('MATERIAL', 'COMPOSITING', 'GEOMETRY', 'WORLD').
        """
        if len(editor_name) > 0:
            self.editor_name = editor_name
        if len(editor_type) > 0:
            self.editor_type = editor_type

        try:
            # Clear default nodes
            if self.node_tree:
                for node in self.node_tree.nodes:
                    self.node_tree.nodes.remove(node)

                for link in self.node_tree.links:
                    self.node_tree.links.remove(link)

            # Recreate the node tree.
            self._create_node_tree()  
            self.logger.info(f"Reset EditorNode nodes.")

        except Exception as e:
            warn_msg = f"reset(), Could not reset EditorNode class, "
            warn_msg += f"error message: '{str(e)}'."
            self.logger.warn(warn_msg)
 

    def set_object(
            self, 
            mesh_obj=None
        ):
        # Double-check if the mesh object is ready.
        if not mesh_obj or not hasattr(mesh_obj, 'type') or mesh_obj.type != 'MESH':
            warn_msg = f"set_object(), the input mesh object is not valid, either none or of wrong type."
            self.logger.warn(warn_msg)
        
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
            self.logger.warn(warn_msg)
            return None
        
        if len(node_type) == 0:
            warn_msg =f"create_node(), Input node_type is an empty string."
            self.logger.warn(warn_msg)
            return None       

        if len(node_name) == 0:
            node_name = f"{node_type}_node"
            warn_msg =f"create_node(), Input node_name is an empty string, rename it to '{node_name}'."
            self.logger.warn(warn_msg)            

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
        for node in self.node_tree.nodes:
            if node.name == node_name:
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
            self.logger.warn(warn_msg)
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
            self.logger.warn(warn_msg)


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
            self.logger.warn(warn_msg)
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

            self.logger.warn(warn_msg)      
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
    def run_demo():
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
        output_node = generator.create_node(
            node_name="DemoOutputNode", 
            node_type="ShaderNodeOutputMaterial", 
            location=(400, 0)
        )
        principled_node = generator.create_node(
            node_name="DemoPrincipledNode", 
            node_type='ShaderNodeBsdfPrincipled', 
            location=(-200, 200)
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

