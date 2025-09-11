import os
import json
import bpy

from video.video_strip import VideoStrip
from video.image_strip import ImageStrip
from video.audio_strip import AudioStrip


class VideoEditor:
    def __init__(self):
        self.logger = None
        self.camera = None
        self.scene = bpy.context.scene
        
        self.channel = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("VideoEditor").getLogger()

            from camera.camera import Camera
            self.camera = Camera("VideoEditorCamera")

            from video.video_channel import VideoChannel
            self.channel = VideoChannel()

            if not self.scene.sequence_editor:
                self.scene.sequence_editor_create()

            self.logger.info(f"VideoEditor class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize VideoEditor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize VideoEditor class, error message: '{str(e)}'")


    def upload(
            self, 
            strip_filename=""
        ):
        """
        Load a strip from a file, of various types including video, audio, image, text. 

        Args:
            strip_filename (str): The file name of this video strip, 
                the valid suffices are (".MP4", ".MOV", ".PNG", ".JPG", ".MP3", ".WAV", ".TXT"), 
                case insensitive. 
        """
        filename_with_suffix = os.path.basename(strip_filename)
        filename, suffix = os.path.splitext(filename_with_suffix)
        channel_idx = 0

        if suffix.upper() == ".MP4" or suffix.upper() == ".MOV":
            video_strip = VideoStrip(
                video_channel = self.channel
            )
            video_strip.upload(strip_filename)

            channel_idx = self.channel.raw_video_channel
            self.channel.channels[str(channel_idx)].append(video_strip)

        elif suffix.upper() == ".JPG" or suffix.upper() == ".PNG":
            image_strip = ImageStrip(
                image_channel = self.channel
            )
            image_strip.upload(strip_filename)

            channel_idx = self.channel.raw_image_channel
            self.channel.channels[str(channel_idx)].append(image_strip)

        elif suffix.upper() == ".MP3" or suffix.upper() == ".WAV":
            audio_strip = AudioStrip(
                audio_channel = self.channel
            )
            audio_strip.upload(strip_filename)

            channel_idx = self.channel.raw_audio_channel
            self.channel.channels[str(channel_idx)].append(audio_strip)


    def get_strip_object(
            self, 
            strip_name="",
            strip_type=""
        ):
        """
        Find the strip object, given the strip name, and type. 

        Args:
            strip_name (str): The object name of the strip,  
                if there are multiple strip objects share the same name, return the first one.
            strip_type (str): The type of this strip object, 
                the valid type string are (".MP4", ".MOV", ".PNG", ".JPG", ".MP3", ".WAV", ".TXT"), 
                case insensitive. 

        Returns:
            An object instance of strip object.
        """        
        channel_indices = []
        if strip_type.upper() == ".MP4" or strip_type.upper() == ".MOV":
            channel_indices = [
                self.channel.main_video_channel,
                self.channel.raw_video_channel
            ]

        elif strip_type.upper() == ".JPG" or strip_type.upper() == ".PNG":
            return None
        
        elif strip_type.upper() == ".MP3" or strip_type.upper() == ".WAV":
            channel_indices = [
                self.channel.main_audio_channel,
                self.channel.raw_audio_channel
            ]

        # for channel_idx in channel_indices:   
        for channel_idx in channel_indices:
            if len(self.channel.channels[str(channel_idx)]) > 0:
                for strip_obj in self.channel.channels[str(channel_idx)]:
                    if strip_obj.strip_name.upper() == strip_name.upper():
                        return strip_obj

        return None


    def download(
            self, 
            strip_name = "",
            strip_filename=""
        ):
        """
        Load a strip from a file, of various types including video, audio, image, text. 

        Args:
            strip_name (str): The object name of the strip that will be converted into file and be downloaded, 
                if there are multiple strip objects share the same name, download the first one.
            strip_filename (str): The file name of this strip is downloaded to, 
                the valid suffices are (".MP4", ".MOV", ".PNG", ".JPG", ".MP3", ".WAV", ".TXT"), 
                case insensitive. 
        """
        filename_with_suffix = os.path.basename(strip_filename)
        filename, suffix = os.path.splitext(filename_with_suffix)

        strip_obj = self.get_strip_object(
            strip_name=strip_name,
            strip_type=suffix.upper()
        )

        if strip_obj:
            strip_obj.download(strip_filename)

            info_msg = f"download(), download strip object named '{strip_obj.strip_name}' "
            info_msg += f"to file '{strip_filename}'."
            self.logger.info(info_msg)
        
        elif suffix.upper() == ".JPG" or suffix.upper() == ".PNG": 
            warn_msg = f"download(), image object download is not supported, because it is not necessary."
            self.logger.warn(warn_msg)

        else:        
            warn_msg = f"download(), cannot find strip object named'{strip_name}'."
            self.logger.warn(warn_msg)



    def delete_strip(
            self, 
            strip_obj=None
        ):
        self.channel.delete_strip(strip_obj)



    def convert_frame_idx_to_time_string(
            self, 
            frame_idx = 0
        ) -> str:
        """
        Convert a frame index to a "HH:MM:SS:MS" time string.
        
        Args:
            frame: The frame number to convert
            scene: Blender scene to get frame rate from (uses current scene if None)
            
        Returns:
            String in "HH:MM:SS:MS" format
        """
        # Get the frame rate from the scene (default to 24fps if not specified)
        scene = bpy.context.scene
        fps = scene.render.fps / scene.render.fps_base  # Handle fractional frame rates

        debug_msg = f"convert_frame_idx_to_time_string(), scene.render.fps={scene.render.fps}, "
        debug_msg += f"scene.render.fps_base={scene.render.fps_base}, fps={fps}"
        self.logger.debug(debug_msg)


        # Calculate total milliseconds
        total_seconds = frame_idx / fps
        total_ms = int(total_seconds * 1000)
        
        # Break down into components
        hours = total_ms // 3600000
        remaining_ms = total_ms % 3600000
        
        minutes = remaining_ms // 60000
        remaining_ms %= 60000
        
        seconds = remaining_ms // 1000
        ms = remaining_ms % 1000
        
        # Format with leading 
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{ms:03d}"
        return time_str
    

    def convert_time_string_to_frame_idx(
            self, 
            time_str=""
        ) -> int:
        """
        Convert a "HH:MM:SS:MS" time string to a frame index.
        
        Args:
            time_str: String in "HH:MM:SS:MS" format (e.g., "00:01:23:456")
            scene: Blender scene to get frame rate from (uses current scene if None)
            
        Returns:
            Frame index as an integer (rounded to nearest frame)
        """
        # Split the time string into components
        try:
            hours, minutes, seconds, ms = map(int, time_str.split(':'))
        except ValueError as e:
            warn_msg = f"convert_time_string_to_frame_idx(), "
            warn_msg += f"Invalid time format: {time_str}. Use 'HH:MM:SS:MS'"
            self.logger.debug(warn_msg)
            return -1
        
        # Calculate total time in seconds
        total_seconds = (hours * 3600) + (minutes * 60) + seconds + (ms / 1000)
        
        # Get frame rate from the scene
        scene = bpy.context.scene
        fps = scene.render.fps / scene.render.fps_base  # Handle accurate frame rate
        
        # Convert seconds to frames and round to nearest integer
        return round(total_seconds * fps)



    @staticmethod
    def run_demo():
        video_editor = VideoEditor()

        image_filename = "input/battle_field.png"
        video_editor.upload(image_filename)

        video_filename = "input/TrueStory.mp4"
        video_editor.upload(video_filename)

        audio_filename = "input/TrueStory.mp3"
        video_editor.upload(audio_filename)

        print(f"Upload 'battle_field.png', 'TrueStory.mp4', and 'TrueStory.mp3' \n")
        video_editor.channel.print_all_channels()

        video_editor.download(strip_name="raw_TrueStory", strip_filename=f"output/raw_TrueStory.mp3")
        video_editor.download(strip_name="raw_TrueStory", strip_filename=f"output/raw_TrueStory.mp4")
        video_editor.download(strip_name="raw_battle_field", strip_filename=f"output/raw_TrueStory.jpg")