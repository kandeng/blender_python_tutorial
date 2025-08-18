import bpy
import os
import sys
import pprint


class ApplyTexture:
    """
    A class to apply a full set of PBR textures to a specified mesh object.
    """
    def __init__(self, use_modifier = True):
        """
        Initializes the texture application process.
        """
        self.texture_generator = None
        self.modifier_generator = None

        try:
            from shader_modifier.shader_generator import ShaderGenerator
            self.texture_generator = ShaderGenerator()

            from shader_modifier.modifier_generator import ModifierGenerator
            self.modifier_generator = ModifierGenerator()
        except ImportError:
            print("[ERROR] Could not import ApplyTexture class. Make sure 'apply_texture_asset.py' is in the correct directory.")
            ApplyTexture = None

        self.mesh = None
        self.use_modifier = use_modifier
        
        self.texture_dir = None
        self.texture_paths = {}
        self.secondary_texture_dir = None
        self.secondary_texture_paths = {}

        self.material = None
        self.node_names = []
        self.secondary_node_names = []



    def set_object(self, mesh_object=None):
        # Double-check if the mesh object is ready.
        if not mesh_object or not hasattr(mesh_object, 'type') or mesh_object.type != 'MESH':
            raise ValueError("A valid mesh object must be provided.")
        
        self.mesh = mesh_object
        print(f"[INFO] ApplyTexture initialized for mesh '{self.mesh.name}'.")

    def set_texture_directory(self, texture_dir="/"):
        if not os.path.isdir(texture_dir):
            raise FileNotFoundError(f"Texture directory not found: {texture_dir}")
        
        self.texture_dir = texture_dir
        self.texture_paths = self._scan_texture_directory(self.texture_dir)    
        print(f"[INFO] Found {len(self.texture_paths)} texture maps.")

    def set_secondary_texture_directory(self, secondary_texture_dir="/"):
        if not os.path.isdir(secondary_texture_dir):
            raise FileNotFoundError(f"Texture directory not found: {secondary_texture_dir}")
        
        self.secondary_texture_dir = secondary_texture_dir
        print(f"[INFO] Following is the images for the secondary texture.")
        self.secondary_texture_paths = self._scan_texture_directory(self.secondary_texture_dir)    
        print(f"[INFO] Found {len(self.secondary_texture_paths)} for the secondary texture maps.")

    def _scan_texture_directory(self, texture_dir):
        """ Scans the directory for common PBR texture maps. """
        texture_files = {}
        for file in os.listdir(texture_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.exr')):
                file_path = os.path.join(texture_dir, file)
                if 'color' in file.lower() or 'albedo' in file.lower() or 'diff' in file.lower():
                    texture_files['color'] = file_path
                elif 'displacement' in file.lower() or 'height' in file.lower() or 'disp' in file.lower():
                    texture_files['displacement'] = file_path
                elif 'rough' in file.lower():
                    texture_files['roughness'] = file_path
                elif 'normal' in file.lower() or 'nor' in file.lower():
                    texture_files['normal'] = file_path
                elif 'metal' in file.lower():
                    texture_files['metalness'] = file_path
        
        print(f"\n[INFO] texture_files in file directory '{texture_dir}':")
        pprint.pprint(texture_files)
        print(f"\n")
        return texture_files


    def get_node_by_name(self, node_name:str):
        node_obj = self.texture_generator.get_node_by_name(node_name)
        return node_obj

    def get_link_by_name(self, link_name:str):
        link_obj = self.texture_generator.get_link_by_name(link_name)
        return link_obj
    
    def set_node_attribute(self, node_name:str, node_attribute:dict):
        self.texture_generator.set_node_attribute(node_name, node_attribute)


    def create_base_nodes(self):
        """
        Creates the commonly used, non-image-specific shader nodes using TextureGenerator.
        """
        print("[INFO] Creating base shader nodes...")
        
        # Create material using TextureGenerator
        material_name = f"{self.mesh.name}_Material"
        self.texture_generator.set_object(self.mesh)
        self.material = self.texture_generator.create_material(material_name)
        
        # Create output node.
        output_node_name = "Output_Node"
        output_node = self.texture_generator.create_node(
            'ShaderNodeOutputMaterial', 
            output_node_name, 
            location=(500, 500)
        )
        self.node_names.append(output_node_name)

        # Create principled BSDF node.
        principled_bsdf_node_name = "Principled_BSDF_Node"
        principled_bsdf = self.texture_generator.create_node(
            'ShaderNodeBsdfPrincipled', 
            principled_bsdf_node_name, 
            location=(200, 500)
        )
        self.node_names.append(principled_bsdf_node_name)

        # Link BSDF to output
        self.texture_generator.create_link_via_sockets(
            principled_bsdf.outputs[0],
            output_node.inputs[0]
        )
        
        # Create texture coordinate node.
        texture_coordinate_node_name = "Texture_Coordinate_Node"
        tex_coord_node = self.texture_generator.create_node(
            'ShaderNodeTexCoord', 
            texture_coordinate_node_name, 
            location=(-800, 500)
        )
        self.node_names.append(texture_coordinate_node_name)
        
        # Create texture coordinate map node.
        mapping_node_name = "Mapping_Node"
        mapping_node = self.texture_generator.create_node(
            'ShaderNodeMapping', 
            mapping_node_name, 
            location=(-600, 500)
        )
        self.node_names.append(mapping_node_name)
        
        # Link texture coordinate node to texture coordinate map node.
        self.texture_generator.create_link_via_sockets(
            tex_coord_node.outputs[2],  # UV
            mapping_node.inputs[0]    # Vector                
        )

        print("[INFO] Base shader nodes created using TextureGenerator.")


    def create_secondary_base_nodes(self):
        print("[INFO] Creating base shader nodes for the secondary texture ...")
                
        #  Get related nodes that have been created previously.
        principled_bsdf_node = self.get_node_by_name("Principled_BSDF_Node")
        output_node = self.get_node_by_name("Output_Node")
        output_node.location=(800, 0)
      
        # Create mix shader node, and rearrange the links.
        mix_shader_node_name = "mix_Principled_BSDFs"
        mix_shader = self.texture_generator.create_node(
            'ShaderNodeMixShader', 
            mix_shader_node_name, 
            location=(600, 0)
        )
        self.node_names.append(mix_shader_node_name)

        self.texture_generator.create_link_via_sockets(
            principled_bsdf_node.outputs[0],  # BDSF
            mix_shader.inputs[1]   # Shader
        )

        self.texture_generator.create_link_via_sockets(
            mix_shader.outputs[0],   # Shader
            output_node.inputs[0]    # Surface
        )

        # Create and link noise texture node. 
        noise_texture_node_name = "Noise_Texture_Node"
        noise_texture_node = self.texture_generator.create_node(
            'ShaderNodeTexNoise', 
            noise_texture_node_name, 
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
        color_ramp_node = self.texture_generator.create_node(
            'ShaderNodeValToRGB', 
            color_ramp_node_name, 
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

        self.texture_generator.create_link_via_sockets(
            color_ramp_node.outputs[0],      # Color
            mix_shader.inputs[0]             # Fac
        )     
        self.texture_generator.create_link_via_sockets(
            noise_texture_node.outputs[0],     # Fac
            color_ramp_node.inputs[0]          # Fac
        )        
    

        # Create and link the noise texture coordinate node and mapping node
        noise_tex_coord_node_name = "Noise_Texture_Coordinate"
        noise_tex_coord_node = self.texture_generator.create_node(
            'ShaderNodeTexCoord', 
            noise_tex_coord_node_name, 
            location=(-400, 0)
        )
        self.node_names.append(noise_tex_coord_node_name)
        
        noise_mapping_node_name = "Noise_Mapping"
        noise_mapping_node = self.texture_generator.create_node(
            'ShaderNodeMapping', 
            noise_mapping_node_name, 
            location=(-200, 0)
        )
        self.node_names.append(noise_mapping_node_name)

        self.texture_generator.create_link_via_sockets(
            noise_tex_coord_node.outputs[3],    # Object 
            noise_mapping_node.inputs[0]        # Vector
        )

        self.texture_generator.create_link_via_sockets(
            noise_mapping_node.outputs[0],      # Vector 
            noise_texture_node.inputs[0]        # Vector
        )

        # Create and link the secondary principled BSDF node
        secondary_principled_bsdf_node_name = "secondary_Principled_BSDF"
        self.secondary_principled_bsdf = self.texture_generator.create_node(
            'ShaderNodeBsdfPrincipled', 
            secondary_principled_bsdf_node_name, 
            location=(200, -500)
        )
        self.node_names.append(secondary_principled_bsdf_node_name)

        self.texture_generator.create_link_via_sockets(
            self.secondary_principled_bsdf.outputs[0],   # BDSF
            mix_shader.inputs[2]   # Shader
        )

        # Create and link texture coordinate node.
        secondary_tex_coord_node_name = "secondary_Texture_Coordinate"
        secondary_tex_coord_node = self.texture_generator.create_node(
            'ShaderNodeTexCoord', 
            secondary_tex_coord_node_name, 
            location=(-800, -500)
        )
        self.node_names.append(secondary_tex_coord_node_name)
        
        secondary_mapping_node_name = "secondary_Mapping"
        secondary_mapping_node = self.texture_generator.create_node(
            'ShaderNodeMapping', 
            secondary_mapping_node_name, 
            location=(-600, -500)
        )
        self.node_names.append(secondary_mapping_node_name)

        self.texture_generator.create_link_via_sockets(
            secondary_tex_coord_node.outputs[3],  # Object 
            secondary_mapping_node.inputs[0]      # Vector
        )

        print("[INFO] Base shader nodes created for the secondary texture.")


    def create_texture_nodes(self):
        """
        Creates image texture nodes for all available texture maps.
        """
        print("[INFO] Creating image texture nodes...")

        # Get related nodes that have created previously.
        principled_bsdf_node = self.get_node_by_name("Principled_BSDF_Node")
        output_node = self.get_node_by_name("Output_Node")
        coordinate_mapping_node = self.get_node_by_name("Mapping_Node")

        if principled_bsdf_node and output_node and coordinate_mapping_node:
            print("[INFO] Creating image texture nodes...")
        else:
            print("[ERROR] Principled_BSDF_Node not created yet, run create_base_nodes() first.")

        # Create and connect nodes for each texture type found
        node_y = 1300

        if 'color' in self.texture_paths:
            node_y = node_y - 300
            color_node_name = "Color_Node"
            color_node = self.create_imagetexture_node(
                texture_image = self.texture_paths['color'], 
                node_name = color_node_name, 
                node_location = (-300, node_y)
            )
            self.node_names.append(color_node_name)
            color_node.image.colorspace_settings.name = 'sRGB'

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                color_node.inputs[0]    # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                color_node.outputs[0],  # Color
                principled_bsdf_node.inputs[0]    # Base Color                
            )

        if 'roughness' in self.texture_paths:
            node_y = node_y - 300
            rough_node_name = "Rough_Node"
            rough_node =  self.create_imagetexture_node(
                texture_image = self.texture_paths['roughness'], 
                node_name = rough_node_name, 
                node_location = (-300, node_y)
            )      
            self.node_names.append(rough_node_name)
            rough_node.image.colorspace_settings.name = 'Non-Color'

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                rough_node.inputs[0]    # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                rough_node.outputs[0],  # Color
                principled_bsdf_node.inputs[2]    # Roughness                
            )

        if 'normal' in self.texture_paths:
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

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                normal_node.inputs[0]    # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                normal_map_node.outputs[0],       # Normal
                principled_bsdf_node.inputs[5]    # Normal                
            )

        if 'metalness' in self.texture_paths:
            node_y = node_y - 300
            metal_node_name = "Metal_Node"
            metal_node = self.create_imagetexture_node(
                texture_image = self.texture_paths['metalness'], 
                node_name = metal_node_name, 
                node_location = (-300, node_y)
            )    
            self.node_names.append(metal_node_name)   
            metal_node.image.colorspace_settings.name = 'Non-Color'

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                metal_node.inputs[0]                 # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                metal_node.outputs[0],            # Normal
                principled_bsdf_node.inputs[1]    # Normal                
            )

        if 'displacement' in self.texture_paths:
            # If use modifier, then don't do anything here. 
            # Instead, call create_displacement_modifier() in a separated step.
            if not self.use_modifier:
                node_y = node_y - 300
                texture_node_name = "Displace_Texture_Node", 
                displace_node_name = "Displace_Map_Node", 
                displace_texture_node, displace_map_node = self.create_displacement_node(
                    texture_image = self.texture_paths['displacement'], 
                    texture_node_name = texture_node_name, 
                    displace_node_name = displace_node_name, 
                    node_location = (-300, node_y)
                )
                self.node_names.append(texture_node_name)   
                self.node_names.append(displace_node_name)   

                self.texture_generator.create_link_via_sockets(
                    coordinate_mapping_node.outputs[0],  # Vector
                    displace_texture_node.inputs[0]              # Vector             
                )
                self.texture_generator.create_link_via_sockets(
                    displace_map_node.outputs[0],     # Displacement
                    output_node.inputs[2]         # Displacement                
                )


    def create_secondary_texture_nodes(self):
        """
        Creates the secondary image texture nodes for all available texture maps.
        """
        print("[INFO] Creating the secondary image texture nodes...")

        # Get related nodes that have created previously.
        output_node = self.get_node_by_name("Output_Node")
        principled_bsdf_node = self.get_node_by_name("secondary_Principled_BSDF")
        coordinate_mapping_node = self.get_node_by_name("secondary_Mapping")

        if output_node and principled_bsdf_node and coordinate_mapping_node:
            print("[INFO] Creating secondary image texture nodes...")
        else:
            print("[ERROR] The secondary_Principled_BSDF node not created yet, run create_secondary_base_nodes() first.")

        # Create and connect nodes for each texture type found
        node_y = -200
        if 'color' in self.secondary_texture_paths:
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

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                color_node.inputs[0]    # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                color_node.outputs[0],  # Color
                principled_bsdf_node.inputs[0]    # Base Color                
            )

        if 'roughness' in self.secondary_texture_paths:
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

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                rough_node.inputs[0]    # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                rough_node.outputs[0],  # Color
                principled_bsdf_node.inputs[2]    # Roughness                
            )

        if 'normal' in self.secondary_texture_paths:
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

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                normal_node.inputs[0]    # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                normal_map_node.outputs[0],       # Normal
                principled_bsdf_node.inputs[5]    # Normal                
            )

        if 'metalness' in self.secondary_texture_paths:
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

            self.texture_generator.create_link_via_sockets(
                coordinate_mapping_node.outputs[0],  # Vector
                metal_node.inputs[0]                 # Vector                
            )
            self.texture_generator.create_link_via_sockets(
                metal_node.outputs[0],            # Normal
                principled_bsdf_node.inputs[1]    # Normal                
            )

        if 'displacement' in self.secondary_texture_paths:
            # If use modifier, then don't do anything here. 
            # Instead, call create_displacement_modifier() in a separated step.
            if not self.use_modifier:
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

                self.texture_generator.create_link_via_sockets(
                    coordinate_mapping_node.outputs[0],  # Vector
                    displace_texture_node.inputs[0]              # Vector             
                )
                self.texture_generator.create_link_via_sockets(
                    displace_map_node.outputs[0],     # Displacement
                    output_node.inputs[2]         # Displacement                
                )



    def create_imagetexture_node(self, texture_image, node_name, node_location):
        # Create texture node
        tex_node = self.texture_generator.create_node(
            'ShaderNodeTexImage', 
            node_name, 
            location=node_location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(texture_image)
        return tex_node


    def create_normal_node(self, texture_image, normal_node_name, normal_map_node_name, node_location):
        # Create texture node
        tex_node = self.texture_generator.create_node(
            'ShaderNodeTexImage', 
            normal_node_name, 
            location=node_location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(texture_image)
        tex_node.image.colorspace_settings.name = 'Non-Color'

        # Create normal map node
        normal_map_node = self.texture_generator.create_node(
            'ShaderNodeNormalMap', 
            normal_map_node_name, 
            location=(node_location[0] + 300, node_location[1] - 100)
        )
        
        self.texture_generator.create_link_via_sockets(
            tex_node.outputs[0],  # Color
            normal_map_node.inputs[1]    # Color                
        )
        normal_map_node.inputs[0].default_value = 1.0  # Strength 

        print(f"[INFO] Created normal map node using TextureGenerator.")
        return tex_node, normal_map_node
    

    def create_displacement_node(self, texture_image, texture_node_name, displace_node_name, node_location):
        # Create texture node
        tex_node = self.texture_generator.create_node(
            'ShaderNodeTexImage', 
            texture_node_name, 
            location=node_location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(texture_image)
        tex_node.image.colorspace_settings.name = 'Non-Color'
        
        # Create displacement node
        disp_node = self.texture_generator.create_node(
            'ShaderNodeDisplacement', 
            displace_node_name, 
            location=(node_location[0] + 300, node_location[1] - 100)
        )
        
        # Set displacement attributes
        disp_node.inputs['Height'].default_value = 0.0
        disp_node.inputs['Midlevel'].default_value = 0.0
        disp_node.inputs['Scale'].default_value = 0.1

        # Set link from tex_node to disp_node
        self.texture_generator.create_link_via_sockets(
            tex_node.outputs[0],  # Color
            disp_node.inputs[3]    # Normal                
        )
        
        
        # Enable displacement in material settings for Cycles
        self.material.displacement_method = 'BOTH'

        self.use_modifier = False
        print(f"[INFO] Created displacement shader node using TextureGenerator.")
        return tex_node, disp_node
    

    def create_displacement_modifier(self, disp_strength:float=0.1, midlevel:float=0.5):
        """
        Create a displacement modifier using the ModifierGenerator class.
        There are 2 ways to use displacement,
        1. Use shader node, to change the way of rendering only,
        2. Use modifier tool, to change the locations of the vertices physically.
        Usually, only one way is selected to use. 
        However, it is okay to use both. The rendering effect will look like doubly displaced. 
        """
        # Prepare the mesh for UV mapping
        bpy.context.view_layer.objects.active = self.mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        try:
            # Load the displacement texture
            path = self.texture_paths['displacement']
            disp_image = bpy.data.images.load(path, check_existing=True)
            disp_image.colorspace_settings.name = 'Non-Color'
        except Exception as e:
            print(f"[ERROR] Could not load displacement texture: {e}")
            return

        # Create a texture for the displacement modifier
        disp_texture = bpy.data.textures.new(name="RockDisplacementTexture", type='IMAGE')
        disp_texture.image = disp_image

        # Initialize the ModifierGenerator
        self.modifier_generator.set_object(self.mesh)

        # Create displacement modifier with initial attributes
        modifier_attributes = {
            "strength": disp_strength,
            "mid_level": midlevel,
            "texture_coords": 'UV',
            "uv_layer": "UVMap",
            "texture": disp_texture
        }

        # Create the displacement modifier using ModifierGenerator
        disp_mod = self.modifier_generator.create_modifier(
            modifier_type="displace",
            modifier_name="Final_Displacement",
            modifier_attributes=modifier_attributes
        )

        self.use_modifier = True
        print(f"[INFO] Created displacement modifier using ModifierGenerator.")
        return disp_mod

    
    def apply_another_texture(self, secondary_texture_dir=""):
        # 1. Verify secondary_texture_dir value
        if len(secondary_texture_dir) == 0 and self.secondary_texture_dir is not None :
            print("[INFO] If the input 'secondary_texture_dir' is empty,", end=" ")
            print(f"we will use 'self.secondary_texture_dir' that is '{self.secondary_texture_dir}'")
        elif len(secondary_texture_dir) > 0 and self.secondary_texture_dir is not None:
            print(f"[WARN] The previous 'self.secondary_texture_dir' that is '{self.secondary_texture_dir}',", end=" ")
            print(f"will be changed to '{secondary_texture_dir}'")
            self.set_secondary_texture_directory(secondary_texture_dir)
        elif len(secondary_texture_dir) > 0 and self.secondary_texture_dir is None:
            print(f"[INFO] Set 'self.secondary_texture_dir' to '{secondary_texture_dir}'")
            self.set_secondary_texture_directory(secondary_texture_dir)
        else:
            print(f"[ERROR] 'secondary_texture_dir'='{secondary_texture_dir}' is invalid")
            return

        # 2. Create the commonly used shader nodes for the secondary texture
        self.create_secondary_base_nodes()

        # 3. Create the textures nodes for the secondary texture
        self.create_secondary_texture_nodes()



    @staticmethod
    def setup_render_engine(engine='CYCLES', resolution=(1920, 1080)):
        """
        4. Sets up the render engine and output settings.

        Args:
            engine (str): The render engine to use ('CYCLES' or 'EEVEE').
            resolution (tuple): The output resolution (width, height).
        """
        print(f"[INFO] Setting up {engine} render engine...")
        scene = bpy.context.scene
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]

        if engine.upper() == 'CYCLES':
            scene.render.engine = 'CYCLES'
            scene.cycles.device = 'GPU'
            scene.cycles.samples = 128
        elif 'EEVEE' in engine.upper():
            try:
                scene.render.engine = 'BLENDER_EEVEE'
            except TypeError:
                print(f"[WARNING] BLENDER_EEVEE not available, falling back to BLENDER_EEVEE_NEXT.")
                scene.render.engine = 'BLENDER_EEVEE_NEXT'
            scene.eevee.taa_render_samples = 64
        else:
            print(f"[WARNING] Unknown render engine '{engine}'. Defaulting to Cycles.")
            scene.render.engine = 'CYCLES'


    # --- Main execution example ---
    @staticmethod
    def run_demo():
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
        wood_texture_directory = "/home/robot/movie_blender_studio/asset/texture/WoodFloor043_4K"
        moss_texture_directory = "/home/robot/movie_blender_studio/asset/texture/Moss002_2K-JPG"

        try:
            # 1. Instantiate the class with the mesh and texture directory
            texture_applier = ApplyTexture()
            texture_applier.set_object(sample_mesh)
            
            # 2. Apply the preliminary texture, wood.
            texture_applier.set_texture_directory(wood_texture_directory)
            texture_applier.create_base_nodes()
            texture_applier.create_texture_nodes()
            print(f"[INFO] Texture shader graph created successfully.")

            texture_applier.create_displacement_modifier()
            print(f"[INFO] Displacement modifier created successfully.")

            # 3. Apply the secondary texture, moss.
            #    It will look very stranges with moss texture. For testing purpose only.
            texture_applier.use_modifier = False
            texture_applier.set_secondary_texture_directory(moss_texture_directory)
            texture_applier.create_secondary_base_nodes()
            texture_applier.create_secondary_texture_nodes()
            print(f"[INFO] Secondary texture shader graph created successfully.")


            # 4. Set up the render engine
            ApplyTexture.setup_render_engine(engine='EEVEE')

            print("\n[SUCCESS] Script finished.")

        except (ValueError, FileNotFoundError) as e:
            print(f"\n[ERROR] An error occurred: {e}")



if __name__ == "__main__":
    ApplyTexture.run_demo()