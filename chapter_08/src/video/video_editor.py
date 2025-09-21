import os
import json
import bpy

from video.video_strip import VideoStrip
from video.image_strip import ImageStrip
from video.audio_strip import AudioStrip


class VideoEditor:
    def __init__(self):
        self.logger = None
        self.renderer = None
        
        self.video_channel = None
        self.video_compositor = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("VideoEditor").getLogger()

            from camera.camera import Camera
            self.renderer = Camera("VideoEditorCamera").renderer

            from video.video_channel import VideoChannel
            self.video_channel = VideoChannel()

            if not bpy.context.scene.sequence_editor:
                bpy.context.scene.sequence_editor_create()

            self.logger.info(f"VideoEditor class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize VideoEditor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize VideoEditor class, error message: '{str(e)}'")


    def upload(
            self, 
            strip_filename="",
            image_duration=0
        ):
        """
        Load a strip from a file, of various types including video, audio, image, text. 

        Args:
            strip_filename (str): The file name of this video strip, 
                the valid suffices are (".MP4", ".MOV", ".PNG", ".JPG", ".JPEG", ".MP3", ".WAV", ".TXT"), 
                case insensitive. 
            image_duration(int): The duration of the image sequence,
                for video and audio sequence, their durations are the length of the video and audio content.
        """
        filename_with_suffix = os.path.basename(strip_filename)
        filename, suffix = os.path.splitext(filename_with_suffix)
        channel_idx = 0

        if suffix.upper() == ".MP4" or suffix.upper() == ".MOV":
            video_strip = VideoStrip(
                video_channel = self.video_channel
            )
            video_strip.upload(strip_filename)

            channel_idx = self.video_channel.raw_video_channel
            self.video_channel.channels[str(channel_idx)].append(video_strip)

        elif suffix.upper() == ".JPG" or suffix.upper() == ".JPEG" or suffix.upper() == ".PNG":
            image_strip = ImageStrip(
                image_channel = self.video_channel
            )
            image_strip.upload(
                image_filename=strip_filename,
                frame_duration=image_duration
            )

            channel_idx = self.video_channel.raw_image_channel
            self.video_channel.channels[str(channel_idx)].append(image_strip)

        elif suffix.upper() == ".MP3" or suffix.upper() == ".WAV":
            audio_strip = AudioStrip(
                audio_channel = self.video_channel
            )
            audio_strip.upload(strip_filename)

            channel_idx = self.video_channel.raw_audio_channel
            self.video_channel.channels[str(channel_idx)].append(audio_strip)


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
        if strip_type.upper().endswith("MP4") or strip_type.upper().endswith("MOV"):
            channel_indices = [
                self.video_channel.main_video_channel,
                self.video_channel.raw_video_channel
            ]

        elif strip_type.upper().endswith("JPG") or strip_type.upper().endswith("JPEG") or strip_type.upper().endswith("PNG"):
            return None
        
        elif strip_type.upper().endswith("MP3") or strip_type.upper().endswith("WAV"):
            channel_indices = [
                self.video_channel.main_audio_channel,
                self.video_channel.raw_audio_channel
            ]

        # for channel_idx in channel_indices:   
        for channel_idx in channel_indices:
            if len(self.video_channel.channels[str(channel_idx)]) > 0:
                for strip_obj in self.video_channel.channels[str(channel_idx)]:
                    if strip_obj.strip_name.upper() == strip_name.upper():
                        info_msg = f"get_strip_object(), found strip object named '{strip_obj.strip_name}'."
                        self.logger.info(info_msg)
                        return strip_obj

        warn_msg = f"get_strip_object(), cannot found strip object named '{strip_obj.strip_name}'."
        self.logger.warn(warn_msg)        
        return None


    def render(
            self, 
            file_name="",
            frame_start=0, 
            frame_end=0,
            fps=0
        ):
        """
        Render all strips in the scene to a file, either a video file, or an audio file. 

        Args:
            file_name (str): The file name of this strip is downloaded to, 
                the valid suffices are (".MP4", ".MP3"), case insensitive. 
        """
        filename_with_suffix = os.path.basename(file_name)
        filename, suffix = os.path.splitext(filename_with_suffix)

        if suffix.upper() == ".MP4":
            self.renderer.set_video_settings(    
                file_name=file_name,
                frame_start=frame_start, 
                frame_end=frame_end,
                fps=fps
            )
            self.renderer.start_rendering()
            
        elif suffix.upper() == ".MP3":
            self.renderer.set_audio_settings(
                file_name=file_name     
            )
            self.renderer.start_rendering()


    def delete_strip(
            self, 
            strip_obj=None
        ):
        self.video_channel.delete_strip(strip_obj)



    def trim(
            self,
            strip_name="",
            strip_type="", 
            start_frame=0,
            end_frame=0
        ):
        """
        Trim the strip. 

        Args:
            strip_name (str): The object instance of the strip to set volume. 
            strip_type (str): The type of this strip, 
                the valid types are (".MP4", ".MOV", ".PNG", ".JPG", ".MP3", ".WAV", ".TXT"), case insensitive. 
            start_frame (int): The starting frame index of the strip.
            end_frame (int): The end frame index of the strip.
                start_frame and end_frame are not the absolute ones, 
                but the relative ones regarding to the beginning of the strip.
            If you need to convert a time string of "HH:MM:SS:MS" into a frame index, 
                please refer to the convert_time_string_to_frame_idx() of video_editor.py 
        """
        if  start_frame >= end_frame:
            warn_msg = f"trim(), the start_frame={start_frame} must be less than the end_frame={end_frame}."
            self.logger.warn(warn_msg)
            return None
        
        strip_obj = self.get_strip_object(
            strip_name=strip_name,
            strip_type=strip_type
        )
        if not strip_obj:
            warn_msg = f"trim(), cannot find strip named '{strip_name}', with type '{strip_type}'."
            self.logger.warn(warn_msg)
            return


        # 1. frame_duration      
        strip_obj.frame_duration = round(end_frame - start_frame)
        
        # 2. frame_start
        # strip_obj.frame_start keeps unchanged in Blender VSE timeline.    
        strip_obj.strip_content.frame_start = round(strip_obj.frame_start - start_frame)

        # 3. frame_final_end & frame_end
        strip_obj.strip_content.frame_final_end = round(strip_obj.strip_content.frame_start + strip_obj.frame_duration)
        strip_obj.frame_end = round(strip_obj.frame_start + strip_obj.frame_duration)

        # 4. frame_offset_start 
        strip_obj.strip_content.frame_offset_start = round(start_frame)

        # 5. frame_offset_end
        # frame_offset_end defines how many frames from the end of the original source video are ignored (trimmed off).
        strip_obj.strip_content.frame_offset_end = round(strip_obj.strip_content.frame_duration - end_frame)

        # Adjust the Blender UI
        if strip_obj.frame_end > bpy.context.scene.frame_end:
            bpy.context.scene.frame_end = strip_obj.frame_end

        info_msg = f"trim(), get a subset of the strip '{strip_obj.strip_name}'"
        info_msg += f"\n\t with frame_start = {strip_obj.strip_content.frame_start}, "
        info_msg += f"and initializes its frame_duration to {strip_obj.strip_content.frame_duration}."
        self.logger.info(info_msg)


    def set_volume(
            self, 
            strip_name="",
            strip_type="",
            volume = 0.0                
        ):
        """
        Set the volume of the strip. When volume is 0.0, mute the strip.

        Args:
            strip_name (str): The object instance of the strip to set volume. 
            strip_type (str): The type of this strip, 
                the valid types are (".MP4", ".MOV", ".PNG", ".JPG", ".MP3", ".WAV", ".TXT"), case insensitive. 
            volume (float): The volume of this audio_strip, within (0.0, 1.0)
        """
        if (strip_type.upper().endswith("MP4") or 
            strip_type.upper().endswith("MOV") or
            strip_type.upper().endswith("MP3") or 
            strip_type.upper().endswith("WAV")
        ):
            if not (0.0 <= volume <= 1.0):
                warn_msg = f"set_volume(), volume={volume} is out of range (0.0-1.0). Clamping to valid range."
                self.logger.warn(warn_msg)
                volume = max(0.0, min(1.0, volume))
        
            strip_obj = self.get_strip_object(
                strip_name=strip_name,
                strip_type=strip_type
            )
            if not strip_obj:
                warn_msg = f"set_volume(), cannot find strip named '{strip_name}', with type '{strip_type}'."
                self.logger.warn(warn_msg)
                return

            # The 'volume' property exists on MovieStrip only if the source video contains audio, and the computer has audio device.
            # For silent videos, 'has_audio' will be False, and 'volume' will not be available.
            if not hasattr(strip_obj.strip_content, "volume"):
                warn_msg = f"set_volume(), strip_obj.strip_content '{strip_obj.strip_name}', "
                warn_msg += f"type='{type(strip_obj.strip_content)}', doesn't have 'volume' property, \n\t maybe because, "
                warn_msg += f"1. the video is silent, 2. the video doesn't have sound trek, 3. the computer doesn't have sound device." 
                self.logger.warn(warn_msg)
                return 

            clamped_volume = max(0.0, min(2.0, volume))
            strip_obj.strip_content.volume = clamped_volume

            info_msg = f"set_volume(), set the volume of the strip '{strip_obj.strip_name}', "
            info_msg += f"type='{type(strip_obj.strip_content)}', to {strip_obj.strip_content.volume}."
            self.logger.info(info_msg)

        else:
            warn_msg = f"set_volume(), strip_type='{strip_type}' doesn't have volume property."
            self.logger.warn(warn_msg)


    def set_alpha(
            self, 
            strip_name="",
            strip_type="",
            alpha = 0.0                  
        ):
        """
        Set the alpha (transparency) of the video or image strip. When alpha is 0.0 (totally transparent), mute the strip.

        Args:
            strip_name (str): The object instance of the strip to set volume. 
            strip_type (str): The type of this strip, 
                the valid types are (".MP4", ".MOV", ".PNG", ".JPG", ".TXT"), case insensitive. 
            alpha (float): The alpha of this strip, from 0.0 (fully transparent) to 1.0 (fully opaque)
        """
        if (strip_type.upper().endswith("MP4") or 
            strip_type.upper().endswith("MOV") or
            strip_type.upper().endswith("PNG") or 
            strip_type.upper().endswith("JPG") or 
            strip_type.upper().endswith("JPEG")
        ):
            if not (0.0 <= alpha <= 1.0):
                warn_msg = f"set_alpha(), alpha={alpha} is out of range (0.0, 1.0). Clamping to valid range."
                self.logger.warn(warn_msg)
                alpha = max(0.0, min(1.0, alpha))

            strip_obj = self.get_strip_object(
                strip_name=strip_name,
                strip_type=strip_type
            )
            if not strip_obj:
                warn_msg = f"set_alpha(), cannot find strip named '{strip_name}', with type '{strip_type}'."
                self.logger.warn(warn_msg)
                return
            
            if (not hasattr(strip_obj.strip_content, "blend_type") or  
                not hasattr(strip_obj.strip_content, "blend_alpha")
            ):
                warn_msg = f"set_alpha(), strip_obj.strip_content, type='{type(strip_obj.strip_content)}', "
                warn_msg += f"doesn't have 'blend_type' property, or 'blend_alpha' property."
                self.logger.warn(warn_msg)
                return 
                
            # Set blend mode to "ALPHA_OVER" to enable transparency
            strip_obj.strip_content.blend_type = 'ALPHA_OVER'
            # Set alpha value
            strip_obj.strip_content.blend_alpha = alpha
            
            info_msg = f"set_alpha(), set the alpha of the strip '{strip_obj.strip_name}' to {strip_obj.strip_content.blend_alpha}."
            self.logger.info(info_msg)

        else:
            warn_msg = f"set_alpha(), strip_type='{strip_type}' is not valid."
            self.logger.warn(warn_msg)



    @staticmethod
    def run_demo():
        video_editor = VideoEditor()

        # 1. Upload MP4 and MP3
        image_filename = "input/battle_field.png"
        video_editor.upload(
            strip_filename=image_filename,
            image_duration=200
        )

        video_filename = "input/TrueStory.mp4"
        video_editor.upload(
            strip_filename=video_filename
        )

        video_nyu_filename = "input/nyu_corridor.MOV"
        video_editor.upload(
            strip_filename=video_nyu_filename
        )

        video_nyu_object = video_editor.get_strip_object(
            strip_name="raw_nyu_corridor",
            strip_type="MP4"
        )
        video_nyu_object.frame_start = 10
        video_nyu_object.strip_content.frame_start = 250

        audio_filename = "input/TrueStory.mp3"
        video_editor.upload(
            strip_filename=audio_filename
        )

        # 2. Trim MP4
        video_editor.trim(
            strip_name="raw_TrueStory",
            strip_type="MP4", 
            start_frame=500,
            end_frame=1200
        )

        # 3. Mix sound and lower volume of MP4 and MP3
        video_editor.set_volume(
            strip_name="raw_TrueStory",
            strip_type="MP4",
            volume = 0.5                
        )

        video_editor.set_volume(
            strip_name="raw_TrueStory",
            strip_type="MP3",
            volume = 0.5              
        )

        # 4. Set alpha of MP4 vidoes
        video_nyu_object = video_editor.get_strip_object(
            strip_name="raw_nyu_corridor",
            strip_type="MP4"
        )
        video_nyu_object.frame_start = 10

        video_editor.set_alpha(
            strip_name="raw_nyu_corridor",
            strip_type="MP4",
            alpha = 0.5                  
        )

        video_editor.set_alpha(
            strip_name="raw_TrueStory",
            strip_type="MP4",
            alpha = 0.5                  
        )

        # 5. Print out all media in the various channels. 
        print(f"Upload 'battle_field.png', 'TrueStory.mp4', and 'TrueStory.mp3' \n")
        video_editor.video_channel.print_all_channels()

        """
        # 6. Rendering
        rendered_output_filename = "truestory_output/rendered_truestory.mp4"
        video_editor.render(
            file_name=rendered_output_filename,
            frame_start=1, 
            frame_end=1500,
            fps=25
        )   
        """

        # 7. Upload an image sequence from disk to scene
        greenscreen_imgseq_dir = "/home/robot/movie_blender_studio/output/bicycling_greenscreen_imgseq"
        from video.image_sequence_strip import ImageSequenceStrip
        imgseq_strip = ImageSequenceStrip()
        imgseq_strip.upload_image_sequence(
            image_sequence_dir=greenscreen_imgseq_dir
        )

        # 8. Render bpy.context.scene to an image sequence. The scene may contain multiple strips.
        whole_scene_imgseq_dir = "/home/robot/movie_blender_studio/output/whole_scene_imgseq"
        imgseq_strip.render_to_image_sequence(
            image_sequence_dir=whole_scene_imgseq_dir
        )