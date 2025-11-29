import bpy
import json

class MaterialEditor:
    """
    A class to manage the material slots of a mesh object,
    including the creation, linking and property setting of texture/shader/material nodes.
    """
    def __init__(
            self, 
            obj:object=None
        ):
        if not obj or not hasattr(obj, 'type') or obj.type != 'MESH':
            warn_msg = f"MaterialEditor(), the input mesh object is not valid, either none or of wrong type."
            self.logger.warning(warn_msg)
            return

        self.obj = obj   
        self.activate_material = None
        self.material_node_tree = None
        self.logger = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Modeling").getLogger()

            info_msg = f"MaterialEditor of '{self.obj.name}' is initialized."
            self.logger.info(info_msg)

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize MaterialEditor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize MaterialEditor class, error message: '{str(e)}'")


    def get_material_slots(
            self
        ) -> list:
        try:
            material_slots = []
            for mat in self.obj.data.materials:
                material_slots.append(mat.name)

            debug_msg = f"get_material_slots(), the material slots of object '{self.obj.name}' are: \n"
            material_slots_str = json.dumps(material_slots, ensure_ascii=False, indent=2)
            debug_msg += material_slots_str
            self.logger.debug(debug_msg)

            return material_slots
        
        except Exception as e:
            warn_msg = f"get_material_slots(), cannot get the material slots of object '{self.obj.name}', "
            warn_msg += f"the exception is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return []


    def get_material(
            self,
            material_name: str=""
        ) -> object:
        try:
            material_name = material_name.strip()
            for mat_obj in self.obj.data.materials:
                if mat_obj.name.lower() == material_name.lower():
                    self.activate_material = mat_obj
                    self.material_node_tree = mat_obj.node_tree

                    info_msg = f"get_material(), the object '{self.obj.name}'s activate material_node_tree "
                    info_msg += f"is set to the node_tree of the material '{material_name}'."
                    self.logger.info(info_msg)

                    return mat_obj

            warn_msg = f"get_material(), the material '{material_name}' is not yet associated with "
            warn_msg += f"object '{self.obj.name}'."
            self.logger.warning(warn_msg)
            return None
        
        except Exception as e:
            warn_msg = f"get_material(), cannot get the material '{material_name}' of object '{self.obj.name}', "
            warn_msg += f"the exception is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return None
        


    def create_material(
            self,
            material_name:str=""
        ):    
        material_name = material_name.strip()

        try:
            # Create a new default material if none exists
            material_obj = bpy.data.materials.new(name=material_name)
            material_obj.use_nodes = True

            self.obj.data.materials.append(material_obj)          
            self.activate_material = material_obj   
            self.material_node_tree = material_obj.node_tree

            info_msg = f"create_material(), a new material '{material_name}' has been created, "
            info_msg += f"and been set to the object '{self.obj.name}'s activate material_node_tree."
            self.logger.info(info_msg)

        except Exception as e:
            warn_msg = f"create_material(), couldn't create '{material_name}' for object '{self.obj.name}', "
            warn_msg += f"the exception is: '{str(e)}'."
            self.logger.warning(warn_msg)



    def create_node(
            self, 
            node_name:str="", 
            node_type:str="", 
            node_attributes:dict={}, 
            location:tuple=(0, 0)
        ) -> object:
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
        if not self.material_node_tree:
            warn_msg =f"create_node(), material's node_tree is not set."
            self.logger.warning(warn_msg)
            return None
        
        if len(node_type) == 0:
            warn_msg =f"create_node(), node_type is empty."
            self.logger.warning(warn_msg)
            return None       

        if len(node_name) == 0:
            node_name = f"{node_type}_node"
            debug_msg =f"create_node(), the input node_name is an empty string, name it to '{node_name}'."
            self.logger.debug(debug_msg)            

        self.activate_material.use_nodes = True
        new_node = self.material_node_tree.nodes.new(type=node_type)
        new_node.name = node_name
        new_node.location = location
        
        if len(node_attributes) > 0:
            self.set_node_attribute(node_name, node_attributes)
        
        info_msg = f"create_node(), node_name='{node_name}', node_type='{node_type}'."
        self.logger.info(info_msg)

        return new_node


    def get_node_or_group(
            self,
            node_name:str=""
        ):
        # return self.material_node_tree.nodes.get(node_name)
        for idx, node in enumerate(self.material_node_tree.nodes):
            # self.logger.debug(f"get_node_or_group(), [{idx}] node_name='{node_name}', node.name='{node.name}' ")

            if node.name.lower() == node_name.lower():
                info_msg = f"get_node_or_group(), find a node named '{node_name}'."
                self.logger.info(info_msg)
                return node
        return None
    

    def set_node_attribute(
            self, 
            node_name:str="", 
            node_attributes:dict={}
        ):
        """
        Updates the attributes of an existing node.

        Args:
            node_name (str): The name of an editor node. 
            node_attributes: The key-value pairs of the node's attributes.
        """
        if not self.material_node_tree:
            warn_msg =f"set_node_attribute(), material's node_tree is not set."
            self.logger.warning(warn_msg)
            return

        self.activate_material.use_nodes = True      
        target_node = self.get_node_or_group(node_name=node_name)

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
            warn_msg = f"set_node_attribute(), The shader node '{node_name}' of object '{self.obj.name}' is not found."
            self.logger.warning(warn_msg)


    def create_link(
            self, 
            from_node_output:object=None, 
            to_node_input:object=None
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
        if not self.material_node_tree:
            warn_msg =f"create_link(), material's node_tree is not set."
            self.logger.warning(warn_msg)
            return None

        if from_node_output and to_node_input:
            new_link = self.material_node_tree.links.new(from_node_output, to_node_input)

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
            link_name:str=""
        ):
        """
        Given the name of an editor node, return its object instance.

        Args:
            link_name (str): The name of a link between two editor nodes. 

        Returns:
            The object instance of the link, or None.
        """
        # link_obj = self.node_tree.links.get(link_name)
        for link in self.material_node_tree.links:
            if link.name == link_name:
                return link
        return None



    def _clone_nodes_to_group(
            self,
            group_node:object=None,
            nodes_to_group:list=[]
        ) -> dict:
        nodes_in_group = {}  # Map original node NAME → cloned node
        
        for original_node in nodes_to_group:
            cloned_node = group_node.node_tree.nodes.new(type=original_node.bl_idname)
            cloned_node.name = original_node.name
            cloned_node.label = original_node.label
            cloned_node.location = (
                original_node.location.x,
                original_node.location.y
            )
            
            # Copy input values
            for idx, in_socket in enumerate(original_node.inputs):
                if idx < len(cloned_node.inputs) and hasattr(in_socket, 'default_value'):
                    try:
                        cloned_node.inputs[idx].default_value = in_socket.default_value.copy()
                    except:
                        pass  # Skip non-copyable values (e.g., links)
            
            nodes_in_group[original_node.name] = cloned_node
        
        return nodes_in_group


    def _clone_links_to_group(
            self,
            group_node:object=None,
            nodes_in_group:dict={}
        ):
        group_links = group_node.node_tree.links
        
        group_input_node = None
        group_output_node = None
        for node in group_node.node_tree.nodes:
            if node.bl_idname == "NodeGroupInput":
                group_input_node = node    
            elif node.bl_idname == "NodeGroupOutput":
                group_output_node = node        
            else:
                continue
        
        for original_link in self.activate_material.node_tree.links:
            from_node_name = original_link.from_node.name
            to_node_name = original_link.to_node.name

            from_socket_identifier = original_link.from_socket.identifier
            to_socket_identifier = original_link.to_socket.identifier
       
            # Clone the links that both from_node and to_node are in the group. 
            if (from_node_name in nodes_in_group) and (to_node_name in nodes_in_group):
                from_node_obj = nodes_in_group[from_node_name]
                to_node_obj = nodes_in_group[to_node_name]

                debug_msg = f"_clone_links_to_group(), from_node_name.from_socket_name='{from_node_name}.{original_link.from_socket.name}', "
                debug_msg += f"to_node_name.to_socket_name='{to_node_name}.{original_link.to_socket.name}'.\n"

                debug_msg += f"\t from_node_name.from_socket.identifier='{from_node_name}.{original_link.from_socket.identifier}', "
                debug_msg += f"to_node_name.to_socket.identifier='{to_node_name}.{original_link.to_socket.identifier}'.\n"
                self.logger.debug(debug_msg)

                try:
                    group_links.new(
                        from_node_obj.outputs[from_socket_identifier],
                        to_node_obj.inputs[to_socket_identifier]
                    )                    
                except Exception as e_indx:
                    try:
                        group_links.new(
                            from_node_obj.outputs[original_link.from_socket.name],
                            to_node_obj.inputs[original_link.to_socket.name]
                        )
                    except Exception as e_name:
                        debug_msg = f"_clone_links_to_group(), after trying to use both name and index "
                        debug_msg += f"to clone link, it still failed, with the following exception: '{str(e_name)}'."
                        continue


            # Clone the links that from_node is outside of the group and to_node is in the group. 
            elif (from_node_name not in nodes_in_group) and (to_node_name in nodes_in_group):
                from_node_obj = self.get_node_or_group(node_name=from_node_name)
                to_node_obj = nodes_in_group[to_node_name]

                try:
                    from_socket_name = f"from_{from_socket_identifier}"

                    _ = self.get_or_create_group_socket(
                        group_name=group_node.name,
                        socket_name=from_socket_name,
                        in_or_out="INPUT",  
                        socket_type=original_link.from_socket.bl_idname
                    )

                    group_links.new(
                        group_input_node.outputs[from_socket_name],
                        to_node_obj.inputs[to_socket_identifier]
                    )   

                    self.activate_material.node_tree.links.new(
                        from_node_obj.outputs[from_socket_identifier],
                        group_node.inputs[from_socket_name]
                    )                      
                except Exception as e:
                    warn_msg = f"_clone_links_to_group(), when creating an input socket and create links "
                    warn_msg += f"from external node '{from_node_name}' to internal node '{to_node_name}', "
                    warn_msg += f"following exception is thrown: '{str(e)}'."
                    self.logger.warning(warn_msg)


            # Clone the links that from_node is in the group and to_node is outside of the group. 
            elif (from_node_name in nodes_in_group) and (to_node_name not in nodes_in_group):
                from_node_obj = nodes_in_group[from_node_name] 
                to_node_obj = self.get_node_or_group(node_name=to_node_name)

                try:
                    to_socket_name = f"to_{to_socket_identifier}"

                    _ = self.get_or_create_group_socket(
                        group_name=group_node.name,
                        socket_name=to_socket_name,
                        in_or_out="OUTPUT",  
                        socket_type=original_link.to_socket.bl_idname
                    )

                    group_links.new(
                        from_node_obj.outputs[from_socket_identifier],
                        group_output_node.inputs[to_socket_name]
                    )   

                    self.activate_material.node_tree.links.new(
                        group_node.outputs[to_socket_name],
                        to_node_obj.inputs[to_socket_identifier],
                    )     
                except Exception as e:
                    warn_msg = f"_clone_links_to_group(), when creating an input socket and create links "
                    warn_msg += f"from internal node '{from_node_name}' to external node '{to_node_name}', "
                    warn_msg += f"following exception is thrown: '{str(e)}'."
                    self.logger.warning(warn_msg)                

            # Ignore the links that both from_node and to_node are outside of the group. 
            else:
                continue


    def create_group(
            self, 
            group_name: str="",
            group_nodes: list=[]
        ) -> object:
        group_name = group_name.strip()
        self.activate_material.use_nodes = True

        # 1. Create the node group, including its internal node_tree.
        group_node = None
        try:
            # Create a new Node Group data block
            # The type must be 'ShaderNodeTree' for material shader groups.
            group_tree = bpy.data.node_groups.new(name=f"{group_name}_node_tree", type='ShaderNodeTree')
            group_input = group_tree.nodes.new("NodeGroupInput")
            group_input.location = (-400, 0)
            group_output = group_tree.nodes.new("NodeGroupOutput")
            group_output.location = (400, 0)


            # Add the node group to the material.
            group_node = self.material_node_tree.nodes.new(type='ShaderNodeGroup')
            group_node.node_tree = group_tree
            group_node.name=group_name

            debug_msg = f"create_group(), create a new node group '{group_tree.name}' for object '{self.obj.name}'."
            self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"create_group(), following exception was thrown when creating a node group '{group_name}': '{str(e)}'"
            self.logger.warning(warn_msg)


        # 2. Find the nodes to be grouped 
        nodes_to_group = []
        for node_name in group_nodes:
            try:
                node_to_select = self.get_node_or_group(
                    node_name=node_name
                )
                nodes_to_group.append(node_to_select) 
            
            except Exception as e:
                warn_msg = f"create_group(), Required node '{node_name}' not found in the material's node tree, "
                warn_msg += f"the exception is: '{str(e)}'."
                self.logger.warning(warn_msg)
                continue

        try:
            # 3. Clone the group_nodes in the newly created empty node group.
            nodes_in_group = self._clone_nodes_to_group(
                group_node=group_node,
                nodes_to_group=nodes_to_group
            ) 

            # 4. Clone the links between the group nodes.
            self._clone_links_to_group(
                group_node=group_node,
                nodes_in_group=nodes_in_group
            )
        except Exception as e:
            warn_msg = f"create_group(), The following exception was thrown, when cloning the nodes and links "
            warn_msg += f"from '{group_nodes}' to group '{group_name}': '{str(e)}'"
            self.logger.warning(warn_msg)

        # 5. Remove the nodes that have been cloned inside the group
        for node in nodes_to_group:
            try:
                self.activate_material.node_tree.nodes.remove(node)
            except Exception as e:
                warn_msg = f"create_group(), The following exception was thrown, when removing node '{node.name}' "
                warn_msg += f"from material '{self.activate_material.name}': '{str(e)}'."
                self.logger.warning(warn_msg)
                continue



    def insert_nodes_to_group(
            self,
            node_names:list=[],
            group_name:str=""
        ) -> object:
        # 1. Deselect all nodes first for a clean operation
        for node in self.material_node_tree.nodes:
            node.select = False

        # 2. Select the specific nodes to be grouped 
        for node_name in node_names:
            try:
                node_to_select = self.get_node_or_group(
                    node_name=node_name
                )
                node_to_select.select = True
            
            except Exception as e:
                warn_msg = f"insert_nodes_to_group(), Required node '{node_name}' not found in the material's node tree, "
                warn_msg += f"the exception is: '{str(e)}'."
                self.logger.warning(warn_msg)
                continue

        # 3. Execute the Group Make Operator
        try:
            self.activate_material.use_nodes = True
            target_group = self.get_node_or_group(group_name)
            
            override = {
                'active_node': target_group, # Crucial: The destination group node
                'node_tree': self.material_node_tree,
                'selected_nodes': [n for n in self.material_node_tree.nodes if n.select]
            }
            bpy.ops.node.group_insert(context=override)

            info_msg = f"insert_nodes_to_group(), inserted shader nodes {node_names} into node_group '{group_name}'."
            self.logger.info(info_msg)
            return target_group

        except Exception as e:
            warn_msg = f"insert_nodes_to_group(), following exception was thrown, "
            warn_msg += f"when inserting shader nodes {node_names} into node_group '{group_name}': '{str(e)}'."
            self.logger.warning(warn_msg)
            return None



    def get_or_create_group_socket(
            self,
            group_name:str="",
            socket_name:str="",
            in_or_out:str="INPUT",  # INPUT | OUTPUT
            socket_type:str=""
        ) -> object:
        """
        Socket Type, Data Type, Description
        NodeSocketFloat, Float (Single Number), "Used for scalar values like roughness, factor (Fac), alpha, or single distance values."
        NodeSocketInt, Integer (Whole Number),"Used for discrete values like count, index, or iteration levels."
        NodeSocketColor, Color (Vector of 4 Floats), "Used for color values (RGB + Alpha)."
        NodeSocketVector, Vector (3 Floats), "Used for coordinates (X, Y, Z), normals, tangents, or position data."
        NodeSocketShader, Shader (BSDF/BDSF), "Used to pass the final shader definition, such as the output of a Principled BSDF or Mix Shader node."
        NodeSocketBool, Boolean (True/False), "Used for switches or true/false logic (e.g., controlling a Mix Shader's 'Clamp' checkbox)."
        NodeSocketString, String (Text), "Used for text input, often seen in custom nodes."        
        """
        target_group = self.get_node_or_group(node_name=group_name)

        if target_group:
            for item in target_group.node_tree.interface.items_tree:
                if item.name == socket_name and item.in_out == "INPUT":
                    info_msg = f"get_or_create_group_socket(), the socket '{socket_name}' of type '{in_or_out}' "
                    info_msg += f"already exists in group '{group_name}'."
                    self.logger.info(info_msg)
                    return item
        
            group_socket = target_group.node_tree.interface.new_socket(
                name=socket_name,             # The name you see on the outside of the group node
                in_out=in_or_out,             # Specifies it as an input socket
                socket_type=socket_type       # Defines the type of data (e.g., Color, Float, Vector)
            )

            info_msg = f"get_or_create_group_socket(), created socket '{socket_name}' of type '{in_or_out}' for group '{group_name}'."
            self.logger.info(info_msg)
            return group_socket

        else:
            warn_msg = f"get_or_create_group_socket(), the group '{group_name}' doesn't exist in material '{self.activate_material.name}'."
            self.logger.warning(warn_msg)
            return None



    def copy_group(
            self,
            source_group_name: str="",
            target_group_name: str=""
        ) -> object:
        source_group = self.get_node_or_group(
            node_name=source_group_name
        )

        if source_group is None:
            warn_msg = f"copy_group(), source_group '{source_group_name}' doesn't exist."
            self.logger.warning(warn_msg)
            return None
                    
        elif source_group.type == 'GROUP':    
            target_group = source_group.copy()
            target_group.name = target_group_name

            info_msg = f"copy_group(), make a copy of source_group '{source_group_name}' to '{target_group_name}'."
            self.logger.info(info_msg)
            return target_group
        
        else:
            warn_msg = f"copy_group(), source_group '{source_group_name}' is not a group, "
            warn_msg += f"its type is '{source_group.type}'."
            self.logger.warning(warn_msg)
            return None
    


    @staticmethod
    def usage_demo():
        """
        A static method to demonstrate the functionality of the MaterialEditor class.
        """
        print("[INFO] --- Running MaterialEditor Demo ---")
        bpy.ops.object.select_all(action='DESELECT')
        
        cube_obj = bpy.data.objects.get("MultiShaderCube")
        if cube_obj:
            bpy.data.objects.remove(cube_obj, do_unlink=True)
        
        bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
        bpy.context.object.name = "MultiShaderCube"
        active_obj = bpy.context.object

        material_editor = MaterialEditor(
            obj=active_obj
        )

        material_editor.create_material(
            material_name="DemoEditor"
        ) 

        output_node = material_editor.get_node_or_group(
            node_name="Material Output"
        )
        principled_node = material_editor.get_node_or_group(
            node_name="Principled BSDF"
        )
        
        emission_node = material_editor.create_node(
            node_type='ShaderNodeEmission', 
            node_name="DemoEmissionNode", 
            node_attributes={'Strength': 5.0}, 
            location=(-200, -200)
        )     
        mix_shader_node = material_editor.create_node(
            node_type='ShaderNodeMixShader', 
            node_name="DemoMixShader",
            node_attributes={'Factor': 0.5}, 
            location=(100, 0)
        )

        texcoord_node = material_editor.create_node(
            node_type='ShaderNodeTexCoord', 
            node_name="DemoUVCoords",
            location=(0, 100)
        )

        mix_shader_node_2 = material_editor.create_node(
            node_type='ShaderNodeMixShader', 
            node_name="DemoMixShader_2",
            node_attributes={'Factor': 0.5}, 
            location=(100, 0)
        )


        material_editor.create_link(
            from_node_output=principled_node.outputs[0], 
            to_node_input=mix_shader_node.inputs[1]
        )
        material_editor.create_link(
            from_node_output=emission_node.outputs[0], 
            to_node_input=mix_shader_node.inputs[2]
        )
        material_editor.create_link(
            from_node_output=mix_shader_node.outputs[0], 
            to_node_input=output_node.inputs[0]
        )      
        material_editor.create_link(
            from_node_output=mix_shader_node.outputs[0], 
            to_node_input=mix_shader_node_2.inputs[1]
        )    
        
        material_editor.create_link(
            from_node_output=texcoord_node.outputs[0], 
            to_node_input=emission_node.inputs[0]
        )        

        material_editor.create_link(
            from_node_output=texcoord_node.outputs[0], 
            to_node_input=principled_node.inputs[0]
        )        

        # --- Verification Step ---
        print("\n\n[INFO] --- Verifying links after rewiring ---")
        emission_node_final = material_editor.get_node_or_group("DemoEmissionNode")

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



        # Node group
        source_group = material_editor.create_group(
            group_name="DemoSourceGroup",
            group_nodes=['Principled BSDF', 'DemoEmissionNode', 'DemoMixShader']
        )

        """
        source_group = material_editor.insert_nodes_to_group(
            group_name="DemoSourceGroup",
            node_names=['DemoMixShader', 'DemoEmissionNode']
        )         


        in_socket = material_editor.create_group_socket(
            group_name="DemoSourceGroup",
            socket_name="DemoInSocket",
            in_or_out="INPUT",  # INPUT | OUTPUT
            socket_type="NodeSocketVector"
        ) 

        target_group = material_editor.copy_group(
            source_group_name="DemoSourceGroup",
            target_group_name="DemoTargetGroup"
        )
        """

        print("[INFO] --- MaterialEditor Demo Finished ---\n\n")
        

