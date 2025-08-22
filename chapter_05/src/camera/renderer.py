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


    def set_scene_settings(self, engine='CYCLES', 
                           resolution_x=640, resolution_y=360, samples=32, 
                           frame_start=1, frame_end=60
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


    def set_output_settings(self, output_path="render_output", 
                            file_format="PNG", 
                            video_codec="", container="",
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


    def operate_rendering(self):
        """
        Renders the animation as a sequence of images.
        """
        self.logger.info("Starting renderring process...")

        # Check if there's an active camera in the scene
        if not self.scene.camera:
            self.logger.error("No active camera found in the scene. Cannot render.")
            return

        try:
            bpy.ops.render.render(animation=True)
            self.logger.info("Rendering process completed.")
        except Exception as e: 
            self.logger.error(f"operate_rendering() threw an exception: '{str(e)}'")     


    def render_frame_images(self, output_path="frame_images"):
        # Rendering images for all frames.
        self.logger.info("render_frame_images(): Starting renderring frames to image series...")
        self.set_output_settings(
            output_path=output_path, 
            file_format="PNG"
        )

        self.operate_rendering() 


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
            self.logger.debug(f"img_path:'{img_path}', img_path.stem: '{img_path.stem}'")

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


    def compile_images_to_video(self, 
                                input_images_dir="frame_images", image_extension="png", frame_duration=1,
                                output_video_dir="render_output"):
        self.logger.info("compile_images_to_video(): Compiling the image series into video...")

        self._import_image_sequence(
            input_images_dir=input_images_dir, image_extension="png", frame_duration=1
            )

        self.set_output_settings(
            output_path=output_video_dir,
            file_format="FFMPEG", video_codec="H264", container="MPEG4"
            )

        self.operate_rendering()    
        self.logger.info(f" Successfully generated a video stored in directory '{output_video_dir}'")         



    @staticmethod
    def run_demo():
        bpy.ops.object.camera_add(location=(10, -10, 5))
        bpy.context.object.name = "Camera4Renderer"
        bpy.context.scene.camera = bpy.context.object
    
        demo_rendering_engine = Renderer()
        demo_rendering_engine.set_scene_settings()

        # file_format (str): The file format ('FFMPEG', 'PNG', 'JPEG', etc.).
        # video_codec (str): The video codec ('MPEG4', 'H264', etc.).
        # container (str): The video container ('MPEG4', 'MKV', etc.).

        """
        # Directly render mp4 video.
        demo_rendering_engine.set_output_settings(
            output_path="./render_output/", 
            file_format="PNG"
            )

        demo_rendering_engine.set_output_settings(
            output_path="./render_output/",
            file_format="FFMPEG", video_codec="H264", container="MPEG4"
            )
            
        demo_rendering_engine.operate_rendering()        
        """

        demo_rendering_engine.render_frame_images(
            output_path="tmp_frame_img"
            )
        demo_rendering_engine.compile_images_to_video(
            input_images_dir="tmp_frame_img",
            output_video_dir="video_output/"
            )


if __name__ == "__main__":
    Renderer.run_demo()