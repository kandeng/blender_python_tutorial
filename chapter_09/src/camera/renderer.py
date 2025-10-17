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

            self.create_renderer()
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Renderer class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize Renderer class, error message: '{e}'")
 

    def create_renderer(self):
        self.scene = bpy.context.scene

        # Initialize video sequencer
        if not self.scene.sequence_editor:
            self.scene.sequence_editor_create()
        self.sequencer = self.scene.sequence_editor


    def set_scene_settings(
            self, 
            resolution_x=0, 
            resolution_y=0, 
            samples=0, 
            frame_start=0, 
            frame_end=0
        ):
        """
        Configures the scene's rendering settings.

        Args:
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
        self.scene.render.engine = 'CYCLES'
        self.scene.cycles.feature_set = 'SUPPORTED'
        self.scene.cycles.displacement_method = 'BOTH'
        self.scene.cycles.preview_samples = 16  # Faster preview samples
        self.scene.cycles.use_denoising = True  # Enable denoising for cleaner results
        self.scene.cycles.film_exposure = 1.2  # Slight exposure adjustment

        if samples > 0:
            self.scene.cycles.samples = samples  # Higher = better quality, slower
    
        # Set the resolution if necessary, otherwise, use the scene's current settings.
        if resolution_x > 0:
            self.scene.render.resolution_x = resolution_x
        if resolution_y > 0:
            self.scene.render.resolution_y = resolution_y
        self.scene.render.resolution_percentage = 100
        
        # Set the frame range
        if frame_start > 0:
            self.scene.frame_start = frame_start
        if frame_end > 0:
            self.scene.frame_end = frame_end
    
        if samples <= 0:
            samples = 32 

        scene_setting = {
            "self.scene.render.engine": self.scene.render.engine,
            "self.scene.render.resolution_x": self.scene.render.resolution_x,
            "self.scene.render.resolution_y": self.scene.render.resolution_y,
            "self.scene.render.resolution_percentage": self.scene.render.resolution_percentage,
            "self.scene.frame_start": self.scene.frame_start,
            "self.scene.frame_end": self.scene.frame_end
        }

        scene_setting_str = json.dumps(scene_setting, indent=2, ensure_ascii=False)
        self.logger.info(f"set_scene_settings(), set the rendering engine's scene settings.")
        self.logger.debug(scene_setting_str)


    def set_filepath_setting(
            self, 
            file_name=""
        ):
        """
        Configures the renderer's filepath settings.

        Args:
            file_name (str): The full path for the output file.
        """        
        if len(file_name) == 0:
            warn_msg = f"set_filepath_setting(), you need to specify the output filename with directory."
            self.logger.warn(warn_msg)
            return
    
        output_dir = os.path.dirname(file_name)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.scene.render.filepath = file_name
        self.scene.render.use_placeholder = False
        self.scene.render.use_file_extension = False

        output_setting = {
            "self.scene.render.filepath": self.scene.render.filepath,
            "self.scene.render.use_placeholder": self.scene.render.use_placeholder,
            "self.scene.render.use_file_extension": self.scene.render.use_file_extension
        }
        
        output_setting_str = json.dumps(output_setting, indent=2, ensure_ascii=False)
        self.logger.info(f"set_filepath_setting(), set the rendering engine's output filepath settings.")
        self.logger.debug(output_setting_str)  


    def start_rendering(self):
        """
        Renders the animation as a sequence of images.
        """
        # Check if there's an active camera in the scene
        if not self.scene.camera:
            warn_msg = f"start_rendering(), no active camera found in the scene. Cannot render."
            self.logger.warn(warn_msg)

        try:
            self.logger.info(f"start_rendering(), rendering '{self.scene.render.filepath}' starts...")
            bpy.ops.render.render(animation=True)
            self.logger.info(f"start_rendering(), rendering '{self.scene.render.filepath}' completed.")
        except Exception as e: 
            self.logger.error(f"start_rendering() threw an exception: '{str(e)}'")     


    def set_image_settings(
            self,    
            file_name="",         
            file_format="PNG", 
            resolution_x=0, 
            resolution_y=0, 
            samples=0
        ):
        """
        Set the Blender rendering engine setting to prepare the rendering of a PNG image.

        Args:
            file_name (str): The full path for the output file.
            file_format (str): The format of the image file, the valid value is ('PNG', 'JPEG')
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
        # 1. Set the scene
        self.set_scene_settings(
            resolution_x=resolution_x, 
            resolution_y=resolution_y, 
            samples=samples, 
            frame_start=0, 
            frame_end=0   # Using scene's current frame_start and frame_end settings.        
        )
        
        # 2. Set the output filepath
        #    Ensure the output path ends with .mp4 extension
        if not (
            file_name.upper().endswith('.PNG') or
            file_name.upper().endswith('.JPG') or
            file_name.upper().endswith('.JPEG')
        ):
            base_name = os.path.splitext(file_name)[0]
            if file_format.upper() == 'PNG':
                file_name = base_name + '.png'
            elif file_format.upper() == 'JPEG':
                file_name = base_name + '.jpg'
            else:
                file_name = base_name + '.jpg'
            
        self.set_filepath_setting(
            file_name=file_name
        )

        # 3. Set image settings.
        if file_format == 'PNG':
            self.scene.render.image_settings.color_mode = 'RGBA'  # Include alpha channel for PNG
        elif file_format == 'JPEG':
            self.scene.render.image_settings.color_mode = 'RGB'  # JPG doesn't have alpha channel
        else:
            warn_msg = f"set_image_settings(), For the time being, we only support 'PNG' and 'JPEG', "
            warn_msg += f"\n\t not including '{file_format}'."
            self.logger.warn(warn_msg)
            self.scene.render.image_settings.color_mode = 'RGB'
            
        self.scene.render.image_settings.file_format = file_format  # Can be 'PNG', 'JPEG', 'OPEN_EXR', etc.
        self.scene.render.image_settings.compression = 15  # PNG compression (0-100)

        # 4. Print out the info log.
        image_settings = {
            "self.scene.render.image_settings.color_mode": self.scene.render.image_settings.color_mode,
            "self.scene.render.image_settings.file_format": self.scene.render.image_settings.file_format,
            "self.scene.render.image_settings.compression": self.scene.render.image_settings.compression
        }
        image_settings_str = json.dumps(image_settings, indent=2, ensure_ascii=False)
        self.logger.info(f"set_image_settings(), set the rendering engine's image settings.")
        self.logger.debug(image_settings_str)  


    def set_video_settings(
            self,             
            file_name="", 
            resolution_x=0, 
            resolution_y=0, 
            samples=0,
            frame_start=0, 
            frame_end=0,
            fps = 0
        ):
        """
        Set the Blender rendering engine setting to prepare the rendering of a MP4 video.

        Args:
            file_name (str): The full path for the output file.
            resolution_x (int): The width of the rendered output in pixels.
            resolution_y (int): The height of the rendered output in pixels.
            samples (int): The number of samples for the render engine, HD=128.
            frame_start (int): The index of starting frame.
            frame_end (int): The index of end frame.
            fps (float): bpy.context.scene.render.fps: Base frame rate
                         bpy.context.scene.render.fps_base: Frame rate divisor, forcely set to 1.0. 

            The popular resolutions are:
            - 480p: 854 * 480 (16:9)
            - 360p: 640 * 360 (16:9)
            - 720p (HD): 1280 * 720 (16:9)
            - 1080p (Full HD/FHD): 1920 * 1080 (16:9)
            - 720p (HD vertical 9:16): 720 * 1280 
            - 1080p (Full HD Mobile vertical 9:16): 1080 * 1920
        """    
        # 1. Set the scene
        self.set_scene_settings(
            resolution_x=resolution_x, 
            resolution_y=resolution_y, 
            samples=samples, 
            frame_start=frame_start, 
            frame_end=frame_end     
        )

        # 2. Ensure the output path ends with .mp4 extension
        if not (file_name.endswith('.mp4') or file_name.endswith('.MP4')):
            base_name = os.path.splitext(file_name)[0]
            file_name = base_name + '.mp4'

        # 3. Set the output filepath
        self.set_filepath_setting(
            file_name=file_name
        )

        # 4. Set video settings
        self.scene.render.image_settings.file_format = 'FFMPEG'
        self.scene.render.ffmpeg.codec = 'H264'
        self.scene.render.ffmpeg.format = 'MPEG4'
        self.scene.render.ffmpeg.audio_codec = 'AAC'
        self.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'  # Quality setting
        self.scene.render.ffmpeg.video_bitrate = 4000  # 4Mbps video bitrate
        self.scene.render.ffmpeg.audio_bitrate = 192  # 192kbps audio bitrate

        if fps > 0:
            self.scene.render.fps = fps
            self.scene.render.fps_base = 1.0

        # 5. Print out the info log
        output_setting = {
            "self.scene.render.image_settings.file_format": self.scene.render.image_settings.file_format,
            "self.scene.render.fps": self.scene.render.fps,
            "self.scene.render.fps_base": self.scene.render.fps_base,
            "self.scene.render.ffmpeg.codec": self.scene.render.ffmpeg.codec,
            "self.scene.render.ffmpeg.format": self.scene.render.ffmpeg.format,
            "self.scene.render.ffmpeg.audio_codec": self.scene.render.ffmpeg.audio_codec,
            "self.scene.render.ffmpeg.constant_rate_factor": self.scene.render.ffmpeg.constant_rate_factor,
            "self.scene.render.ffmpeg.video_bitrate": self.scene.render.ffmpeg.video_bitrate,
            "self.scene.render.ffmpeg.audio_bitrate": self.scene.render.ffmpeg.audio_bitrate     
        }
        output_setting_str = json.dumps(output_setting, indent=2, ensure_ascii=False)
        info_msg = f"set_video_settings(), set the video related rendering settings.\n"
        self.logger.info(info_msg)
        self.logger.debug(f"{output_setting_str} \n")


    def set_audio_settings(
            self, 
            file_name="", 
            samples=0,
            frame_start=0, 
            frame_end=0,
            fps = 0        
        ):
        """
        Set the Blender rendering engine setting to prepare the rendering of a MP3 audio.

        Args:
            file_name (str): The full path for the output file.
            samples (int): The number of samples for the render engine, HD=128.
            frame_start (int): The index of starting frame.
            frame_end (int): The index of end frame.
            fps (float): bpy.context.scene.render.fps: Base frame rate
                         bpy.context.scene.render.fps_base: Frame rate divisor, forcely set to 1.0. 
        """ 
        # 1. Set the scene
        self.set_scene_settings(
            resolution_x=0, 
            resolution_y=0, 
            samples=samples, 
            frame_start=frame_start, 
            frame_end=frame_end     
        )

        # 2. Ensure the output path ends with .mp3 extension
        if not (file_name.endswith('.mp3') or file_name.endswith('.MP3')):
            base_name = os.path.splitext(file_name)[0]
            file_name = base_name + '.mp3'

        # 3. Set the output filepath
        self.set_filepath_setting(
            file_name=file_name
        )

        # 4. Set the audio settings
        #    Crucially, set the video codec to 'NONE' to ensure only audio is rendered.
        self.scene.render.image_settings.file_format = 'FFMPEG'
        self.scene.render.ffmpeg.codec = 'NONE'
        self.scene.render.ffmpeg.format = 'MPEG4'
        self.scene.render.ffmpeg.audio_codec = 'AAC'
        self.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'  # Quality setting
        self.scene.render.ffmpeg.audio_bitrate = 192  # 192kbps audio bitrate
        # self.scene.render.ffmpeg.video_bitrate = 4000  # 4Mbps video bitrate

        if fps > 0:
            self.scene.render.fps = fps
            self.scene.render.fps_base = 1.0

        # 5. Print out the info log
        output_setting = {
            "self.scene.render.image_settings.file_format": self.scene.render.image_settings.file_format,
            "self.scene.render.fps": self.scene.render.fps,
            "self.scene.render.fps_base": self.scene.render.fps_base,
            "self.scene.render.ffmpeg.codec": self.scene.render.ffmpeg.codec,
            "self.scene.render.ffmpeg.format": self.scene.render.ffmpeg.format,
            "self.scene.render.ffmpeg.audio_codec": self.scene.render.ffmpeg.audio_codec,
            "self.scene.render.ffmpeg.constant_rate_factor": self.scene.render.ffmpeg.constant_rate_factor,
            "self.scene.render.ffmpeg.audio_bitrate": self.scene.render.ffmpeg.audio_bitrate     
        }
        output_setting_str = json.dumps(output_setting, indent=2, ensure_ascii=False)

        info_msg = f"set_audio_settings(), set the audio related rendering settings.\n"
        self.logger.info(info_msg)
        self.logger.debug(f"{output_setting_str} \n")          




    """
    def render_single_images(
            self, 
            image_output_filename=""
        ):
        ""
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
        ""      
        # Ensure output directory exists
        output_dir = os.path.dirname(image_output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        self.scene.render.filepath = image_output_filename

        # Start rendering
        bpy.ops.render.render(write_still=True)
        
        info_msg = f"render_single_images(): Output will be saved to: '{image_output_filename}'."
        self.logger.info(info_msg)


    def render_frame_images(self, output_path="frame_images"):
        # Rendering images for all frames.
        self.logger.info("render_frame_images(): Starting renderring frames to image series...")
        self.set_output_settings(
            file_name=output_path, 
            file_format="PNG"
        )

        self.start_rendering() 


    def _import_image_sequence(self, input_images_dir="frame_images", image_extension="png", frame_duration=1):
        ""
        Import image sequence into video sequencer
        :param image_extension: File extension of images (png, jpg, etc.)
        :param frame_duration: How many frames each image should display
        ""

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
            file_name=output_video_dir,
            file_format="FFMPEG", 
            video_codec="H264", 
            container="MPEG4",
            fps = fps
        )

        self.start_rendering()    
        self.logger.info(f" Successfully generated a video stored in directory '{output_video_dir}'")         
    """



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