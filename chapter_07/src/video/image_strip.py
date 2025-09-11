import bpy
import os
import json

from video.video_channel import VideoChannel


class ImageStrip:
    def __init__(
            self, 
            image_channel = None
        ):
        self.logger = None
        self.channel=image_channel

        self.strip_name=""       
        self.strip_content = None
        self.frame_start = 0
        self.frame_duration = 0

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("ImageStrip").getLogger()

            self.logger.info(f"ImageStrip class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize ImageStrip class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize ImageStrip class, error message: '{str(e)}'")

        
    def upload(
            self, 
            image_filename=""
        ):
        """
        Upload an image strip from a file. 

        Args:
            image_filename (str): The file name of this image strip, 
                the valid suffices are (".JPG", ".PNG"), case insensitive. 
        """
        filename_with_suffix = os.path.basename(image_filename)
        filename, suffix = os.path.splitext(filename_with_suffix)

        self.strip_name = f"raw_{filename}"
        channel_idx = self.channel.raw_image_channel
        frame_start_idx = self.channel.get_channel_end(channel_idx)
        
        image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
            name=self.strip_name, 
            filepath=image_filename, 
            channel=channel_idx,
            frame_start=frame_start_idx
        )

        self.strip_content = image_strip
        self.frame_start = self.channel.get_channel_end(channel_idx)
        self.frame_duration = 5 
        self.strip_content.frame_final_end = self.strip_content.frame_final_start + self.frame_duration - 1

        info_msg = f"load_strip(), load an image_strip from file '{image_filename}'"
        info_msg += f"\n\t with frame_start = {image_strip.frame_start}, "
        info_msg += f"and initializes its frame_duration to {self.frame_duration}."
        self.logger.info(info_msg)
