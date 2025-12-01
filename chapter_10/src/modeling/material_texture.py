import bpy
import os
import json
from pathlib import Path

class MaterialTexture:
    """
    A class to load texture assets from local disk, and apply to a mesh object.
    A mesh object may have multiple materials, MaterialTexture is one material instance.
    """
    def __init__(
            self, 
            object_instance:object=None,
            material_name:str=""
        ):
        """
        Initializes the material instance for the object.

        Args:
            object_instance (object): An object instance that the texture and shader nodes are applied to.
            material_name (str): The name of the material.
        """
        self.obj = object_instance
        self.material_editor = None
        self.material_obj = None
        self.logger = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Modeling").getLogger()
        
            from modeling.material_editor import MaterialEditor
            self.material_editor = MaterialEditor(obj=self.obj)
            self.material_obj = self.material_editor.create_material(
                material_name=material_name
            ) 

            info_msg = f"MaterialTexture(), create a material '{self.material_obj.name}' "
            info_msg += f"for a mesh object '{self.obj.name}'."
            self.logger.info(info_msg)

        except Exception as e:
            print(f"[ERROR] Could not initialize MaterialTexture object. The error message: '{str(e)}'.")



    def scan_texture_directory(
            self, 
            texture_dir:str=""
        ) -> dict:
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

        debug_msg = f"scan_texture_directory(), texture_files in file directory '{texture_dir}': \n"
        debug_msg += json.dumps(texture_files, indent=2, ensure_ascii=False)
        self.logger.debug(debug_msg)

        return texture_files
    



    def create_base_nodes(
            self,
            principled_bsdf_node_name: str="Principled_BSDF", 
            tex_coord_node_name: str="Texture_Coordinate",
            mapping_node_name: str="Mapping_Node"
        ):
        """
        Creates and connects the basic Principled BSDF shader nodes.
        """
        principled_bsdf_node = self.material_editor.create_node(
            node_type='ShaderNodeBsdfPrincipled', 
            node_name=principled_bsdf_node_name,
            location=(300, 0)
        )
        
        tex_coord_node = self.material_editor.create_node(
            node_type='ShaderNodeTexCoord',
            node_name=tex_coord_node_name,
            location=(-800, 0)
        )

        mapping_node = self.material_editor.create_node(
            node_type='ShaderNodeMapping',
            node_name=mapping_node_name,
            location=(-600, 0)
        )

        self.material_editor.create_link(
            from_node_output=tex_coord_node.outputs['UV'], 
            to_node_input=mapping_node.inputs['Vector']   
        )

        self.material_editor.create_link(
            from_node_output=mapping_node.outputs[0], 
            to_node_input=principled_bsdf_node.inputs[0]   
        )

        info_msg = f"create_base_nodes(), Base texture_shader nodes created."
        self.logger.info(info_msg)


    def create_texture_nodes(
            self,
            principled_bsdf_node_name: str="Principled_BSDF", 
            mapping_node_name: str="Mapping_Node",
            color_node_name: str="Color_Node",
            rough_node_name: str="Rough_Node",
            normal_node_name: str="Normal_Node",
            normal_map_node_name: str="Normal_Map_Node",
            metal_node_name: str="Metal_Node",
            displace_texture_node_name: str="Displace_Texture_Node",
            displace_map_node_name: str="Displace_Map_Node"
        ):
        """
        Creates texture nodes.
        """
        principled_bsdf_node = self.material_obj.node_tree.nodes[principled_bsdf_node_name]
        coordinate_mapping_node = self.material_obj.node_tree.nodes[mapping_node_name] 

        # 1. Create 'Color_Node'
        node_y = 600
        color_node = self.material_editor.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=color_node_name, 
            location=(-300, node_y)
        )

        self.material_editor.create_link(
            from_node_output = coordinate_mapping_node.outputs[0],  # Vector
            to_node_input = color_node.inputs[0]    # Vector                
        )
        self.material_editor.create_link(
            from_node_output = color_node.outputs[0],  # Color
            to_node_input = principled_bsdf_node.inputs[0]    # Base Color                
        )

        # 2. Create 'Rough_Node'
        node_y = node_y - 300
        rough_node = self.material_editor.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=rough_node_name, 
            location=(-300, node_y)
        )

        self.material_editor.create_link(
            from_node_output = coordinate_mapping_node.outputs[0],  # Vector
            to_node_input = rough_node.inputs[0]    # Vector                
        )
        self.material_editor.create_link(
            from_node_output = rough_node.outputs[0],  # Color
            to_node_input = principled_bsdf_node.inputs[2]    # Roughness                
        )

        # 3. Create 'Normal_Node'
        node_y = node_y - 300
        normal_node = self.material_editor.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=normal_node_name, 
            location=(-300, node_y)
        )

        normal_map_node = self.material_editor.create_node(
            node_type='ShaderNodeNormalMap', 
            node_name=normal_map_node_name, 
            location=(0, node_y)
        )
        
        self.material_editor.create_link(
            normal_node.outputs[0],  # Color
            normal_map_node.inputs[1]    # Color                
        )
        normal_map_node.inputs[0].default_value = 1.0  # Strength 

        self.material_editor.create_link(
            from_node_output = coordinate_mapping_node.outputs[0],  # Vector
            to_node_input = normal_node.inputs[0]    # Vector                
        )
        self.material_editor.create_link(
            from_node_output = normal_map_node.outputs[0],       # Normal
            to_node_input = principled_bsdf_node.inputs[5]    # Normal                
        )

        # 4. Create 'Metal_Node'
        node_y = node_y - 300
        metal_node = self.material_editor.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=metal_node_name, 
            location=(-300, node_y)
        )

        self.material_editor.create_link(
            from_node_output = coordinate_mapping_node.outputs[0],  # Vector
            to_node_input = metal_node.inputs[0]                 # Vector                
        )
        self.material_editor.create_link(
            from_node_output = metal_node.outputs[0],            # Normal
            to_node_input = principled_bsdf_node.inputs[1]    # Normal                
        )

        # 5. Create 'Displacement Nodes'
        node_y = node_y - 300
        displace_tex_node = self.material_editor.create_node(
            node_type='ShaderNodeTexImage', 
            node_name=displace_texture_node_name, 
            location=(-300, node_y)
        )
        
        disp_map_node = self.material_editor.create_node(
            node_type='ShaderNodeDisplacement', 
            node_name=displace_map_node_name, 
            location=(0, node_y)
        )
        # For unknown reason, these 3 line don't work.
        disp_map_node.inputs[0].default_value = 0.0         # 'Height'
        disp_map_node.inputs[1].default_value = 0.0          # 'Midlevel'
        disp_map_node.inputs[2].default_value = 0.1          # 'Scale'

        # Set link from tex_node to disp_node
        self.material_editor.create_link(
            from_node_output = displace_tex_node.outputs[0],  # Color
            to_node_input = disp_map_node.inputs[3]    # Normal                
        )

        self.material_editor.create_link(
            from_node_output = coordinate_mapping_node.outputs[0],       # Vector
            to_node_input = displace_tex_node.inputs[0]              # Vector             
        )

        info_msg = f"create_texture_nodes(), Creates image texture nodes for all available texture maps."
        self.logger.info(info_msg)



    def create_texture_group(
            self,
            texture_name: str=""
        ) -> object:
        # 1. Create the texture/shader nodes.
        principled_bsdf_node_name = f"{texture_name}_Principled_BSDF"
        base_node_names = {
            "principled_bsdf_node_name": principled_bsdf_node_name, 
            "tex_coord_node_name": f"{texture_name}_Texture_Coordinate",
            "mapping_node_name": f"{texture_name}_Mapping_Node"            
        }
        self.create_base_nodes(**base_node_names)

        displace_map_node_name = f"{texture_name}_Displace_Map_Node"
        texture_node_names = {
            "principled_bsdf_node_name": f"{texture_name}_Principled_BSDF", 
            "mapping_node_name": f"{texture_name}_Mapping_Node",
            "color_node_name": f"{texture_name}_Color_Node",
            "rough_node_name": f"{texture_name}_Rough_Node",
            "normal_node_name": f"{texture_name}_Normal_Node",
            "normal_map_node_name": f"{texture_name}_Normal_Map_Node",
            "metal_node_name": f"{texture_name}_Metal_Node",
            "displace_texture_node_name": f"{texture_name}_Displace_Texture_Node",
            "displace_map_node_name": displace_map_node_name
        }
        self.create_texture_nodes(**texture_node_names)

        # 2. Create a node group.
        group_node_names = list({**base_node_names, **texture_node_names}.values())
        group_node = self.material_editor.create_group(
            group_name=f"{texture_name}_group",
            group_nodes=group_node_names           
        )

        # 3. Create the output sockets, and link the internal nodes to it.
        principled_bsdf_socket_name = "principled_bsdf_socket"
        _ = self.material_editor.get_or_create_group_socket(
            group_name=group_node.name,
            socket_name=principled_bsdf_socket_name,
            in_or_out="OUTPUT",  
            socket_type="NodeSocketShader"
        ) 

        displace_map_socket_name = "displace_map_socket"
        _ = self.material_editor.get_or_create_group_socket(
            group_name=group_node.name,
            socket_name=displace_map_socket_name,
            in_or_out="OUTPUT",  
            socket_type="NodeSocketVector"
        ) 

        principled_bsdf_node = group_node.node_tree.nodes[principled_bsdf_node_name]
        displace_map_node = group_node.node_tree.nodes[displace_map_node_name]
        group_output_node = group_node.node_tree.nodes["Group Output"]

        group_node.node_tree.links.new(
            principled_bsdf_node.outputs["BSDF"],
            group_output_node.inputs[principled_bsdf_socket_name]
        )   
        group_node.node_tree.links.new(
            displace_map_node.outputs["Displacement"],
            group_output_node.inputs[displace_map_socket_name]
        )   

        info_msg = f"create_texture_group(), create a node group '{group_node.name}'. "
        self.logger.info(info_msg)
        return group_node


    def _extract_base_dirname(
            self, 
            filepath: str=""
        ) -> str:
        path = Path(filepath).resolve()   # Resolve relative paths/aliases (e.g., ~ → /home/user)
        normalized_path = str(path).rstrip(os.sep)  # Remove trailing slashes to avoid empty basename
        path_obj = Path(normalized_path)
        
        # Case 1: Path is a DIRECTORY (exists on disk)
        if path_obj.is_dir():
            return path_obj.name
             
        # Case 2: Path is a FILE (exists on disk)
        elif path_obj.is_file():
            base_filename = path_obj.name
            base_dirname = path_obj.parent.name

            warn_msg = f"extract_filepath(), '{filepath}' is a filename, rather than a directory name as expected. "
            warn_msg += f"We will return the directory '{base_dirname}' of this file."
            self.logger.warning(warn_msg)
            return base_dirname
            
        # Case 3: Path does NOT exist (infer from string structure)
        else:
            warn_msg = f"extract_filepath(), '{filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return ""


    def _set_texture_images(
            self,
            texture_group_node: object=None,
            texture_dirpath: str=""
        ):
        # 1. Get the texture image filepaths.
        texture_files = self.scan_texture_directory(
            texture_dir=texture_dirpath
        ) 

        # 2. Get the prefix of the internal node's name in the group.
        #    referring to create_texture_group()
        dirname = self._extract_base_dirname(
            filepath=texture_dirpath
        )
        texture_node_names = {
            "principled_bsdf_node_name": f"{dirname}_Principled_BSDF", 
            "mapping_node_name": f"{dirname}_Mapping_Node",
            "color_node_name": f"{dirname}_Color_Node",
            "rough_node_name": f"{dirname}_Rough_Node",
            "normal_node_name": f"{dirname}_Normal_Node",
            "normal_map_node_name": f"{dirname}_Normal_Map_Node",
            "metal_node_name": f"{dirname}_Metal_Node",
            "displace_texture_node_name": f"{dirname}_Displace_Texture_Node",
            "displace_map_node_name": f"{dirname}_Displace_Map_Node"
        }

        # 3. Set texture images to the shader nodes.
        if (('color' in texture_files) and
            (len(texture_files['color']) > 0)
            ):
            color_node = texture_group_node.node_tree.nodes[
                texture_node_names["color_node_name"]
            ]
            color_node.image = bpy.data.images.load(texture_files['color'])
            color_node.image.colorspace_settings.name = 'sRGB'
            # color_node.projection = 'BOX'
            # color_node.projection_blend = 0.2

        if (('roughness' in texture_files) and
            (len(texture_files['roughness']) > 0)
            ):
            rough_node = texture_group_node.node_tree.nodes[
                texture_node_names["rough_node_name"]
            ]
            rough_node.image = bpy.data.images.load(texture_files['roughness'])
            rough_node.image.colorspace_settings.name = 'Non-Color'
            # rough_node.projection = 'BOX'
            # rough_node.projection_blend = 0.2

        if (('normal' in texture_files) and 
            (len(texture_files['normal']) > 0)
            ):
            normal_node = texture_group_node.node_tree.nodes[
                texture_node_names["normal_node_name"]
            ]
            normal_map_node = texture_group_node.node_tree.nodes[
                texture_node_names["normal_map_node_name"]
            ]  
            normal_node.image = bpy.data.images.load(texture_files['normal'])
            normal_node.image.colorspace_settings.name = 'Non-Color'
            # normal_node.projection = 'BOX'
            # normal_node.projection_blend = 0.2

        if (('metalness' in texture_files) and
            (len(texture_files['metalness']) > 0)
            ):
            metal_node = texture_group_node.node_tree.nodes[
                texture_node_names["metal_node_name"]
            ]
            metal_node.image = bpy.data.images.load(texture_files['metalness'])
            metal_node.image.colorspace_settings.name = 'Non-Color'
            # metal_node.projection = 'BOX'

        if (('displacement' in texture_files) and
            (len(texture_files['displacement']) > 0)
            ):
            displace_texture_node = texture_group_node.node_tree.nodes[
                texture_node_names["displace_texture_node_name"]
            ]
            displace_map_node = texture_group_node.node_tree.nodes[
                texture_node_names["displace_map_node_name"]
            ]
            displace_texture_node.image = bpy.data.images.load(texture_files['displacement'])
            displace_texture_node.image.colorspace_settings.name = 'Non-Color'
            # displace_texture_node.projection = 'BOX'
            displace_map_node.inputs[0].default_value = 0.0
            displace_map_node.inputs[1].default_value = 0.0
            displace_map_node.inputs[2].default_value = 0.1



    def load_texture(
            self, 
            texture_dirpath: str=""
        ) -> object:
        # 1. Create a node group for these textures
        dirname = self._extract_base_dirname(
            filepath=texture_dirpath
        )
        if len(dirname) == 0:
            warn_msg = f"load_texture(), the input texture_dirpath '{texture_dirpath}' is not valid."
            self.logger.warning(warn_msg)
            return 
        
        self.material_obj.use_nodes = True

        texture_group_node = self.create_texture_group(
            texture_name=dirname
        ) 
        
        # 2. Link the group's output socket to the material's output node.
        output_node = self.material_editor.get_node_or_group(
            node_name="Material Output"
        )
        if output_node is None:
            warn_msg = f"load_texture(), the activate material '{self.material_obj.name}' doesn't have 'Output_Node'."
            self.logger.warning(warn_msg)
            return 
        output_node.location = (200, 0)

        principled_bsdf_socket_name = "principled_bsdf_socket"
        displace_map_socket_name = "displace_map_socket"

        self.material_obj.node_tree.links.new(
            texture_group_node.outputs[principled_bsdf_socket_name],
            output_node.inputs["Surface"]
        )    

        self.material_obj.node_tree.links.new(
            texture_group_node.outputs[displace_map_socket_name],
            output_node.inputs["Displacement"]
        )    

        # 3. Set texture images to the related shader nodes.
        self._set_texture_images(
            texture_group_node=texture_group_node,
            texture_dirpath=texture_dirpath
        )

        # 4. Return the group node
        return texture_group_node



    @staticmethod
    def usage_demo():
        # 1. Clear the scene and create a sample mesh to texture
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
        sample_mesh = bpy.context.active_object
        sample_mesh.name = "DemoFloor"

        # 2. Set up the sun. 
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 3.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (0.0, 0.0, 5.0) 
        bpy.context.collection.objects.link(sun_obj)

        # 3. Create material object
        material_texture = MaterialTexture(
            object_instance=sample_mesh,
            material_name=f"{sample_mesh.name}Material"            
        )

        # 4. Load texture file from directories
        texture_root_directory = f"/home/robot/blender_asset/texture"
        texture_directories = [
            f"{texture_root_directory}/Moss002_2K-JPG",
            f"{texture_root_directory}/WoodFloor043_4K"
        ]

        group_node_y = -100
        for idx, tex_dir in enumerate(texture_directories):  
            group_node = material_texture.load_texture(
                texture_dirpath=tex_dir
            )

            group_node.location = (-200, group_node_y)
            group_node_y += 200