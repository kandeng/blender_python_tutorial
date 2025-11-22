import os
import sys
import json
import time
import bpy
from pathlib import Path


class ImageVideoProjector:
    """
    To retrieve objects from the engon polygoniq addon library, 
    and control its properties.
    """
    def __init__(self):
        self.logger = None

        self.screen_object = None
        self.editor_node = None 

        self.video_editor = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Assembling").getLogger()
            self.logger.info(f"ImageVideoProjector class initialized.")

            from modeling.editor_node import EditorNode
            self.editor_node = EditorNode(
                editor_name="",
                editor_type="MATERIAL",
                obj=None
            )

            from video_editing.video_editor import VideoEditor
            self.video_editor = VideoEditor()

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not import the classes that ImageVideoProjector depends on, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not import the classes that ImageVideoProjector depends on, error message: '{str(e)}'")


    def create_screen(
            self,
            screen_name: str="",
            screen_scale: tuple=(1.0, 1.0, 1.0)
        ) -> None:
        # Create a mesh plane object
        try:
            bpy.ops.mesh.primitive_plane_add(
                size=2.0,  # Size of the plane (2x2 meters by default)
                enter_editmode=False,
                align='WORLD', # Align the object to world axes
                location=(0.0, 0.0, 0.0)
            )

            if bpy.context.object and bpy.context.object.type == 'MESH':
                bpy.context.object.name = screen_name   
                bpy.context.object.scale = screen_scale   

            info_msg = f"create_screen(), create a mesh plane object used for the screen to display a video clip, "
            info_msg += f"screen_name='{screen_name}', screen_scale='{screen_scale}'."
            self.logger.info(info_msg)

            return bpy.context.object
        except Exception as e:
            warn_msg = f"create_screen(), Could not add a plane to the 'bpy.context.objects', the error message is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return None


    def get_screen(
            self,
            screen_name: str="",
        ) -> object:
        screen_instance = None
        try:
            for obj_instance in bpy.data.objects:
                if screen_name.lower() in obj_instance.name.lower():
                    screen_instance = obj_instance
                    break

            info_msg = f"get_screen(), given the screen names: '{screen_name}', "
            info_msg += f"find the related objects in 'bpy.data.objects': '{screen_instance.name}'."
            self.logger.info(info_msg)

            return screen_instance
        except Exception as e:
            warn_msg = f"get_screen(), the following exception is thrown "
            warn_msg += f"when get '{screen_name}' from 'bpy.data.objects': '{str(e)}'"
            self.logger.warning(warn_msg)
            return None
        

    def create_screen_material(
            self,
            filepath: str=""
        ) -> object:
        filename_with_suffix = os.path.basename(filepath)
        filename, _ = os.path.splitext(filename_with_suffix)
        material_name = f"{filename}_material_{int(time.time()*1000)}"  # Add timestamp for uniqueness

        try:
            # Clear existing materials
            if self.screen_object.data.materials:
                self.screen_object.data.materials.clear()     

            # Create a new unique material
            material_obj = bpy.data.materials.new(name=material_name)
            material_obj.use_nodes = True
            self.screen_object.data.materials.append(material_obj)            

            # Set the node tree for this specific material
            self.editor_node.node_tree = material_obj.node_tree
    
            info_msg = f"create_screen_material(), create a material '{material_obj.name}' "
            info_msg += f"for screen_object '{self.screen_object.name}'."
            self.logger.info(info_msg)

            return material_obj
        
        except Exception as e:
            warn_msg = f"create_screen_material(), when creating the material for the screen '{self.screen_object.name}', "
            warn_msg += f"following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return None



    def load_image_video(
            self,
            filepath: str=""
        ) -> object:
        """
        Given an image or a video filepath, load it into 'bpy.data.images' 

        Args:
            filepath (str): A filepath of an image file or a video file.
                The valid filename suffices are '.png', '.jpg', '.jpeg', '.tif', '.exr' and '.mov', '.mp4', '.mkv'.

        Returns: 
            The 'bpy.data.images' object that contains the image or video content.
        """
        if not os.path.exists(filepath):
            warn_msg = f"load_image_video(), '{filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return None

        # Check if the image datablock already exists (avoid duplicates)
        file_basename = os.path.basename(filepath)
        try:
            # Create a unique name for each video to prevent conflicts
            unique_name = f"{file_basename}_{int(time.time()*1000)}"
            
            # Always create a new image datablock to ensure isolation
            media_data_object = bpy.data.images.load(
                filepath=filepath,
                check_existing=False  # Force creation of a new datablock
            )
            # Rename to our unique name
            media_data_object.name = unique_name

            info_msg = f"load_image_video(), load the content of '{filepath}' to 'bpy.data.images' with unique name '{unique_name}'."
            self.logger.info(info_msg)
            return media_data_object

        except Exception as e:
            warn_msg = f"load_image_video(), when loading image or video from file '{filepath}', "
            warn_msg += f"following exception was thrown: '{str(e)}'."
            self.logger.warning(warn_msg)
            return None


    def create_material_nodes(
            self,
            filepath: str=""
        ):
        # Get the file_basename 
        filename_with_suffix = os.path.basename(filepath)
        file_basename, _ = os.path.splitext(filename_with_suffix)
    
        # Clear default nodes
        self.editor_node.node_tree.nodes.clear()

        # Load the image/video into 'bpy.data.images'
        video_data_object = self.load_image_video(filepath)
        if video_data_object is None:
            warn_msg = f"create_material_nodes(), failed to load video '{filepath}'."
            self.logger.warning(warn_msg)
            return

        # Create the image texture node and set its properties.
        video_texture_node_name = "Video_Texture"  
        video_texture_node = self.editor_node.create_node(
            node_type='ShaderNodeTexImage',  
            node_name=f"{video_texture_node_name}_{file_basename}",
            location=(-400, 0)
        )        
        video_texture_node.image = video_data_object

        if video_data_object.source == 'MOVIE':
            video_texture_node.image_user.frame_duration = video_data_object.frame_duration
            video_texture_node.image_user.use_auto_refresh = True
            video_texture_node.image_user.use_cyclic = True
            video_texture_node.image_user.frame_current = 1
        elif video_data_object.source == 'FILE':
            video_texture_node.image_user.frame_duration = 1
            video_texture_node.image_user.use_auto_refresh = False
            video_texture_node.image_user.use_cyclic = False
            video_texture_node.image_user.frame_current = 1        

        # Create the main Principled BSDF and the material output nodes.
        principled_bsdf_node_name = "Principled_BSDF"  
        principled_bsdf_node = self.editor_node.create_node(
            node_type='ShaderNodeBsdfPrincipled', 
            node_name=f"{principled_bsdf_node_name}_{file_basename}",
            location=(0, 0)
        )

        material_output_node_name = "Material_Output"  # Use the expected name
        material_output_node = self.editor_node.create_node(
            node_type='ShaderNodeOutputMaterial',
            node_name=f"{material_output_node_name}_{file_basename}",
            location=(300, 0)
        )

        # Create texture coordinate and mapping nodes for texture transformations
        tex_coord_node_name = "Texture_Coordinate"
        tex_coord_node = self.editor_node.create_node(
            node_type='ShaderNodeTexCoord',
            node_name=f"{tex_coord_node_name}_{file_basename}",
            location=(-800, 0)
        )

        mapping_node_name = "UV_Mapping"  # This is what the code is looking for
        mapping_node = self.editor_node.create_node(
            node_type='ShaderNodeMapping',
            node_name=f"{mapping_node_name}_{file_basename}",
            location=(-600, 0)
        )

        # Link the texture coordinate to the mapping node
        if tex_coord_node and mapping_node:
            self.editor_node.create_link(
                from_node_output=tex_coord_node.outputs['UV'],  # UV output
                to_node_input=mapping_node.inputs['Vector']   # Vector input
            )

        # Link the mapping node to the video texture node
        if mapping_node and video_texture_node:
            self.editor_node.create_link(
                from_node_output=mapping_node.outputs[0],  # Vector output
                to_node_input=video_texture_node.inputs[0]   # Vector input
            )

        # Link the video texture node to the principled bsdf_node 
        if video_texture_node and principled_bsdf_node:
            self.editor_node.create_link(
                from_node_output=video_texture_node.outputs['Color'],  # Color output
                to_node_input=principled_bsdf_node.inputs['Base Color']   # Base Color input
            )

        # Link the principled bsdf_node to the material output node
        if principled_bsdf_node and material_output_node:
            self.editor_node.create_link(
                from_node_output=principled_bsdf_node.outputs['BSDF'],  # BSDF output
                to_node_input=material_output_node.inputs['Surface']   # Surface input
            )

        info_msg = f"create_material_nodes(), Base texture_shader nodes created for video '{filepath}'."
        self.logger.info(info_msg)



    def project_image_video_to_screen(
            self,
            filepath: str=""
        ):
        """
        video_metadata = {
            "resolution_x": int(video_obj.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "resolution_y": int(video_obj.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": video_obj.get(cv2.CAP_PROP_FPS),
            "codec_fourcc": int(video_obj.get(cv2.CAP_PROP_FOURCC)),
            "format_id": int(video_obj.get(cv2.CAP_PROP_FORMAT)),
            "frame_count": int(video_obj.get(cv2.CAP_PROP_FRAME_COUNT))
        }        
        """
        # 1. Get the video's metadata and filename.
        video_metadata = self.video_editor.get_video_metadata(filepath)
        # Assume the pixel per millimeter is 3.75 px/mm
        video_frame_size = (
            video_metadata["resolution_x"] / 3.75,
            video_metadata["resolution_y"] / 3.75,
        )
        scale_factor = 0.02
        screen_scale = [dim * scale_factor for dim in (*video_frame_size, 1.0)]

        filename_with_suffix = os.path.basename(filepath)
        filename, _ = os.path.splitext(filename_with_suffix)

        # 2. Create a mesh plane object as the screen.
        self.screen_object = self.create_screen(
            screen_name=f"{filename}_screen",
            screen_scale=screen_scale
        )

        # 3. Create the material/shader nodes.
        material_obj = self.create_screen_material(
            filepath=filepath
        )
        self.editor_node.node_tree = material_obj.node_tree

        self.create_material_nodes(
            filepath=filepath
        )



    def control_panel(
            self, 
            screen_location: tuple=(0.0, 0.0, 0.0),
            screen_scale: tuple=(1.0, 1.0, 1.0),
            screen_rotation: tuple=(0.0, 0.0, 0.0),
            is_cyclic: bool=False,     # cyclic playback the video clip
        ):
        pass



    @staticmethod
    def usage_demo():
        project_dir = f"/home/robot/llamedia_studio_20251106/testing"
        input_video_filepaths = [
            f"{project_dir}/input/kdeng_greenscreen.mov",
            f"{project_dir}/input/nyu_corridor.MOV",
            f"{project_dir}/input/TrueStory.mp4",
            f"{project_dir}/input/bicycling_greenscreen.webm",
            f"{project_dir}/input/opera_house_inside.jpeg",
            f"{project_dir}/input/battle_field.png"
        ]

        # Keep track of screen positions to avoid overlap
        screen_positions = [
            (-3, 0, 0),  # First screen to the left
            (3, 0, 0)    # Second screen to the right
        ]
        
        for i, filepath in enumerate(input_video_filepaths[4:]):
            image_video_projector = ImageVideoProjector()
            image_video_projector.project_image_video_to_screen(
                filepath=filepath
            )
        
            image_video_projector.control_panel(
                screen_location=screen_positions[i],
                # screen_scale=(1.0, 1.0, 1.0),
                screen_rotation=(0.0, 0.0, 0.0),
                is_cyclic=False,     # cyclic playback the video clip
            )