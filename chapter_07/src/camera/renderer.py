import bpy
import os
import sys
import json
from pathlib import Path

class Renderer:
    def __init__(self):
        self.logger = None
        self.scene = None
        self.sequencer = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("Renderer").getLogger()
            self.logger.info(f"Renderer class initialized.")

            self._create_renderer()
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Renderer class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize Renderer class, error message: '{e}'")
 

    def _create_renderer(self):
        self.scene = bpy.context.scene

        # Initialize video sequencer
        if not self.scene.sequence_editor:
            self.scene.sequence_editor_create()
        self.sequencer = self.scene.sequence_editor


    def set_scene_settings(
            self, 
            engine='CYCLES', 
            resolution_x=640, 
            resolution_y=360, 
            samples=32, 
            frame_start=1, 
            frame_end=60
        ):
        """
        Configures the scene's rendering settings.

        Args:
            engine (str): The render engine to use ('CYCLES', 'BLENDER_EEVEE', etc.).
            resolution_x (int): The width of the rendered output in pixels.
            resolution_y (int): The height of the rendered output in pixels.
            samples (int): The number of samples for the render engine, HD=128
            frame_start (int): The starting frame of the animation.
            frame_end (int): The ending frame of the animation.

            The popular resolutions are:
            - 480p: 854 * 480 (16:9)
            - 360p: 640 * 360 (16:9)
            - 720p (HD): 1280 * 720 (16:9)
            - 1080p (Full HD/FHD): 1920 * 1080 (16:9)
            - 720p (HD vertical 9:16): 720 * 1280 
            - 1080p (Full HD Mobile vertical 9:16): 1080 * 1920
        """
        # Set the rendering engine
        self.scene.render.engine = engine
        
        # Set the resolution
        self.scene.render.resolution_x = resolution_x
        self.scene.render.resolution_y = resolution_y
        self.scene.render.resolution_percentage = 100
        
        # Set the frame range
        self.scene.frame_start = frame_start
        self.scene.frame_end = frame_end
        
        # Set render quality settings (for Cycles)
        if engine == 'CYCLES':
            self.scene.cycles.samples = samples
            self.scene.cycles.use_denoising = True
            # Enable feature set for better displacement
            self.scene.cycles.feature_set = 'SUPPORTED'
            # Set displacement method
            self.scene.cycles.displacement_method = 'BOTH'
        elif engine == 'BLENDER_EEVEE':
            # Eevee specific settings can be added here if needed
            pass

        scene_setting = {
            "self.scene.render.engine": self.scene.render.engine,
            "self.scene.render.resolution_x": self.scene.render.resolution_x,
            "self.scene.render.resolution_y": self.scene.render.resolution_y,
            "self.scene.render.resolution_percentage": self.scene.render.resolution_percentage,
            "self.scene.frame_start": self.scene.frame_start,
            "self.scene.frame_end": self.scene.frame_end
        }

        scene_setting_str = json.dumps(scene_setting, indent=2, ensure_ascii=False)
        self.logger.info(f"Set the rendering engine's scene settings. ")
        self.logger.debug(scene_setting_str)


    def set_output_settings(
            self, 
            output_path="render_output", 
            file_format="PNG", 
            video_codec="", 
            container="",
            fps = 30
        ):
        """
        Configures the output path, file format, and codec.

        Args:
            output_path (str): The full path for the output file or image sequence.
            file_format (str): The file format ('FFMPEG', 'PNG', 'JPEG', etc.).
            video_codec (str): The video codec ('MPEG4', 'H264', etc.).
            container (str): The video container ('MPEG4', 'AVI', 'QUICKTIME', 'DV', 'OGG', 'MKV', 'FLASH', 'WEBM').
        """
        # Ensure the output directory exists
        if output_path.startswith("./"):
            output_path = output_path[2:]
        
        if not output_path.startswith("/"):
            output_path = f"{os.getcwd()}/{output_path}"
        if output_path.endswith("/"):
            output_path = output_path[:-1]

        if output_path and not os.path.exists(output_path):
            os.makedirs(output_path)
            
        self.scene.render.fps = fps
        self.scene.render.fps_base = 1.0
        self.scene.render.image_settings.file_format = file_format

        if file_format == 'FFMPEG':
            self.scene.render.filepath = f"{output_path}/video_"
        else:
            self.scene.render.filepath = f"{output_path}/image_"

        output_setting = {
            "self.scene.render.filepath": self.scene.render.filepath,
            "self.scene.render.image_settings.file_format": self.scene.render.image_settings.file_format,
            "self.scene.render.fps": self.scene.render.fps,
            "self.scene.render.fps_base": self.scene.render.fps_base       
        }
        
        if file_format == 'FFMPEG':
            self.scene.render.ffmpeg.codec = video_codec
            self.scene.render.ffmpeg.format = container
            
            output_setting["self.scene.render.ffmpeg.codec"] = self.scene.render.ffmpeg.codec
            output_setting["self.scene.render.ffmpeg.format"] = self.scene.render.ffmpeg.format
        
        output_setting_str = json.dumps(output_setting, indent=2, ensure_ascii=False)
        self.logger.info(f"Set the rendering engine's output settings. ")
        self.logger.debug(output_setting_str)  


    def start_rendering(self):
        """
        Renders the animation as a sequence of images.
        """
        self.logger.info("Starting renderring process...")

        # Check if there's an active camera in the scene
        # if not self.scene.camera:
        #    self.logger.error("No active camera found in the scene. Cannot render.")
        #    return

        """
        rendering_setting = {
            "render.engine": bpy.context.scene.render.engine,
            "render.resolution_x": bpy.context.scene.render.resolution_x,
            "render.resolution_y": bpy.context.scene.render.resolution_y,
            "render.resolution_percentage": bpy.context.scene.render.resolution_percentage,
            "scene.frame_start": bpy.context.scene.frame_start,
            "scene.frame_end": bpy.context.scene.frame_end,
            "scene.filepath": bpy.context.scene.render.filepath,
            "scene.file_format": bpy.context.scene.render.image_settings.file_format,
            "scene.fps": bpy.context.scene.render.fps,
            "scene.fps_base": bpy.context.scene.render.fps_base,
            "ffmpeg.codec": bpy.context.scene.render.ffmpeg.codec,
            "ffmpeg.format": bpy.context.scene.render.ffmpeg.format      
        }
        rendering_msg = f"All the scene and renderer setting before starting the rendering: \n"
        setting_str = json.dumps(rendering_setting, indent=2, ensure_ascii=False)
        rendering_msg += setting_str
        self.logger.debug(rendering_msg)        
        """

        try:
            bpy.ops.render.render(animation=True)
            self.logger.info("Rendering process completed.")
        except Exception as e: 
            self.logger.error(f"start_rendering() threw an exception: '{str(e)}'")     


    def render_frame_images(self, output_path="frame_images"):
        # Rendering images for all frames.
        self.logger.info("render_frame_images(): Starting renderring frames to image series...")
        self.set_output_settings(
            output_path=output_path, 
            file_format="PNG"
        )

        self.start_rendering() 


    def _import_image_sequence(self, input_images_dir="frame_images", image_extension="png", frame_duration=1):
        """
        Import image sequence into video sequencer
        :param image_extension: File extension of images (png, jpg, etc.)
        :param frame_duration: How many frames each image should display
        """

        if len(input_images_dir) == 0:
            input_images_dir = self.scene.render.filepath
        self.logger.info(f"_import_image_sequence(): images_dir='{input_images_dir}'")

        # Get sorted list of image files
        images_path = Path(input_images_dir).resolve()
        image_files = sorted(images_path.glob(f"*.{image_extension}"))
  
        # Add each image to sequencer
        current_frame = self.scene.frame_start       
        for img_path in image_files:
            # Create image strip
            strip = self.sequencer.sequences.new_image(
                name=img_path.stem,
                filepath=str(img_path),
                channel=1,
                frame_start=current_frame
            )
            
            # Set strip duration
            strip.frame_final_duration = frame_duration
            
            # Move to next frame position
            current_frame += frame_duration

        # Set scene frame range to match sequence length
        self.scene.frame_start = 1
        self.scene.frame_end = current_frame - 1


    def compile_images_to_video(
            self, 
            input_images_dir="frame_images", 
            output_video_dir="render_output",
            image_extension="png", 
            frame_duration=1, 
            fps = 30
        ):
        self.logger.info("compile_images_to_video(): Compiling the image series into video...")

        self._import_image_sequence(
            input_images_dir=input_images_dir, 
            image_extension="png", 
            frame_duration=1
        )

        self.set_output_settings(
            output_path=output_video_dir,
            file_format="FFMPEG", 
            video_codec="H264", 
            container="MPEG4",
            fps = fps
        )

        self.start_rendering()    
        self.logger.info(f" Successfully generated a video stored in directory '{output_video_dir}'")         


    def set_image_settings(
            self,             
            engine='CYCLES', 
            file_format="PNG", 
            resolution_x=640, 
            resolution_y=360, 
            samples=32
        ):
        """
        Set the Blender rendering engine setting to prepare the rendering of a PNG image.

        Args:
            engine (str): The render engine to use ('CYCLES', 'BLENDER_EEVEE', etc.)
            file_format (str): The format of the image file, ('PNG', 'JPG', etc)
            resolution_x (int): The width of the rendered output in pixels.
            resolution_y (int): The height of the rendered output in pixels.
            samples (int): The number of samples for the render engine, HD=128

            The popular resolutions are:
            - 480p: 854 * 480 (16:9)
            - 360p: 640 * 360 (16:9)
            - 720p (HD): 1280 * 720 (16:9)
            - 1080p (Full HD/FHD): 1920 * 1080 (16:9)
            - 720p (HD vertical 9:16): 720 * 1280 
            - 1080p (Full HD Mobile vertical 9:16): 1080 * 1920
        """      
        # Get the scene
        self.scene = bpy.context.scene
        
        # Set render engine to Cycles
        self.scene.render.engine = engine        
        if engine == 'CYCLES':
            self.scene.cycles.samples = samples
            self.scene.cycles.use_denoising = True
            # Enable feature set for better displacement
            self.scene.cycles.feature_set = 'SUPPORTED'
            # Set displacement method
            self.scene.cycles.displacement_method = 'BOTH'
        elif engine == 'BLENDER_EEVEE':
            # Eevee specific settings can be added here if needed
            pass

        # Configure Cycles settings
        cycles = self.scene.cycles
        cycles.samples = samples  # Higher = better quality, slower
        cycles.preview_samples = 16  # Faster preview samples
        cycles.use_denoising = True  # Enable denoising for cleaner results
        cycles.film_exposure = 1.2  # Slight exposure adjustment
        
        # Set resolution
        self.scene.render.resolution_x = resolution_x
        self.scene.render.resolution_y = resolution_y
        self.scene.render.resolution_percentage = 100  # Use full resolution
        
        # Set output format and path
        if file_format == 'PNG':
            self.scene.render.image_settings.color_mode = 'RGBA'  # Include alpha channel for PNG
        elif file_format == 'JPEG':
            self.scene.render.image_settings.color_mode = 'RGB'  # JPG doesn't have alpha channel
        else:
            self.logger.warn(f"For the time being, we only support 'PNG' and 'JPEG', not including '{file_format}'")
            self.scene.render.image_settings.color_mode = 'RGB'
            
        self.scene.render.image_settings.file_format = file_format  # Can be 'PNG', 'JPEG', 'OPEN_EXR', etc.
        self.scene.render.image_settings.compression = 15  # PNG compression (0-100)

        info_msg = f"set_scene_settings(): Rendering with Cycles, \n\t"
        info_msg += f"Resolution: {resolution_x}x{resolution_y}, Samples: {samples}."
        self.logger.info(info_msg)



    def render_single_images(
            self, 
            image_output_filename=""
        ):
        """
        Rendering the Blender scene into a PNG image.

        Args:
            image_output_filename (str): a file directory and name to output the png image.
            engine (str): The render engine to use ('CYCLES', 'BLENDER_EEVEE', etc.).
            resolution_x (int): The width of the rendered output in pixels.
            resolution_y (int): The height of the rendered output in pixels.
            samples (int): The number of samples for the render engine, HD=128

            The popular resolutions are:
            - 480p: 854 * 480 (16:9)
            - 360p: 640 * 360 (16:9)
            - 720p (HD): 1280 * 720 (16:9)
            - 1080p (Full HD/FHD): 1920 * 1080 (16:9)
            - 720p (HD vertical 9:16): 720 * 1280 
            - 1080p (Full HD Mobile vertical 9:16): 1080 * 1920
        """        
        # Ensure output directory exists
        output_dir = os.path.dirname(image_output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        self.scene.render.filepath = image_output_filename

        # Start rendering
        bpy.ops.render.render(write_still=True)
        
        info_msg = f"render_single_images(): Output will be saved to: '{image_output_filename}'."
        self.logger.info(info_msg)


    @staticmethod
    def run_demo():
        bpy.ops.object.camera_add(location=(10, -10, 5))
        bpy.context.object.name = "Camera4Renderer"
        bpy.context.scene.camera = bpy.context.object
    
        demo_rendering_engine = Renderer()
        demo_rendering_engine.set_scene_settings()

        demo_rendering_engine.render_frame_images(
            output_path="tmp_frame_img"
        )
        demo_rendering_engine.compile_images_to_video(
            input_images_dir="tmp_frame_img",
            output_video_dir="video_output/"
        )


if __name__ == "__main__":
    Renderer.run_demo()