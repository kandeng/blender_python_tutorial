import bpy

class TextureGenerator:
    """
    A class to simplify the creation and modification of Blender materials and
    their shader node trees.
    """

    def __init__(self):
        """
        Initializes the TextureGenerator instance with an object to apply materials to.
        """
        self.obj = None
        self.material = None
        self.node_tree = None
        print("[INFO] TextureGenerator initialized.")


    def set_object(self, mesh_obj):
        # Double-check if the mesh object is ready.
        if not mesh_obj or not hasattr(mesh_obj, 'type') or mesh_obj.type != 'MESH':
            raise ValueError("A valid mesh object must be provided.")
        
        self.obj= mesh_obj
        print(f"[INFO] ApplyTexture initialized for mesh '{self.obj.name}'.")


    def create_material(self, mat_name):
        """
        Creates a new material, enables its node tree, and applies it to the object.
        It also sets the instance's active material and node_tree.

        Args:
            mat_name (str): The name for the new material.

        Returns:
            bpy.types.Material: The newly created material.
        """
        if self.obj is None:
            print(f"[ERROR] The 'self.obj' is None, please set 'self.obj' first, after then you can use 'create_material()'.")
            return
        
        self.material = bpy.data.materials.new(name=mat_name)
        self.material.use_nodes = True
        self.node_tree = self.material.node_tree
        
        self.node_tree.nodes.clear()
            
        if self.obj.data.materials:
            self.obj.data.materials[0] = self.material
        else:
            self.obj.data.materials.append(self.material)
        
        print(f"[INFO] Material '{mat_name}' created and assigned.")
        return self.material


    def create_node(self, node_type, node_name, attributes=None, location=(0, 0)):
        """
        Creates a new shader node and sets its attributes.
        """
        if not self.node_tree:
            print("[ERROR] Node tree not set. Create a material first.")
            return None

        new_node = self.node_tree.nodes.new(type=node_type)
        new_node.name = node_name
        new_node.location = location
        
        if attributes:
            self.set_node_attribute(node_name, attributes)
        
        print(f"[INFO] Created node '{node_name}' of type '{node_type}'.")
        return new_node

    def set_node_attribute(self, node_name, attributes):
        """
        Updates the attributes of an existing node.
        """
        if not self.node_tree:
            print("[ERROR] Node tree not set. Create a material first.")
            return

        target_node = self.node_tree.nodes.get(node_name)
        if target_node:
            for attr, value in attributes.items():
                if attr in target_node.inputs:
                    target_node.inputs[attr].default_value = value
                elif hasattr(target_node, attr):
                    setattr(target_node, attr, value)
            print(f"[INFO] Attributes for node '{node_name}' updated.")
        else:
            print(f"[ERROR] Node '{node_name}' not found.")

    def create_link(self, from_node, from_socket_name, to_node, to_socket_name):
        """
        Creates a new link between two nodes.
        """
        if not self.node_tree:
            print("[ERROR] Node tree not set. Create a material first.")
            return

        from_socket = from_node.outputs.get(from_socket_name)
        to_socket = to_node.inputs.get(to_socket_name)
        
        if from_socket and to_socket:
            self.node_tree.links.new(from_socket, to_socket)
            print(f"[INFO] Link created from '{from_node.name}.{from_socket_name}' to '{to_node.name}.{to_socket_name}'.")
        else:
            print(f"[ERROR] Could not create link. Sockets not found ('{from_socket_name}' or '{to_socket_name}').")

    def set_link_attribute(self, from_node_name, from_socket_name, to_node_name, to_socket_name):
        """
        Ensures a specific link exists, replacing any existing link to the destination socket.
        """
        if not self.node_tree:
            print("[ERROR] Node tree not set. Create a material first.")
            return

        from_node = self.node_tree.nodes.get(from_node_name)
        to_node = self.node_tree.nodes.get(to_node_name)

        if not from_node:
            print(f"[ERROR] 'From' node '{from_node_name}' not found.")
            return
        if not to_node:
            print(f"[ERROR] 'To' node '{to_node_name}' not found.")
            return

        to_socket = to_node.inputs.get(to_socket_name)
        if not to_socket:
            print(f"[ERROR] Socket '{to_socket_name}' not found on node '{to_node_name}'.")
            return

        for link in to_socket.links:
            print(f"[INFO] Removed old link from '{link.from_node.name}.{link.from_socket.name}' to '{to_node.name}.{to_socket.name}'.")
            self.node_tree.links.remove(link)

        self.create_link(from_node, from_socket_name, to_node, to_socket_name)


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

    generator = TextureGenerator(active_obj)
    generator.create_material("MixedShaderMaterial")
    
    output_node = generator.create_node('ShaderNodeOutputMaterial', "My_Output_Node", location=(400, 0))
    principled_node = generator.create_node('ShaderNodeBsdfPrincipled', "My_Principled_Node", location=(-200, 200))
    emission_node = generator.create_node('ShaderNodeEmission', "My_Emission_Node", 
        attributes={'Strength': 5.0}, location=(-200, -200))
    mix_shader_node = generator.create_node('ShaderNodeMixShader', "My_Mix_Shader",
        attributes={'Factor': 0.5}, location=(100, 0))
        
    generator.create_link(principled_node, 'BSDF', mix_shader_node, 'Shader_1')
    generator.create_link(emission_node, 'Emission', mix_shader_node, 'Shader_2')
    generator.create_link(mix_shader_node, 'Shader', output_node, 'Surface')
    
    generator.set_node_attribute("My_Principled_Node", {'Base Color': (1.0, 0.0, 0.0, 1.0)})
    generator.set_node_attribute("My_Emission_Node", {'Color': (0.0, 0.0, 1.0, 1.0)})
    
    print("\n[INFO] --- Rewiring link to use Principled BSDF directly ---")
    generator.set_link_attribute(
        from_node_name="My_Principled_Node", 
        from_socket_name="BSDF",
        to_node_name="My_Output_Node", 
        to_socket_name="Surface"
    )

    # --- Verification Step ---
    print("\n[INFO] --- Verifying links after rewiring ---")
    emission_node_final = generator.node_tree.nodes.get("My_Emission_Node")
    if emission_node_final:
        print("[INFO] Found 'My_Emission_Node'. Checking its output links:")
        if not emission_node_final.outputs['Emission'].links:
            print("[INFO] No outgoing links found from the Emission socket.")
        else:
            for link in emission_node_final.outputs['Emission'].links:
                from_node = link.from_node.name
                from_socket = link.from_socket.name
                to_node = link.to_node.name
                to_socket = link.to_socket.name
                print(f"  - Link still exists: From '{from_node}.{from_socket}' to '{to_node}.{to_socket}'")
    else:
        print("[ERROR] Could not find 'My_Emission_Node' for verification.")

    print("[INFO] --- Demo Finished ---")

