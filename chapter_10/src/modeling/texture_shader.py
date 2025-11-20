import bpy
import os
import json


class TextureShader:
    """
    A class to use various texture and shader nodes to decorate a mesh object.
    """
    def __init__(
            self, 
            obj=None
        ):
        """
        Initializes the texture shader.

        Args:
            obj (object): An object instance that the texture and shader nodes are used for. 
        """
        self.logger = None
        self.obj = obj

        self.editor_node = None
        self.modifier_generator = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Modeling").getLogger()
        
            from modeling.editor_node import EditorNode
            self.editor_node = EditorNode(editor_name="TextureShader", editor_type="MATERIAL", obj=self.obj)

            from modeling.modifier_generator import ModifierGenerator
            self.modifier_generator = ModifierGenerator()

            self.logger.info(f"Create a texture_shader named for a mesh object named '{self.obj.name}'.")
        except Exception as e:
            print(f"[ERROR] Could not initialize TextureShader object. The error message: '{str(e)}'.")

        self.texture_dir = "/"
        self.texture_paths = {}   

        self.secondary_texture_dir = "/"
        self.secondary_texture_paths = {}

        self.node_names = []
        self.secondary_node_names = []


    def set_object(self, mesh_object=None):
        # Double-check if the mesh object is ready.
        if not mesh_object or not hasattr(mesh_object, 'type') or mesh_object.type != 'MESH':
            warn_msg = f"set_object(), A valid mesh object must be provided."
            self.logger.warning(warn_msg)
            return
        
        self.obj = mesh_object
        info_msg = f"set_object(), object name = '{self.obj.name}'."
        self.logger.info(info_msg)


    def set_texture_directory(
            self, 
            texture_dir="/"
        ):
        """
        Set the file directory from which to get the texture files.

        Args:
            texture_dir (str): The file directory from which to get the texture files.
        """
        if not os.path.isdir(texture_dir):
            warn_msg = f"set_texture_directory(), Texture directory not found: {texture_dir}"
            self.logger.warn(warn_msg)
            return 
        
        self.texture_dir = texture_dir
        self.texture_paths = self._scan_texture_directory(self.texture_dir)    

        info_msg = f"set_texture_directory(), Found {len(self.texture_paths)} texture maps."
        self.logger.info(info_msg)


    def set_secondary_texture_directory(
            self, 
            secondary_texture_dir="/"
        ):
        """
        Set the file directory from which to get the secondary texture files.

        Args:
            secondary_texture_dir (str): The file directory from which to get the secondary texture files.
        """
        if not os.path.isdir(secondary_texture_dir):
            warn_msg = f"set_secondary_texture_directory(), Texture directory not found: {secondary_texture_dir}"
            self.logger.warn(warn_msg)
            return         
        
        self.secondary_texture_dir = secondary_texture_dir
        self.secondary_texture_paths = self._scan_texture_directory(texture_dir=self.secondary_texture_dir)    

        info_msg = f"set_secondary_texture_directory(), Found {len(self.secondary_texture_paths)} texture maps."
        self.logger.info(info_msg)


    def _scan_texture_directory(self, texture_dir="/"):
        """ Scans the directory for common PBR texture maps. """
        texture_files = {'color': ''}

        for file_name in os.listdir(texture_dir):
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.exr')):
                file_path = os.path.join(texture_dir, file_name)
                if 'color' in file_name.lower() or 'albedo' in file_name.lower() or 'diff' in file_name.lower():
                    texture_files['color'] = file_path
                elif 'displace' in file_name.lower() or 'height' in file_name.lower() or 'disp' in file_name.lower():
                    texture_files['displacement'] = file_path
                elif 'rough' in file_name.lower():
                    texture_files['roughness'] = file_path
                elif 'normal' in file_name.lower() or 'nor' in file_name.lower():
                    texture_files['normal'] = file_path
                elif 'metal' in file_name.lower():
                    texture_files['metalness'] = file_path

        # Sometimes the 'color' image doesn't have special tag, e.g. 'Flower_Rose-Bungaria_1.png'
        if len(texture_files['color']) == 0:
            for file_name in os.listdir(texture_dir):
                if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.exr')):
                    preserved_tags = ['preview', 'displace', 'height', 'disp', 'rough', 'normal', 'metal']
                    if all(tag not in file_name.lower() for tag in preserved_tags):
                        file_path = os.path.join(texture_dir, file_name)
                        texture_files['color'] = file_path

        debug_msg = f"_scan_texture_directory(), texture_files in file directory '{texture_dir}': \n"
        debug_msg += json.dumps(texture_files, indent=2, ensure_ascii=False)
        self.logger.debug(debug_msg)

        return texture_files


    def get_node(self, node_name=""):
        node_obj = self.editor_node.get_node(node_name=node_name)
        return node_obj

    def get_link(self, link_name=""):
        link_obj = self.editor_node.get_link(link_name=link_name)
        return link_obj
    
    def set_node_attribute(self, node_name="", node_attribute={}):
        self.editor_node.set_node_attribute(node_name=node_name, node_attribute=node_attribute)


    def create_base_nodes(self):
        """
        Creates and connects the basic Principled BSDF shader nodes.
        """
        # Clear default nodes
        self.editor_node.node_tree.nodes.clear()

        # Set proper displacement method for Cycles, use both bump and true displacement
        # self.material.cycles.displacement_method = 'BOTH'  

        # Create the main Principled BSDF shader node
        principled_bsdf_node_name = "Principled_BSDF_Node"  
        self.principled_bsdf = self.editor_node.create_node(
            node_type='ShaderNodeBsdfPrincipled', 
            node_name=principled_bsdf_node_name,
            location=(0, 0)
        )
        self.node_names.append(principled_bsdf_node_name)

        # Create texture coordinate and mapping nodes for texture transformations
        tex_coord_node_name = "Texture_Coordinate"
        tex_coord_node = self.editor_node.create_node(
            node_type='ShaderNodeTexCoord',
            node_name=tex_coord_node_name,
            location=(-800, 0)
        )
        self.node_names.append(tex_coord_node_name)

        mapping_node_name = "Mapping_Node"  # This is what the code is looking for
        mapping_node = self.editor_node.create_node(
            node_type='ShaderNodeMapping',
            node_name=mapping_node_name,
            location=(-600, 0)
        )
        self.node_names.append(mapping_node_name)

        # Connect texture coordinate to mapping node
        if tex_coord_node and mapping_node:
            self.editor_node.create_link(
                from_node_output=tex_coord_node.outputs['UV'],  # UV output
                to_node_input=mapping_node.inputs['Vector']   # Vector input
            )

        # Create and link the material output node
        material_output_node_name = "Output_Node"  # Use the expected name
        material_output_node = self.editor_node.create_node(
            node_type='ShaderNodeOutputMaterial',
            node_name=material_output_node_name,
            location=(300, 0)
        )
        self.node_names.append(material_output_node_name)

        # Check that nodes were created successfully before linking
        if self.principled_bsdf and material_output_node:
            self.editor_node.create_link(
                from_node_output=self.principled_bsdf.outputs[0],  # BSDF
                to_node_input=material_output_node.inputs[0]   # Surface
            )
        else:
            warn_msg = f"create_base_nodes(), Failed to create shader nodes."
            self.logger.warn(warn_msg)
            return

        info_msg = f"create_base_nodes(), Base texture_shader nodes created."
        self.logger.info(info_msg)


    def create_secondary_base_nodes(self):             
        #  Get related nodes that have been created previously.
        principled_bsdf_node = self.get_node("Principled_BSDF_Node")
        output_node = self.get_node("Output_Node")
        output_node.location=(800, 0)
      
        # Create mix shader node, and rearrange the links.
        mix_shader_node_name = "mix_Principled_BSDFs"
        mix_shader = self.editor_node.create_node(
            node_type='ShaderNodeMixShader', 
            node_name=mix_shader_node_name, 
            location=(600, 0)
        )
        self.node_names.append(mix_shader_node_name)

        self.editor_node.create_link(
            from_node_output=principled_bsdf_node.outputs[0],  # BDSF
            to_node_input=mix_shader.inputs[1]   # Shader
        )
        self.editor_node.create_link(
            from_node_output=mix_shader.outputs[0],   # Shader
            to_node_input=output_node.inputs[0]    # Surface
        )

        # Create and link noise texture node. 
        noise_texture_node_name = "Noise_Texture_Node"
        noise_texture_node = self.editor_node.create_node(
            node_type='ShaderNodeTexNoise', 
            node_name=noise_texture_node_name, 
            location=(0, 0)
        )
        self.node_names.append(noise_texture_node_name)      
        noise_texture_node.inputs[2].default_value = 2.0      # Scale
        noise_texture_node.inputs[3].default_value = 15.0     # Detail
        noise_texture_node.inputs[4].default_value = 0.8      # Roughness
        noise_texture_node.inputs[5].default_value = 0.1      # Lacuna
        noise_texture_node.inputs[8].default_value = 0.1      # Distortion

        # Create and link color ramp node
        color_ramp_node_name = "Color_Ramp_Node"
        color_ramp_node = self.editor_node.create_node(
            node_type='ShaderNodeValToRGB', 
            node_name=color_ramp_node_name, 
            location=(200, 0)
        )
        self.node_names.append(color_ramp_node_name)      
        # color_ramp_node.inputs[0].default_value = 0.5      # Fac

        # Set the first color to black
        elements = color_ramp_node.color_ramp.elements
        elements[0].position = 0.5
        elements[0].color = (0.0, 0.0, 0.0, 1.0)
        
        # Set the second color to blue
        elements[1].position = 0.75
        elements[1].color = (1.0, 1.0, 1.0, 1.0)

        self.editor_node.create_link(
            from_node_output=color_ramp_node.outputs[0],      # Color
            to_node_input=mix_shader.inputs[0]             # Fac
        )     
        self.editor_node.create_link(
            from_node_output=noise_texture_node.outputs[0],     # Fac
            to_node_input=color_ramp_node.inputs[0]          # Fac
        )        
    

        # Create and link the noise texture coordinate node and mapping node
        noise_tex_coord_node_name = "Noise_Texture_Coordinate"
        noise_tex_coord_node = self.editor_node.create_node(
            node_type='ShaderNodeTexCoord', 
            node_name=noise_tex_coord_node_name, 
            location=(-400, 0)
        )
        self.node_names.append(noise_tex_coord_node_name)
        
        noise_mapping_node_name = "Noise_Mapping"
        noise_mapping_node = self.editor_node.create_node(
            node_type='ShaderNodeMapping', 
            node_name=noise_mapping_node_name, 
            location=(-200, 0)
        )
        self.node_names.append(noise_mapping_node_name)

        self.editor_node.create_link(
            from_node_output=noise_tex_coord_node.outputs[3],    # Object 
            to_node_input=noise_mapping_node.inputs[0]        # Vector
        )

        self.editor_node.create_link(
            from_node_output=noise_mapping_node.outputs[0],      # Vector 
            to_node_input=noise_texture_node.inputs[0]        # Vector
        )

        # Create and link the secondary principled BSDF node
        secondary_principled_bsdf_node_name = "secondary_Principled_BSDF"
        self.secondary_principled_bsdf = self.editor_node.create_node(
            node_type='ShaderNodeBsdfPrincipled', 
            node_name=secondary_principled_bsdf_node_name, 
            location=(200, -500)
        )
        self.node_names.append(secondary_principled_bsdf_node_name)

        self.editor_node.create_link(
            from_node_output=self.secondary_principled_bsdf.outputs[0],   # BDSF
            to_node_input=mix_shader.inputs[2]   # Shader
        )

        # Create and link texture coordinate node.
        secondary_tex_coord_node_name = "secondary_Texture_Coordinate"
        secondary_tex_coord_node = self.editor_node.create_node(
            node_type='ShaderNodeTexCoord', 
            node_name=secondary_tex_coord_node_name, 
            location=(-800, -500)
        )
        self.node_names.append(secondary_tex_coord_node_name)
        
        secondary_mapping_node_name = "secondary_Mapping"
        secondary_mapping_node = self.editor_node.create_node(
            node_type='ShaderNodeMapping', 
            node_name=secondary_mapping_node_name, 
            location=(-600, -500)
        )
        self.node_names.append(secondary_mapping_node_name)

        self.editor_node.create_link(
            from_node_output=secondary_tex_coord_node.outputs[3],  # Object 
            to_node_input=secondary_mapping_node.inputs[0]      # Vector
        )

        info_msg = f"create_secondary_base_nodes(), Base shader nodes created."
        self.logger.info(info_msg)


    def create_texture_nodes(self):
        """
        Creates image texture nodes for all available texture maps.
        """
        # Get related nodes that have created previously.
        principled_bsdf_node = self.get_node("Principled_BSDF_Node")
        output_node = self.get_node("Output_Node")
        coordinate_mapping_node = self.get_node("Mapping_Node")

        if principled_bsdf_node and output_node and coordinate_mapping_node:
            info_msg = f"create_texture_nodes(), Create various texture nodes "
            info_msg += f"for all the texture files in '{self.texture_dir}'."
            self.logger.info(info_msg)
        else:
            warn_msg = f"create_texture_nodes(), Principled_BSDF_Node not created yet, "
            warn_msg += f"run create_base_nodes() first."
            self.logger.warn(warn_msg)
            return 

        # Create and connect nodes for each texture type found
        node_y = 1300

        if (('color' in self.texture_paths) and
            (len(self.texture_paths['color']) > 0)
            ):
            node_y = node_y - 300
            color_node_name = "Color_Node"
            color_node = self.create_imagetexture_node(
                texture_image = self.texture_paths['color'], 
                node_name = color_node_name, 
                node_location = (-300, node_y)
            )
            self.node_names.append(color_node_name)
            color_node.image.colorspace_settings.name = 'sRGB'

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = color_node.inputs[0]    # Vector                
            )
            self.editor_node.create_link(
                from_node_output = color_node.outputs[0],  # Color
                to_node_input = principled_bsdf_node.inputs[0]    # Base Color                
            )

        if (('roughness' in self.texture_paths) and 
            (len(self.texture_paths['roughness']) > 0)
            ):
            node_y = node_y - 300
            rough_node_name = "Rough_Node"
            rough_node =  self.create_imagetexture_node(
                texture_image = self.texture_paths['roughness'], 
                node_name = rough_node_name, 
                node_location = (-300, node_y)
            )      
            self.node_names.append(rough_node_name)
            rough_node.image.colorspace_settings.name = 'Non-Color'

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = rough_node.inputs[0]    # Vector                
            )
            self.editor_node.create_link(
                from_node_output = rough_node.outputs[0],  # Color
                to_node_input = principled_bsdf_node.inputs[2]    # Roughness                
            )

        if (('normal' in self.texture_paths) and 
            (len(self.texture_paths['normal']) > 0)
            ):
            node_y = node_y - 300
            normal_node_name = "Normal_Node"
            normal_map_node_name = "Normal_Map_Node"
            normal_node, normal_map_node = self.create_normal_node(
                texture_image = self.texture_paths['normal'], 
                normal_node_name = normal_node_name, 
                normal_map_node_name = normal_map_node_name, 
                node_location = (-300, node_y)
            )     
            self.node_names.append(normal_node_name) 
            self.node_names.append(normal_map_node_name) 

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = normal_node.inputs[0]    # Vector                
            )
            self.editor_node.create_link(
                from_node_output = normal_map_node.outputs[0],       # Normal
                to_node_input = principled_bsdf_node.inputs[5]    # Normal                
            )

        if (('metalness' in self.texture_paths) and 
            (len(self.texture_paths['metalness']) > 0)
            ):
            node_y = node_y - 300
            metal_node_name = "Metal_Node"
            metal_node = self.create_imagetexture_node(
                texture_image = self.texture_paths['metalness'], 
                node_name = metal_node_name, 
                node_location = (-300, node_y)
            )    
            self.node_names.append(metal_node_name)   
            metal_node.image.colorspace_settings.name = 'Non-Color'

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = metal_node.inputs[0]                 # Vector                
            )
            self.editor_node.create_link(
                from_node_output = metal_node.outputs[0],            # Normal
                to_node_input = principled_bsdf_node.inputs[1]    # Normal                
            )

        if (('displacement' in self.texture_paths) and 
            (len(self.texture_paths['displacement']) > 0)
            ):
            node_y = node_y - 300
            texture_node_name = "Displace_Texture_Node"
            displace_node_name = "Displace_Map_Node"

            self.logger.debug(f"create_texture_nodes(), self.texture_paths['displacement']='{self.texture_paths['displacement']}'. ")
            displace_texture_node, displace_map_node = self.create_displacement_node(
                texture_image = self.texture_paths['displacement'], 
                texture_node_name = texture_node_name, 
                displace_node_name = displace_node_name, 
                node_location = (-300, node_y)
            )
            self.node_names.append(texture_node_name)   
            self.node_names.append(displace_node_name)   

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],       # Vector
                to_node_input = displace_texture_node.inputs[0]              # Vector             
            )
            self.editor_node.create_link(
                from_node_output = displace_map_node.outputs[0],     # Displacement
                to_node_input = output_node.inputs[2]                # Displacement                
            )            

        info_msg = f"create_texture_nodes(), Creates image texture nodes for all available texture maps."
        self.logger.info(info_msg)


    def create_secondary_texture_nodes(self):
        """
        Creates the secondary image texture nodes for all available texture maps.
        """
        # Get related nodes that have created previously.
        output_node = self.get_node("Output_Node")
        principled_bsdf_node = self.get_node("secondary_Principled_BSDF")
        coordinate_mapping_node = self.get_node("secondary_Mapping")

        if principled_bsdf_node and output_node and coordinate_mapping_node:
            info_msg = f"create_secondary_texture_nodes(), Create various texture nodes "
            info_msg += f"for all the secondary texture files in '{self.secondary_texture_dir}'."
            self.logger.info(info_msg)
        else:
            warn_msg = f"create_secondary_texture_nodes(), The secondary_Principled_BSDF node not created yet, "
            warn_msg += f"run create_secondary_base_nodes() first."
            self.logger.warn(warn_msg)
            return 

        # Create and connect nodes for each texture type found
        node_y = -200
        if (('color' in self.secondary_texture_paths) and 
            (len(self.texture_paths['color']) > 0)
            ):
            node_y = node_y - 300
            color_node_name = "Secondary_Color_Node"
            color_node = self.create_imagetexture_node(
                texture_image = self.secondary_texture_paths['color'], 
                node_name = color_node_name, 
                node_location = (-300, node_y)
            )
            self.node_names.append(color_node_name)
            color_node.image.colorspace_settings.name = 'sRGB'
            color_node.projection = 'BOX'
            color_node.projection_blend = 0.2

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = color_node.inputs[0]    # Vector                
            )
            self.editor_node.create_link(
                from_node_output = color_node.outputs[0],  # Color
                to_node_input = principled_bsdf_node.inputs[0]    # Base Color                
            )

        if (('roughness' in self.secondary_texture_paths) and
            (len(self.texture_paths['roughness']) > 0)
            ):
            node_y = node_y - 300
            rough_node_name = "Secondary_Rough_Node"
            rough_node =  self.create_imagetexture_node(
                texture_image = self.secondary_texture_paths['roughness'], 
                node_name = rough_node_name, 
                node_location = (-300, node_y)
            )      
            self.node_names.append(rough_node_name)
            rough_node.image.colorspace_settings.name = 'Non-Color'
            rough_node.projection = 'BOX'
            rough_node.projection_blend = 0.2

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = rough_node.inputs[0]    # Vector                
            )
            self.editor_node.create_link(
                from_node_output = rough_node.outputs[0],  # Color
                to_node_input = principled_bsdf_node.inputs[2]    # Roughness                
            )

            node_y = node_y - 300
            normal_node_name = "Secondary_Normal_Node"
            normal_map_node_name = "Secondary_Normal_Map_Node"
            normal_node, normal_map_node = self.create_normal_node(
                texture_image = self.secondary_texture_paths['normal'], 
                normal_node_name = normal_node_name, 
                normal_map_node_name = normal_map_node_name, 
                node_location = (-300, node_y)
            )     
            self.node_names.append(normal_node_name) 
            self.node_names.append(normal_map_node_name) 
            normal_node.projection = 'BOX'
            normal_node.projection_blend = 0.2

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = normal_node.inputs[0]    # Vector                
            )
            self.editor_node.create_link(
                from_node_output = normal_map_node.outputs[0],       # Normal
                to_node_input = principled_bsdf_node.inputs[5]    # Normal                
            )

        if (('metalness' in self.secondary_texture_paths) and
            (len(self.texture_paths['metalness']) > 0)
            ):
            node_y = node_y - 300
            metal_node_name = "Secondary_Metal_Node"
            metal_node = self.create_imagetexture_node(
                texture_image = self.secondary_texture_paths['metalness'], 
                node_name = metal_node_name, 
                node_location = (-300, node_y)
            )    
            self.node_names.append(metal_node_name)   
            metal_node.image.colorspace_settings.name = 'Non-Color'
            metal_node.projection = 'BOX'

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = metal_node.inputs[0]                 # Vector                
            )
            self.editor_node.create_link(
                from_node_output = metal_node.outputs[0],            # Normal
                to_node_input = principled_bsdf_node.inputs[1]    # Normal                
            )

        if (('displacement' in self.secondary_texture_paths) and
            (len(self.texture_paths['displacement']) > 0)
            ):
            node_y = node_y - 300
            texture_node_name = "Secondary_Displace_Texture_Node"
            displace_node_name = "Secondary_Displace_Map_Node"
            displace_texture_node, displace_map_node = self.create_displacement_node(
                texture_image = self.secondary_texture_paths['displacement'], 
                texture_node_name = texture_node_name, 
                displace_node_name = displace_node_name, 
                node_location = (-300, node_y)
            )
            self.node_names.append(texture_node_name)   
            self.node_names.append(displace_node_name)   
            displace_texture_node.projection = 'BOX'

            self.editor_node.create_link(
                from_node_output = coordinate_mapping_node.outputs[0],  # Vector
                to_node_input = displace_texture_node.inputs[0]              # Vector             
            )
            self.editor_node.create_link(
                from_node_output = displace_map_node.outputs[0],     # Displacement
                to_node_input = output_node.inputs[2]         # Displacement                
            )            

        info_msg = f"create_secondary_texture_nodes(), "
        info_msg += f"Creates secondary image texture nodes for all available texture maps."
        self.logger.info(info_msg)


    def create_imagetexture_node(
            self, 
            texture_image="", 
            node_name="", 
            node_location=(0, 0)
        ):
        # Create texture node
        info_msg = f"create_imagetexture_node(), Created image-texture shader node."
        self.logger.info(info_msg)
    
        tex_node = self.editor_node.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=node_name, 
            location=node_location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(texture_image)

        info_msg = f"create_imagetexture_node(), create a image_texture shader node."
        self.logger.info(info_msg)
        return tex_node


    def create_normal_node(
            self, 
            texture_image="", 
            normal_node_name="", 
            normal_map_node_name="", 
            node_location=(0, 0)
        ):
        # Create texture node
        tex_node = self.editor_node.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=normal_node_name, 
            location=node_location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(texture_image)
        tex_node.image.colorspace_settings.name = 'Non-Color'

        # Create normal map node
        normal_map_node = self.editor_node.create_node(
            node_type='ShaderNodeNormalMap', 
            node_name=normal_map_node_name, 
            location=(node_location[0] + 300, node_location[1] - 100)
        )
        
        self.editor_node.create_link(
            tex_node.outputs[0],  # Color
            normal_map_node.inputs[1]    # Color                
        )
        normal_map_node.inputs[0].default_value = 1.0  # Strength 

        info_msg = f"create_normal_node(), Created normal map node using TextureShader."
        self.logger.info(info_msg)
        return tex_node, normal_map_node
    

    def create_displacement_node(
            self, 
            texture_image="", 
            texture_node_name="", 
            displace_node_name="", 
            node_location=(0, 0)
        ):
        info_msg = f"create_displacement_node(), Created displacement shader node, not modifier."
        self.logger.info(info_msg)

        tex_node = self.editor_node.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=texture_node_name, 
            location=node_location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(texture_image)
        tex_node.image.colorspace_settings.name = 'Non-Color'
        
        # Create displacement node
        disp_node = self.editor_node.create_node(
            node_type='ShaderNodeDisplacement', 
            node_name=displace_node_name, 
            location=(node_location[0] + 300, node_location[1] - 100)
        )
        
        # Set displacement attributes
        disp_node.inputs['Height'].default_value = 0.0
        disp_node.inputs['Midlevel'].default_value = 0.0
        disp_node.inputs['Scale'].default_value = 0.1

        # Set link from tex_node to disp_node
        self.editor_node.create_link(
            from_node_output = tex_node.outputs[0],  # Color
            to_node_input = disp_node.inputs[3]    # Normal                
        )
        
        # Enable displacement in material settings for Cycles
        # self.material.displacement_method = 'BOTH'

        info_msg = f"create_displacement_node(), create a displace shader node."
        self.logger.info(info_msg)
        return tex_node, disp_node
    

    def create_displacement_modifier(
            self, 
            file_path="",
            disp_strength=0.1, 
            midlevel=0.5
        ):
        """
        Create a displacement modifier using the ModifierGenerator class.
        There are 2 ways to use displacement,
        1. Use shader node, to change the way of rendering only,
        2. Use modifier tool, to change the locations of the vertices physically.
        Usually, only one way is selected to use. 
        However, it is okay to use both. The rendering effect will look like doubly displaced. 
        """
        # Prepare the mesh for UV mapping
        bpy.context.view_layer.objects.active = self.obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        try:
            # Load the displacement texture
            # path = self.texture_paths['displacement']
            disp_image = bpy.data.images.load(file_path, check_existing=True)
            disp_image.colorspace_settings.name = 'Non-Color'
        except Exception as e:
            print(f"[ERROR] Could not load displacement texture: {e}")
            return
        
        """
        # Add subdivision surface modifier to enhance displacement effect
        subsurf = self.obj.modifiers.new(name="DisplacementSubdivision", type='SUBSURF')
        subsurf.levels = 3  # Viewport subdivision
        subsurf.render_levels = 3  # Render subdivision
        subsurf.subdivision_type = 'CATMULL_CLARK'        
        """

        # Initialize the ModifierGenerator
        self.modifier_generator.set_object(self.obj)

        # Create a texture for the displacement modifier
        disp_texture = bpy.data.textures.new(name="DisplacementTexture", type='IMAGE')
        disp_texture.image = disp_image

        # Create displacement modifier with initial attributes
        modifier_attributes = {
            "strength": disp_strength,
            "mid_level": midlevel,
            "texture_coords": 'UV',
            "uv_layer": "UVMap",
            "texture": disp_texture
        }

        # Create the displacement modifier using ModifierGenerator
        disp_mod = self.modifier_generator.add_modifier(
            modifier_type="displace",
            modifier_name="Final_Displacement",
            modifier_attributes=modifier_attributes
        )
        
        # Ensure the displacement affects both viewport and render
        if disp_mod:
            disp_mod.show_viewport = True
            disp_mod.show_render = True
            
        # Make sure the material is set to use displacement in both viewport and render
        if self.obj.data.materials:
            mat = self.obj.data.materials[0]
            if mat:
                mat.cycles.displacement_method = 'BOTH'  # Use both bump and true displacement

        info_msg = f"create_displacement_modifier(), use 'modifier_generator' to create a displace modifier."
        self.logger.info(info_msg)
        return disp_mod


    def apply_texture(
            self, 
            texture_dir=""
        ):
        """
        Given a texture file directory and a mesh object, apply the texture images in that directory to the object. 

        Args:
            obj (object): A mesh object instance that the texture images are used to. 
            texture_dir (str): A file directory contains some texture images, including color, normal, displacement etc.
        """
        try:           
            self.set_texture_directory(texture_dir)
            self.create_base_nodes()
            self.create_texture_nodes()

            """
            path = self.texture_paths['displacement']
            self.create_displacement_modifier(
                file_path=path,
                disp_strength=0.2, 
                midlevel=0.5
            )
            """
            
        except (ValueError, FileNotFoundError) as e:
            warn_msg = f"apply_texture(), An error occurred: {str(e)}."
            self.logger.warn(warn_msg)

        info_msg = f"apply_texture(), Given a texture file directory '{texture_dir}', "
        info_msg += f"and a mesh object '{self.obj.name}', "
        info_msg += f"apply the texture images in that directory to the object."
        self.logger.info(info_msg)
        

    def apply_secondary_texture(
            self, 
            secondary_texture_dir=""
        ):
        """
        Given a secondary texture file directory and a mesh object, apply the texture images in that directory to the object. 

        Args:
            obj (object): A mesh object instance that the texture images are used to. 
            texture_dir (str): A file directory contains some texture images, including color, normal, displacement etc.
        """
        try:           
            self.set_secondary_texture_directory(secondary_texture_dir)
            self.create_secondary_base_nodes()
            self.create_secondary_texture_nodes()

            """
            path = self.secondary_texture_paths['displacement']
            self.create_displacement_modifier(
                file_path=path,
                disp_strength=0.2, 
                midlevel=0.5
            )
            """
            
        except (ValueError, FileNotFoundError) as e:
            warn_msg = f"apply_texture(), An error occurred: {str(e)}."
            self.logger.warn(warn_msg)

        info_msg = f"Given a texture file directory and a mesh object, "
        info_msg += f"apply the texture images in that directory to the object."
        self.logger.info(info_msg) 
    

    @staticmethod
    def usage_demo_floor():
        # Clear the scene and create a sample mesh to texture
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
        sample_mesh = bpy.context.active_object
        sample_mesh.name = "DemoFloor"
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.subdivide(number_cuts=50)
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Define the texture directory
        # IMPORTANT: Update this path to your texture folder
        texture_directory = f"/home/robot/blender_asset/texture"
        wood_texture_directory = f"{texture_directory}/WoodFloor043_4K"
        moss_texture_directory = f"{texture_directory}/Moss002_2K-JPG"

        texture_applier = TextureShader(sample_mesh)
        texture_applier.apply_texture(texture_dir=wood_texture_directory)
        texture_applier.apply_secondary_texture(secondary_texture_dir=moss_texture_directory)

        bpy.context.scene.render.engine = 'CYCLES'

        # Set up the sun. 
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 3.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (0.0, 0.0, 5.0) 
        bpy.context.collection.objects.link(sun_obj)


    @staticmethod
    def usage_demo_flower():
        from asset_gateway.glb_gltf_file_handler import GlbGltfFileHandler
        glb_gltf_handler = GlbGltfFileHandler() 
        
        blender_asset_dir = "/home/robot/blender_asset"
        glb_gltf_filepaths = [
            f"{blender_asset_dir}/sketchfab/flower_rose/model.glb",
            f"{blender_asset_dir}/sketchfab/flower_rose/model_out/model.gltf"
        ]

        for idx in range(len(glb_gltf_filepaths)):
            object_names = glb_gltf_handler.import_glb_gltf(
                glb_gltf_filepath=glb_gltf_filepaths[idx]
            ) 
            object_instances = glb_gltf_handler.get_objects(object_names)

            texture_dirpath = os.path.dirname(os.path.abspath(glb_gltf_filepaths[idx])) 
            for item_name in os.listdir(texture_dirpath):
                item_path = os.path.join(texture_dirpath, item_name)
                
                if os.path.isdir(item_path):
                    if 'texture' in item_path.lower():
                        # self.logger.debug(f"load_materials(): item_path='{item_path}'")
                        texture_dirpath = item_path
            
            for obj in object_instances[:1]:
                texture_applier = TextureShader(obj)
                texture_applier.apply_texture(texture_dir=texture_dirpath)


        # Set up the sun. 
        bpy.context.scene.render.engine = 'CYCLES'
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 30.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (15, 10.0, 50.0) 
        bpy.context.collection.objects.link(sun_obj)


    @staticmethod
    def usage_demo():
        TextureShader.usage_demo_floor()
        # TextureShader.usage_demo_flower()



if __name__ == "__main__":
    TextureShader.usage_demo()