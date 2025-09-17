import bpy
import os
import json


class AudioStrip:
    def __init__(
            self, 
            audio_channel = None
        ):
        self.logger = None     
        self.channel=audio_channel

        self.strip_file=""
        self.strip_name=""       
        self.strip_content = None
        self.frame_start = 0
        self.frame_duration = 0
        self.fps = 0
        
        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("AudioStrip").getLogger()

            self.logger.info(f"AudioStrip class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize AudioStrip class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize AudioStrip class, error message: '{str(e)}'")


    def upload(
            self, 
            strip_filename=""
        ):
        """
        Upload an audio strip from a file. 

        Args:
            strip_filename (str): The file name of this audio strip, 
                the valid suffices are (".MP3", ".WAV"),  case insensitive. 
        """ 
        self.strip_file = strip_filename

        filename_with_suffix = os.path.basename(strip_filename)
        filename, suffix = os.path.splitext(filename_with_suffix)

        self.strip_name = f"raw_{filename}"
        channel_idx = self.channel.raw_audio_channel
        frame_start_idx = self.channel.get_channel_end(channel_idx)

        audio_strip = bpy.context.scene.sequence_editor.sequences.new_sound(
            name=self.strip_name,
            filepath=self.strip_file, 
            channel=channel_idx,
            frame_start=frame_start_idx
        )
        self.strip_content = audio_strip

        if bpy.context.scene:
            scene = bpy.context.scene
            self.fps = scene.render.fps / scene.render.fps_base


        self.frame_start = self.channel.get_channel_end(channel_idx)
        self.frame_duration = self.strip_content.frame_final_end - self.strip_content.frame_final_start

        debug_msg = f"filename:'{filename}', self.strip_name:'{self.strip_name}', "
        debug_msg += f"self.strip_content.frame_final_end={self.strip_content.frame_final_end}, "
        debug_msg += f"self.strip_content.frame_final_start={self.strip_content.frame_final_start}"
        self.logger.debug(debug_msg)

        info_msg = f"upload(), load a video_strip from file '{strip_filename}'"
        info_msg += f"\n\t with frame_start = {audio_strip.frame_start}, "
        info_msg += f"frame_duration = {self.frame_duration}."
        self.logger.info(info_msg)


    def download(
            self, 
            audio_filename=""            
        ):
        """
        Download an audio strip to a file. 

        Args:
            audio_filename (str): The file name of this audio strip, 
                the valid suffices are (".MP3"),  case insensitive. 
        """ 
        scene = None
        if bpy.context.scene:
            scene = bpy.context.scene

        # Set scene duration to match the audio strip
        scene.frame_start = self.strip_content.frame_final_start
        scene.frame_end = self.strip_content.frame_final_end

        # Configure the render settings to export only the audio as an MP3.
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.audio_codec = 'MP3'
        scene.render.ffmpeg.audio_bitrate = 192  # Optional: sets the audio quality in kbps.

        # Crucially, set the video codec to 'NONE' to ensure only audio is rendered.
        scene.render.ffmpeg.codec = 'NONE'

        # Ensure the output path ends with .mp3 extension
        if not (audio_filename.endswith('.mp3') or audio_filename.endswith('.MP3')):
            base_name = os.path.splitext(audio_filename)[0]
            audio_filename = base_name + '.mp3'
            
        # Ensure the directory exists
        output_dir = os.path.dirname(audio_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Set output path
        scene.render.filepath = audio_filename
        scene.render.use_placeholder = False
        scene.render.use_file_extension = False
         
        # Render the animation (export the audio)
        try:
            bpy.ops.render.render(animation=True)
            info_msg = f"download(), successfully exported to: {audio_filename}."
            self.logger.info(info_msg)
        except Exception as e:
            warn_msg = f"download(), failed to export audio: {str(e)}"
            self.logger.warn(warn_msg)