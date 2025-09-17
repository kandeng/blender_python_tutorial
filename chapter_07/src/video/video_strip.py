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
        debug_msg += f"self.strip_content.frame_final_start={self.strip_content.frame_final_start}"
        debug_msg += f"self.resolution=({self.resolution_x}*{self.resolution_y})"
        self.logger.debug(debug_msg)

        info_msg = f"load_strip(), load a video_strip from file '{video_filename}'"
        info_msg += f"\n\t with frame_start = {video_strip.frame_start}, "
        info_msg += f"frame_duration = {self.frame_duration}."
        self.logger.info(info_msg)



    def download(
            self, 
            video_filename=""            
        ):
        """
        Download a video strip from a file. 

        Args:
            video_filename (str): The file name of this video strip, 
                the valid suffices are (".MP4"),  case insensitive. 
        """ 
        scene = None
        if bpy.context.scene:
            scene = bpy.context.scene
        
        # Set scene duration to match the video strip
        scene.frame_start = self.strip_content.frame_final_start
        scene.frame_end = self.strip_content.frame_final_end

        self.logger.debug(f"self.strip_content.fps = {self.strip_content.fps}")
        scene.render.fps = int(self.strip_content.fps)  # Match video's frame rate
        scene.render.fps_base = 1.0
        
        # Configure render settings for MP4 output
        scene.render.image_settings.file_format = 'FFMPEG'
        scene.render.ffmpeg.format = 'MPEG4'
        scene.render.ffmpeg.codec = 'H264'
        scene.render.ffmpeg.audio_codec = 'AAC'
        scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'  # Quality setting
        scene.render.ffmpeg.video_bitrate = 4000  # 4Mbps video bitrate
        scene.render.ffmpeg.audio_bitrate = 192  # 192kbps audio bitrate
        
        # Ensure the directory exists
        output_dir = os.path.dirname(video_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Set output path
        scene.render.filepath = video_filename
        scene.render.use_placeholder = False
        scene.render.use_file_extension = False
        
        # Render the animation (export the video)
        try:
            bpy.ops.render.render(animation=True)
            info_msg = f"download(), successfully exported to: {video_filename}."
            self.logger.info(info_msg)
        except Exception as e:
            warn_msg = f"download(), failed to export video: {str(e)}"
            self.logger.warn(warn_msg)



    def substrip(
            self, 
            substrip_name="",
            start_frame=0,
            end_frame=0
        ):
        """
        Get a subset of a video. 

        Args:
            substrip_name (str): The name of the newly created video substrip. 
            start_frame (int): The starting frame index of the subset of the video.
            end_frame (int): The end frame index of the subset of the video.
            If you need to convert a time string of "HH:MM:SS:MS" into a frame index, 
                please refer to the convert_time_string_to_frame_idx() of video_editor.py 

        Returns:
            An object instance of newly created VideoStrip.
        """
        if not isinstance(start_frame, int) or not isinstance(end_frame, int):
            warn_msg = f"substrip(), both 'start_time' and 'end_time' should be both integers of frame indices."
            self.logger.warn(warn_msg)
            return None

        if  start_frame >= end_frame:
            warn_msg = f"substrip(), start frame must be less than end frame."
            self.logger.warn(warn_msg)
            return None
            
        if end_frame > bpy.context.scene.frame_end:
            warn_msg = f"End frame exceeds scene's end frame"
            self.logger.warn(warn_msg)
            return None
        
        channel_idx = self.channel.raw_video_channel
        frame_start_idx = self.channel.get_channel_end(channel_idx)

        # Create the new video strip with the same file path
        video_strip = bpy.context.scene.sequence_editor.sequences.new_movie(
            name=substrip_name, 
            filepath=self.strip_file, 
            channel=channel_idx,
            frame_start=frame_start_idx
        )
 
        substrip_video = VideoStrip(self.channel)
        substrip_video.strip_file = self.strip_file
        substrip_video.strip_name = substrip_name  
        substrip_video.strip_content = video_strip
        substrip_video.frame_start = start_frame
        substrip_video.frame_duration = end_frame - start_frame
        substrip_video.fps = self.fps

        info_msg = f"substrip(), get a segment from videostrip '{self.strip_name}', "
        info_msg += f"from frame {substrip_video.frame_start}, with duration {substrip_video.frame_duration}. "
        info_msg += f"The name of the newly created substrip is '{substrip_video.strip_name}'."
        self.logger.info(info_msg)

        return substrip_video


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