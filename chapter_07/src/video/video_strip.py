import bpy
import os
import json

from video.video_channel import VideoChannel
from video.audio_strip import AudioStrip


class VideoStrip:
    def __init__(
            self, 
            video_channel = None
        ):
        self.logger = None     
        self.channel=video_channel

        self.strip_file=""
        self.strip_name=""       
        self.strip_content = None
        self.frame_start = 0
        self.frame_end = 0
        self.frame_duration = 0
        self.fps = 0
        self.resolution_x = 0
        self.resolution_y = 0
        
        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("VideoStrip").getLogger()

            self.logger.info(f"VideoStrip class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize VideoStrip class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize VideoStrip class, error message: '{str(e)}'")

        
    def upload(
            self, 
            video_filename=""
        ):
        """
        Upload a video strip from a file. 

        Args:
            video_filename (str): The file name of this video strip, 
                the valid suffices are (".MP4", ".MOV"),  case insensitive. 
        """ 
        self.strip_file = video_filename

        filename_with_suffix = os.path.basename(video_filename)
        filename, suffix = os.path.splitext(filename_with_suffix)

        self.strip_name = f"raw_{filename}"
        channel_idx = self.channel.raw_video_channel
        frame_start_idx = self.channel.get_channel_end(channel_idx)

        video_strip = bpy.context.scene.sequence_editor.sequences.new_movie(
            name=self.strip_name, 
            filepath=self.strip_file, 
            channel=channel_idx,
            frame_start=frame_start_idx
        )
        self.strip_content = video_strip

        if bpy.context.scene:
            scene = bpy.context.scene
            self.fps = scene.render.fps / scene.render.fps_base


        self.frame_start = self.channel.get_channel_end(channel_idx)
        self.frame_duration = self.strip_content.frame_final_end - self.strip_content.frame_final_start
        self.frame_end = self.frame_start + self.frame_duration

        self.resolution_x = self.strip_content.elements[0].orig_width
        self.resolution_y = self.strip_content.elements[0].orig_height

        debug_msg = f"filename:'{filename}', self.strip_name:'{self.strip_name}', "
        debug_msg += f"self.strip_content.frame_final_end={self.strip_content.frame_final_end}, "
        debug_msg += f"self.strip_content.frame_final_start={self.strip_content.frame_final_start}, "
        debug_msg += f"self.resolution=({self.resolution_x}*{self.resolution_y})."
        self.logger.debug(debug_msg)

        info_msg = f"load_strip(), load a video_strip from file '{video_filename}'"
        info_msg += f"\n\t with frame_start = {video_strip.frame_start}, "
        info_msg += f"frame_duration = {self.frame_duration}."
        self.logger.info(info_msg)


    def segment_audio(self):
        """
        Get the sournd track from the 'self.strip_content' video_strip.

        Returns:
            An object instance of newly created AudioStrip.
        """
        if not self.strip_content.sound:
            warn_msg = f"segment_audio(), video strip '{self.strip_name}' has no associated audio track."
            self.logger.warn(warn_msg)

        # Create separate audio strip
        audio_strip_name = f"{self.strip_content.name}_soundtrek"
        channel_idx = self.channel.raw_audio_channel 

        sequencer = bpy.context.scene.sequence_editor
        audio_strip = sequencer.sequences.new_sound(
            name=audio_strip_name,
            filepath=self.strip_content.sound.filepath,
            channel=channel_idx,
            frame_start=self.strip_content.frame_start
        )
        
        # Match audio timing to video strip (account for any video offsets)
        audio_strip.frame_offset_start = self.strip_content.frame_offset_start
        audio_strip.frame_final_duration = self.strip_content.frame_final_duration
        audio_strip.volume = self.strip_content.volume  # Match original volume

        soundtrek_audiostrip = AudioStrip(self.channel)
        soundtrek_audiostrip.strip_file = self.strip_content.sound.filepath
        soundtrek_audiostrip.strip_name = audio_strip_name  
        soundtrek_audiostrip.strip_content = audio_strip
        soundtrek_audiostrip.frame_start = self.frame_start
        soundtrek_audiostrip.frame_duration = self.frame_duration
        soundtrek_audiostrip.fps = self.fps

        info_msg = f"segment_audio(), get the soundtrek audio_strip from the videostrip '{self.strip_name}', "
        info_msg += f"the name of the newly created soundtrek audio_strip is '{soundtrek_audiostrip.strip_name}'."
        self.logger.info(info_msg)

        return soundtrek_audiostrip
    
