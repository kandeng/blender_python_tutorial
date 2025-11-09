import os
import sys
import bpy
import math
import numpy as np


class Sky:
    """
    A class to use HDRI image as sky and apply sky_texture to adjust the lighting.
    """
    def __init__(self):
        self.logger = None
        self.editor_node = None
        
        try:
            from logger.logger import Logger
            self.logger = Logger("Landscape").getLogger()
            self.logger.info(f"Sky class initialized.")

            from modeling.editor_node import EditorNode
            self.editor_node = EditorNode(
                editor_name="WorldSky", 
                editor_type="WORLD", 
                obj=None
            )

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Sky class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize Sky class, error message: '{str(e)}'")


    def create_sky_hdri(
            self,
            hdri_filepath: str=""
        ):  
        output_node = self.editor_node.create_node(
            node_type='ShaderNodeOutputWorld', 
            node_name="WorldOutput",
            location=(900, 300)
        )     
        background_node = self.editor_node.create_node(
            node_type='ShaderNodeBackground', 
            node_name="WorldBackground",
            location=(300, 300)
        )  

        hdri_node = self.editor_node.create_node(
            node_type='ShaderNodeTexEnvironment', 
            node_name="WorldSky", 
            location=(0, 300)
        )     
        try:
            hdri_image = bpy.data.images.load(hdri_filepath)
            hdri_node.image = hdri_image
        except Exception as e:
            warn_msg = f"create_sky_hdri(), Could not load HDRI file: {hdri_filepath}, "
            warn_msg += f"the error message is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return

        mapping_node = self.editor_node.create_node(
            node_type='ShaderNodeMapping', 
            node_name="WorldMapping", 
            location=(-300, 300)
        )   
        coordinator_node = self.editor_node.create_node(
            node_type='ShaderNodeTexCoord', 
            node_name="WorldCoordinator", 
            location=(-600, 300)
        )  
        
        self.editor_node.create_link(
            from_node_output=background_node.outputs[0], 
            to_node_input=output_node.inputs[0]
        )
        self.editor_node.create_link(
            from_node_output=hdri_node.outputs[0], 
            to_node_input=background_node.inputs[0]
        )
        self.editor_node.create_link(
            from_node_output=mapping_node.outputs[0], 
            to_node_input=hdri_node.inputs[0]
        )
        self.editor_node.create_link(
            from_node_output=coordinator_node.outputs[0], 
            to_node_input=mapping_node.inputs[0]
        )


    def create_sky_lighting(self):
        mix_shader_node = self.editor_node.create_node(
            node_type='ShaderNodeMixShader', 
            node_name="SkyMixShader",
            location=(600, 0)
        )  
        sky_background_node = self.editor_node.create_node(
            node_type='ShaderNodeBackground', 
            node_name="SkyBackground",
            location=(300, 0)
        )  
        sky_node = self.editor_node.create_node(
            node_type='ShaderNodeTexSky', 
            node_name="SkyTexture",
            location=(0, 0)
        )  
        sky_node.sun_elevation = math.radians(-10)
        sky_node.sun_rotation = math.radians(-20)

        lighting_node = self.editor_node.create_node(
            node_type='ShaderNodeLightPath', 
            node_name="LightingPath",
            location=(0, -300)
        )  

        hdri_background_node = self.editor_node.get_node("WorldBackground")
        world_output_node = self.editor_node.get_node("WorldOutput")

        self.editor_node.create_link(
            from_node_output=mix_shader_node.outputs[0], 
            to_node_input=world_output_node.inputs[0]
        )
        self.editor_node.create_link(
            from_node_output=lighting_node.outputs[0], 
            to_node_input=mix_shader_node.inputs[0]
        )
        self.editor_node.create_link(
            from_node_output=sky_background_node.outputs[0], 
            to_node_input=mix_shader_node.inputs[1]
        )
        self.editor_node.create_link(
            from_node_output=hdri_background_node.outputs[0], 
            to_node_input=mix_shader_node.inputs[2]
        )
        self.editor_node.create_link(
            from_node_output=sky_node.outputs[0], 
            to_node_input=sky_background_node.inputs[0]
        )


    def get_sun_angles(
            self,
            hdri_filepath: str=""
        ):  
        """
        Calculate sun Elevation (X-rotation, sun_elevation) and Azimuth (Z-rotation, sun_rotation) from an HDRI.
        Notice: The result is not very accurate. 
        
        Args:
            hdri_filepath (str): Path to the HDRI image (.hdr, .exr, etc.)
            
        Returns:
            tuple: (azimuth_deg, elevation_deg) in degrees. 
            To convert degree to radian, use 'radian = math.radians(degree)'
        """
        # Load the HDRI image
        hdri_image = None
        try:
            hdri_image = bpy.data.images.load(hdri_filepath)
        except Exception as e:
            warn_msg = f"get_sun_angles(), Could not load HDRI file: {hdri_filepath}, "
            warn_msg += f"the error message is: '{str(e)}'."
            self.logger.warning(warn_msg)
            return 0, 0

        # Check if image is valid
        hdri_width, hdri_height = hdri_image.size  # (width, height) as a tuple
        if (not hdri_image.pixels) or (hdri_width == 0) or (hdri_height == 0):
            warn_msg = f"get_sun_angles(), DRI image is empty or invalid."
            self.logger.warning(warn_msg)
            return 0, 0
        
        # Convert pixel data to a numpy array (RGBA)
        # Pixels are stored as a flat list: [r0, g0, b0, a0, r1, g1, b1, a1, ...]
        pixel_data = np.array(hdri_image.pixels, dtype=np.float32)
        pixel_data = pixel_data.reshape((hdri_height, hdri_width, 4))  # (height, width, RGBA)

        # Flip vertically since Blender uses bottom-left origin but we need top-left for calculations
        pixel_data = np.flipud(pixel_data)
        
        
        # Calculate luminance for each pixel (perceived brightness)
        # Luminance formula: Y = 0.2126*R + 0.7152*G + 0.0722*B
        luminance = 0.2126 * pixel_data[..., 0] + 0.7152 * pixel_data[..., 1] + 0.0722 * pixel_data[..., 2]
        
        # Find coordinates of the brightest pixel (max luminance)
        max_lum_idx = np.unravel_index(np.argmax(luminance), luminance.shape)
        y_pixel, x_pixel = max_lum_idx  # (row, column) in image coordinates
        
        # Convert pixel coordinates to UV coordinates (normalized 0-1)
        # UV origin (0,0) is bottom-left of the image
        u = x_pixel / (hdri_width - 1)    # Horizontal UV (0 = left, 1 = right)
        v = y_pixel / (hdri_height - 1)   # Vertical UV (0 = bottom, 1 = top)
        
        # Convert UVs to spherical coordinates (azimuth and elevation)
        # ---------------------------
        # Azimuth (rotation around Z-axis):
        # - UV u ranges 0-1 → maps to 0-360° (azimuth)
        # - Blender's Z-rotation increases clockwise (matches compass direction)
        azimuth_rad = 2 * math.pi * u  # 0 to 2π radians
        azimuth_deg = math.degrees(azimuth_rad) % 360  # 0 to 360 degrees
        
        # Elevation (rotation around X-axis):
        # - UV v ranges 0-1 → maps to -90° (bottom edge) to +90° (top edge)
        # - Blender's X-rotation: 0° = horizontal, 90° = straight up
        elevation_rad = math.pi * (v - 0.5)  # -π/2 to +π/2 radians
        elevation_deg = 90 - math.degrees(elevation_rad)  # Convert to Blender's X-rotation
        
        info_msg = f"get_sun_angles(), elevation_deg={elevation_deg}, azimuth_deg={azimuth_deg}"
        self.logger.info(info_msg)
        return elevation_deg, azimuth_deg


    def align_sky_hdri(
            self,
            hdri_filepath: str=""
        ):  
        self.create_sky_hdri(hdri_filepath=hdri_filepath)
        self.create_sky_lighting()

        elevation_deg, azimuth_deg = self.get_sun_angles(hdri_filepath)      
        sky_node = self.editor_node.get_node(node_name="SkyTexture")  
        sky_node.sun_elevation = math.radians(elevation_deg)
        sky_node.sun_rotation = math.radians(azimuth_deg)


    @staticmethod
    def usage_demo():
        hdri_filepaths=[
            "/home/robot/blender_asset/hdri/kloppenheim_06_4k.exr",
            "/home/robot/blender_asset/hdri/sunny_country_road_2k.exr"
        ]

        sky_hdri = Sky()
        sky_hdri.align_sky_hdri(hdri_filepath=hdri_filepaths[1])


