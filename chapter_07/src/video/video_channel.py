import bpy
import json

# from video.video_strip import VideoStrip
# from video.image_strip import ImageStrip

class VideoChannel:
    def __init__(self):
        self.logger = None
      
        self.channels={}
        self.main_video_channel = 1
        self.main_audio_channel = 2
        self.main_text_channel = 3
        self.raw_video_channel = 4
        self.raw_audio_channel = 5
        self.raw_text_channel = 6
        self.raw_image_channel = 7 

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("VideoChannel").getLogger()

            self.reserve_channels()
            self.logger.info(f"VideoChannel class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize VideoChannel class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize VideoChannel class, error message: '{str(e)}'")


    def reserve_channels(self):
        self.channels[str(self.main_video_channel)] = []
        self.channels[str(self.main_audio_channel)] = []
        self.channels[str(self.main_text_channel)] = []

        self.channels[str(self.raw_video_channel)] = []
        self.channels[str(self.raw_audio_channel)] = []
        self.channels[str(self.raw_text_channel)] = []
        self.channels[str(self.raw_image_channel)] = []


    def delete_strip(
            self, 
            strip_obj=None
        ):
        if strip_obj is None:
            warn_msg = f"delete_strip(), delete a strip that is None."
            self.logger.warn(warn_msg)
            return
        
        strip_type = type(strip_obj).__name__
        strip_name = strip_obj.strip_name

        if strip_type == "VideoStrip":
            main_video_channel = self.channels[self.main_video_channel]
            for strip_idx in range(len(main_video_channel)):
                if main_video_channel[strip_idx].strip_name == strip_obj.strip_name:
                    del main_video_channel[strip_idx]
                    break

            raw_video_channel = self.channels[self.raw_video_channel]
            for strip_idx in range(len(raw_video_channel)):
                if raw_video_channel[strip_idx].strip_name == strip_obj.strip_name:
                    del raw_video_channel[strip_idx]
                    break

            del strip_obj

            info_msg = f"delete_strip(), delete a video_strip called '{strip_name}'."
            self.logger.info(info_msg)


    def get_channel_end(
            self, 
            channel_idx=0
        ) -> int:
        channel_end_idx = 0

        if len(self.channels[str(channel_idx)]) == 0:
            channel_end_idx = 1
        else:        
            try:
                last_strip_idx = len(self.channels[str(channel_idx)]) - 1
                last_strip_obj = self.channels[str(channel_idx)][last_strip_idx]
                channel_end_idx = last_strip_obj.frame_start + last_strip_obj.frame_duration
       
            except Exception as e:
                warn_msg = f"get_channel_end(), cannot get the frame_end of the last strip in the channel '{channel_idx}', "
                warn_msg += f"\n\t error message: '{str(e)}'"
                self.logger.warn(warn_msg)
        
        return channel_end_idx


    def print_all_channels(self):
        channels_strips = {}

        channel_indices = [
            self.main_video_channel,
            self.main_audio_channel,
            self.main_text_channel,
            self.raw_video_channel, 
            self.raw_audio_channel, 
            self.raw_text_channel, 
            self.raw_image_channel    
        ]
        channel_types = [
            "main_video_channel",
            "main_audio_channel",
            "main_text_channel",
            "raw_video_channel", 
            "raw_audio_channel", 
            "raw_text_channel", 
            "raw_image_channel"  
        ]


        # for channel_idx in channel_indices:   
        for idx in range(len(channel_indices)):
            channel_idx = channel_indices[idx]
            if len(self.channels[str(channel_idx)]) > 0:
                one_channel = {
                    "channel_type": channel_types[idx],
                    "channel_strips": []
                }

                for strip_obj in self.channels[str(channel_idx)]:
                    one_strip = {}
                    one_strip["strip_name"] = strip_obj.strip_name
                    one_strip["frame_start"] = strip_obj.frame_start
                    one_strip["frame_duration"] = strip_obj.frame_duration
                    one_channel["channel_strips"].append(one_strip)

                channel_name = f"channel_{channel_idx}"
                channels_strips[channel_name] = one_channel

        channels_strips_str = json.dumps(channels_strips, indent=2, ensure_ascii=False)
        debug_msg = f"print_all_channels(): \n{channels_strips_str}\n"
        self.logger.debug(debug_msg)



    def convert_frame_idx_to_time_string(
            self, 
            frame_idx = 0
        ) -> str:
        """
        Convert a frame index to a "HH:MM:SS:MS" time string.
        
        Args:
            frame_idx: The frame index number to convert to "HH:MM:SS:MS" format time string.
            
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
            time_str: String in "HH:MM:SS:MS" format (e.g., "00:01:23:46")
            
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