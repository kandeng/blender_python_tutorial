import os
import shutil
import subprocess
import cv2
import json

from moviepy import *
import numpy as np



class VideoEditor:
    def __init__(self):
        self.logger=None
        self.video_metadata={}
        self.video_metadata_filename="video_metadata.json"

        self.font_dir=f"/home/robot/movie_blender_studio/asset/font"
        self.NotoSansSC_Light=f"{self.font_dir}/Noto_Sans_SC/static/NotoSansSC-Light.ttf"


        try:
            from logger.logger import Logger
            self.logger = Logger("VideoEditing").getLogger()

            self.logger.info(f"VideoEditor class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize VideoEditor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize VideoEditor class, error message: '{str(e)}'")


    def _mkdir(
            self, 
            dir_path: str=""
        ):
        # 1. Check if the path exists and is a directory
        if os.path.isdir(dir_path):
            try:
                # 2. Use shutil.rmtree to delete the directory and all contents
                shutil.rmtree(dir_path)
            except OSError as e:
                # Handle permissions errors or other OS-level issues
                warn_msg = f"_mkdir(), cannot delete directory ''. "
                warn_msg += f"The error message is: \n\t {str(e)}"
                self.logger.warning(warn_msg)
                return

        # 2. mkdir. 
        os.makedirs(dir_path, exist_ok=True)


    def get_video_metadata(
            self,
            video_filepath: str="",
        ) -> dict:
        # 1. Double check if the input filepath and the output directory exist.
        if not os.path.isfile(video_filepath):
            warn_msg = f"video_to_image_sequence(), the input video_filepath '{video_filepath}' doesn't exist"
            self.logger.warning(warn_msg)
            return {}

        # 2. Retrieve the video properties, and save them to 'video_metadata.json' 
        video_metadata = {}

        try:
            video_obj = cv2.VideoCapture(video_filepath)
            video_metadata = {
                "resolution_x": int(video_obj.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "resolution_y": int(video_obj.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": video_obj.get(cv2.CAP_PROP_FPS),
                "codec_fourcc": int(video_obj.get(cv2.CAP_PROP_FOURCC)),
                "format_id": int(video_obj.get(cv2.CAP_PROP_FORMAT)),
                "frame_count": int(video_obj.get(cv2.CAP_PROP_FRAME_COUNT))
            }
        except Exception as e:
            warn_msg = f"get_video_metadata(), following exception was thrown "
            warn_msg += f"when using CV2 to get metadata from video '{video_filepath}'."
            self.logger.warning(warn_msg)
            return {}

        # 3. Print out the meta-data and return it.
        video_metadata_str = json.dumps(video_metadata, indent=2, ensure_ascii=False)
        info_msg = f"render_to_image_sequence(), scene_output_settings:\n{video_metadata_str}\n"
        self.logger.info(info_msg)  
        return video_metadata


    def video_to_image_sequence(
            self, 
            video_filepath: str="",
            image_sequence_dir: str="",
        ):
        """
        Convert a video to a sequence of images, 
        and write the metadata of the video into 'video_metadata.json'

        Notice that when converting a MOV video file shot by iPhone, 
        the converted images may look different from the original video.
        The reason is that the color space of the MOV video file is HDR, 
        while the standard color space is SDR.
        
        Args:
            video_filepath (str): The input video filepath,
                the valid suffices of the images are (".MP4", ".MOV", ".WEBM"), case insensitive. 
            image_sequence_dir (str): Directory to save output images,
                will be created if it doesn't exist.
        """       
        # 1. Double check if the input filepath and the output directory exist.
        if not os.path.isfile(video_filepath):
            warn_msg = f"video_to_image_sequence(), the input video_filepath '{video_filepath}' doesn't exist"
            self.logger.warning(warn_msg)
            return
        
        image_sequence_dir = image_sequence_dir.rstrip('/')
        self._mkdir(image_sequence_dir)
        
        # 2. Retrieve the video properties, and save them to 'video_metadata.json' 
        video_obj = cv2.VideoCapture(video_filepath)
        video_metadata = {
            "resolution_x": int(video_obj.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "resolution_y": int(video_obj.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": video_obj.get(cv2.CAP_PROP_FPS),
            "codec_fourcc": int(video_obj.get(cv2.CAP_PROP_FOURCC)),
            "format_id": int(video_obj.get(cv2.CAP_PROP_FORMAT)),
            "frame_count": int(video_obj.get(cv2.CAP_PROP_FRAME_COUNT))
        }

        video_metadata_str = json.dumps(video_metadata, indent=2, ensure_ascii=False)
        debug_msg = f"render_to_image_sequence(), scene_output_settings:\n{video_metadata_str}\n"
        self.logger.debug(debug_msg)  

        json_filepath = f"{image_sequence_dir.rstrip('/')}/{self.video_metadata_filename}"
        with open(json_filepath, "w") as fo:
            fo.write(video_metadata_str)

        # 3. Disassemble the video into a sequence of images. 
        info_msg = f"video_to_image_sequence(), start to convert the input video '{video_filepath}' into a sequence of images ..."
        self.logger.info(info_msg)       

        count = 0
        flag = 1
        while flag:
            flag, image = video_obj.read()
            if flag:
                try:
                    cv2.imwrite(f"{image_sequence_dir}/frame_{count:04}.png", image)
                except Exception as e:
                    warn_msg = f"video_to_image_sequence(), when doing 'cv2.imwrite()', an exception is thrown: "
                    warn_msg += f"'{str(e)}'."
                    self.logger.warning(warn_msg)
                    break
                count += 1      

        # 4. Print out the log message.
        video_obj.release()  

        info_msg = f"video_to_image_sequence(), complete the convertion of the input video '{video_filepath}', "
        info_msg += f"to an image sequence in directory '{image_sequence_dir}'."
        self.logger.info(info_msg)


    def image_sequence_to_mp4(
            self,
            image_sequence_dir: str="",
            video_filepath: str=""      
        ):
        """
        Assemble a sequence of images into a MP4 video.
        The FPS and other metadata are read from 'video_metadata.json'

        Args:
            image_sequence_dir (str): The file directory where the image sequence and 'video_metadata.json' reside.
            video_filepath (str): The output MP4 video's filepath.
        """    
        # 1. Double check if the input directory and output file exists.
        image_sequence_dir = image_sequence_dir.rstrip('/')
        if not os.path.isdir(image_sequence_dir):
            warn_msg = f"image_sequence_to_mp4(), the image_sequence_dir '{image_sequence_dir}' doesn't exist."
            self.logger.warning(warn_msg)
            return
        
        if os.path.isfile(video_filepath):
            os.remove(video_filepath)

        # 2. Get the metadata of the image sequence, including FPS
        video_metadata_filepath = f"{image_sequence_dir}/{self.video_metadata_filename}"
        with open(video_metadata_filepath, 'r') as file:
            self.video_metadata = json.load(file)  

        # 3. Get all image paths in the directory, sorted numerically
        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        image_files = [f for f in os.listdir(image_sequence_dir) if f.lower().endswith(image_extensions)]

        image_files = sorted(
            [os.path.join(image_sequence_dir, f) for f in image_files],
            key=lambda x: int(''.join(filter(str.isdigit, x)))  # Sort by numeric part of filename
        )
        
        if not image_files:
            warn_msg = f"image_sequence_to_mp4(), No image files found in the directory '{image_sequence_dir}'."
            self.logger.warning(warn_msg)
            return
        
        # 4. Create a video clip from the image sequence
        fps = round(self.video_metadata["fps"])
        clip = ImageSequenceClip(image_files, fps=fps)
        
        # 5. Write the video file (MP4 format)
        clip.write_videofile(
            video_filepath,
            codec="libx264",  # Required for MP4 (H.264 codec)
            audio_codec="aac"  # Audio codec (even if no audio, recommended for MP4 compatibility)
        )

        # 6. Print out the log message.
        clip.close()

        info_msg = f"image_sequence_to_mp4(), convert the image sequence in file directory '{image_sequence_dir}', "
        info_msg += f"to a video file '{video_filepath}', with fps={fps}."
        self.logger.info(info_msg)


    def convert_to_mp4(
            self, 
            raw_filepath: str="",
            mp4_filepath: str=""
        ) -> bool:
        """
        Convert a video file to MP4 file. 
        For example, the MOV video file shot by iPhone, sometime cannot be read in by Moviepy, 
        because the MOV video file is of HDR color space, instead of the standard color space is SDR.

        Args:
            raw_filepath (str): The input MOV video filepath, 
            mp4_filepath (str): The output MP4 video filepath.

        Returns:
            True: if conversion completes successfully. 
            False: if conversion fails.
        """
        # 1. Double check if the input video file and the output file exist.
        if not os.path.isfile(raw_filepath):
            warn_msg = f"convert_to_mp4(), the input file '{raw_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return False
        
        if os.path.isfile(mp4_filepath):
            os.remove(mp4_filepath)

        
        # 2. Construct the FFMpeg command. 
        command = [
            'ffmpeg',
            '-i', raw_filepath,       # Input file
            
            # Video stream encoding parameters
            '-c:v', 'libx264',          # H.264 video codec
            '-crf', '23',               # Quality factor (23 is default, lower is higher quality)
            '-preset', 'medium',        # Encoding speed/efficiency tradeoff
            
            # Audio stream encoding parameters
            '-c:a', 'aac',              # AAC audio codec
            '-b:a', '128k',             # Audio bitrate
            
            mp4_filepath             # Output file
        ]
        command_str = ' '.join(command)

        # 3. Construct the FFMpeg command. 
        info_msg = f"convert_to_mp4(), starting FFmpeg transcoding from MOV to MP4 (High Quality)..."
        self.logger.info(info_msg)

        try:
            # Use subprocess.run to execute the command.
            # check=True: raises an exception if the command returns a non-zero exit code (failure).
            # capture_output=True: captures stdout/stderr (optional, useful for debugging).
            # text=True: decodes output as text.
            result = subprocess.run(command, check=True, capture_output=True, text=True)

        except subprocess.CalledProcessError as e:
            warn_msg = f"convert_to_mp4(), FFmpeg Execution Failed, "
            warn_msg += f"\n\t Error executing command: {command_str}"
            warn_msg += f"\n\t FFmpeg stderr error message: '{e.stderr}'"
            self.logger.warning(warn_msg)
            return False

        info_msg = f"convert_to_mp4(), FFmpeg transcoding from MOV to MP4 (High Quality) completes successfully."
        info_msg += f"\n\t The output MP4 video file is saved to: '{mp4_filepath}'."
        self.logger.info(info_msg)
        return True
        

    def _load_video_file(
            self,
            input_video_filepath: str=""
        ) -> object:
        """
        Execute moviepy's 'video_obj = VideoFileClip(input_video_filepath)'. 
        If the input video file cannot be read in by 'VideoFileClip()',
        we convert it to a temporary MP4 file first, after then read in the MP4 using 'VideoFileClip'.

        Args:
            input_video_filepath (str): The filepath of the input video file, 
                the valid suffices of the images are (".MP4", ".MOV", ".WEBM"), case insensitive. 

        Returns:
            Return the 'video_obj' created by VideoFileClip(input_video_filepath)'. 
            If None, it means 'VideoFileClip()' fails.
        """
        # 1. Check if the 'input_video_filepath' exists.
        if not os.path.isfile(input_video_filepath):
            warn_msg = f"_load_video_file(), the input '{input_video_filepath}' video file doesn't exist."
            self.logger.warning(warn_msg)
            return None
        
        # 2. Retrieve the video properties, if needed, convert the MOV file to a temporary MP4 file before retrieval.
        try:
            video_obj = VideoFileClip(input_video_filepath)
            return video_obj
        
        except Exception as e:
            warn_msg = f"_load_video_file(), the input video file '{input_video_filepath}' cannot be read in by 'VideoFileClip()'. "
            warn_msg += f"We will convert it to .mp4 file, and load the newly created .mp4 file."
            self.logger.warning(warn_msg)

            input_video_basename = os.path.basename(input_video_filepath)
            tmp_mp4_filepath = f"/tmp/{input_video_basename}.mp4"

            if self.convert_to_mp4(input_video_filepath, tmp_mp4_filepath):
                video_obj = VideoFileClip(tmp_mp4_filepath)

                if os.path.isfile(tmp_mp4_filepath):
                    pass  # os.remove(tmp_mp4_filepath)
                return video_obj
            else:
                warn_msg = f"_load_video_file(), the input MOV video file '{input_video_filepath}' cannot be converted to MP4 file."
                self.logger.warning(warn_msg)

                if os.path.isfile(tmp_mp4_filepath):
                    pass  # os.remove(tmp_mp4_filepath)
                return None
                    

    def subclip(
            self, 
            input_video_filepath: str="",
            start_time: int | str = 0,
            end_time: int | str = 0,
            output_mp4_filepath: str=""                 
        ):
        """
        Split a video into several segjements. 
        Notice that when the MOV video file shot by iPhone, sometime cannot be read in. 
        Because the MOV video file is of HDR color space, instead of the standard color space is SDR.

        Args:
            input_video_filepath (str): The filepath of the input video file, 
                the valid suffices of the images are (".MP4", ".MOV", ".WEBM"), case insensitive. 
            start_time (int | str), end_time (int | str): 
                the start and end times in seconds (int) or as string with the format "HH:MM:SS.µS"
            output_mp4_filepath (str): The output MP4 video's filepath.
        """
        # 1. Double check if the input video file and output file exist.
        if not os.path.isfile(input_video_filepath):
            warn_msg = f"subclip(), the input_video_filepath '{input_video_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return

        dir_path, file_name = os.path.split(output_mp4_filepath)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        if os.path.isfile(output_mp4_filepath):
            os.remove(output_mp4_filepath)


        # 2. Retrieve the video properties, if needed, convert the MOV file to a temporary MP4 file before retrieval.
        video_obj = self._load_video_file(input_video_filepath)

        if video_obj is None:
            warn_msg = f"subclip(), the input video file '{input_video_filepath}' cannot be loaded by 'VideoFileClip()'."
            self.logger.warning(warn_msg)
            return 
        
        # 3. Get a subclip from the video object. 
        if start_time < video_obj.start: start_time = video_obj.start
        if end_time > video_obj.end: end_time = video_obj.end

        subclip = video_obj.subclipped(start_time, end_time)

        # 4. Write the video file (MP4 format)
        subclip.write_videofile(
            output_mp4_filepath,
            codec="libx264",  # Required for MP4 (H.264 codec)
            audio_codec="aac"  # Audio codec (even if no audio, recommended for MP4 compatibility)
        )

        # 5. Print out the log message.
        video_obj.close()
        subclip.close()

        info_msg = f"subclip(), take a segment from the original video file '{input_video_filepath}', "
        info_msg += f"to a video file '{output_mp4_filepath}'."
        self.logger.info(info_msg)



    def concatenate(
            self,
            input_video_filepaths: list=[],
            output_mp4_filepath: str="" 
        ):
        """
        Concatenate multiple video files to be a long video file. 
        Notice that if the input videos do not have the same resolution, 
        the output video will have the height of the highest video and the width of the widest video of the list. 
        All the video with smaller dimensions will appear centered, and the color of the padding background will be transparent black.

        Args:
            input_video_filepaths (list): A list of filepaths to be concatenated. 
            output_mp4_filepath (str): The output MP4 video filepath. 
        """
        # 1. Read in the input videos.
        video_objects = []
        for video_filepath in input_video_filepaths:
            video_obj = self._load_video_file(video_filepath)

            if video_obj is None:
                warn_msg = f"concatenate(), the input video file '{video_filepath}' cannot be loaded by 'VideoFileClip()'."
                self.logger.warning(warn_msg)
                continue
        
            video_objects.append(video_obj)

        # 2. Concatenate multiple videos. 
        info_msg = f"concatenate(), start to concatenate multiple videos '{input_video_filepaths}', "
        info_msg += f"to a long video file '{output_mp4_filepath}'..."
        self.logger.info(info_msg)

        final_clip = concatenate_videoclips(
            video_objects,
            method="compose",
            transition=None, 
            bg_color=(0, 0, 0, 0),    # Transparent black.
            is_mask=False, 
            padding=0   # Duration time (seconds) during two consecutive clips. 
        )

        # 3. Write the video file (MP4 format).
        if os.path.isfile(output_mp4_filepath):
            os.remove(output_mp4_filepath)

        final_clip.write_videofile(
            output_mp4_filepath,
            codec="libx264",  # Required for MP4 (H.264 codec)
            audio_codec="aac"  # Audio codec (even if no audio, recommended for MP4 compatibility)
        )

        # 4. Print out the log message.
        for video_clip in video_objects:
            video_clip.close()
        final_clip.close()

        info_msg = f"concatenate(), concatenation of multiple videos '{input_video_filepaths}', "
        info_msg += f"to a long video file '{output_mp4_filepath}' completes successfully."
        self.logger.info(info_msg)

    
    def black_and_white(
            self,
            colorful_video_filepath: str="",
            gray_video_filepath: str="",
            rgb_weights: list=[1.0, 1.0, 1.0]
        ):
        """
        Convert a colorful video file to a gray MP4 file. 

        Args:
            colorful_video_filepath (str): The input colorful video filepath. 
            gray_video_filepath (str): The output black-and-white video filepath.
            rgb_weights (list): The weights for the different color channels. 
                For example,  [0.1, 0.1, 0.8] will make areas with a lot of blue appear brighter in the output.
        """     
        # 1. Double check if the input and output video filepath exist.
        if not os.path.isfile(colorful_video_filepath):
            warn_msg = f"black_and_white(), the input colorful_video_filepath '{colorful_video_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return
        
        if os.path.isfile(gray_video_filepath):
            os.remove(gray_video_filepath)

        colorful_clip = self._load_video_file(colorful_video_filepath)

        # 2. Convert colorful video filepath to a black-and-white one.
        info_msg = f"black_and_white(), Start to convert a colorful_video_filepath '{colorful_video_filepath}' "
        info_msg += f"to a black and white one '{gray_video_filepath}', with RGB weights: '{rgb_weights})' ..."
        self.logger.info(info_msg)

        gray_clip = colorful_clip.with_effects(
            [vfx.BlackAndWhite(
                RGB=rgb_weights,
                preserve_luminosity=True
            )]
        )
        
        # 3. Write the output file (preserving audio)
        gray_clip.write_videofile(
            gray_video_filepath, 
            codec='libx264',
            audio_codec='aac',
            logger=None
        )
        
        # 4. Print out the log
        colorful_clip.close()
        gray_clip.close()

        info_msg = f"black_and_white(), The convertion of a colorful_video_filepath '{colorful_video_filepath}' "
        info_msg += f"to a black and white one '{gray_video_filepath}', with RGB weights: '{rgb_weights})' completes successfully."
        self.logger.info(info_msg)


    # NOT YET COMPLETED !!    
    def overlay(
            self, 
            raw_filepath: str="",
            mp4_filepath: str="",
            subtitle_text: str="",
            subtitle_font_size: int=30,
            subtitle_position: list=[0, 0],
            subtitle_time_range: list=[0, 0],
            image_filepath: str="",
            image_width: int=0,
            image_position: list=[0, 0], 
            image_time_range: list=[0, 0]
        ):
        """
        Overlay text and image to the input raw_filepath.

        Args:
            raw_filepath (str): The input video filepath, 
            mp4_filepath (str): The output MP4 video filepath, with overlaid subtitle text and image. 

            subtitle_text (str): The text that is displayed over the raw_filepath.
                It can be either Chinese or English, but with fixed font. 
            subtitle_font_size (int): The size of the font. 
            subtitle_position (list): The relative distance from the top left corner of the raw_filepath.
                e.g. [0.4, 0.7] is at 40% of the width, 70% of the height.
            subtitle_time_range (list): 
                The start and end times in seconds (int) or as string with the format "HH:MM:SS.µS"

            image_filepath (str): The image that is displayed over the raw_filepath.
            image_width (int): The width of the image when displayed over the raw_filepath.
                The image height will be resized proportionally.
            image_position (list): The relative distance from the top left corner of the raw_filepath.
                e.g. [0.4, 0.7] is at 40% of the width, 70% of the height.
            image_time_range (list): 
                The start and end times in seconds (int) or as string with the format "HH:MM:SS.µS"
        """
        # 1. Double check if raw_filepath, mp4_filepath, image_filepath exist.
        if not os.path.isfile(raw_filepath):
            warn_msg = f"overlay(), the input video file '{raw_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return
        
        if os.path.isfile(mp4_filepath):
            warn_msg = f"overlay(), the output video file '{mp4_filepath}' already exists. We will delete it, and create a new one."
            self.logger.warning(warn_msg)
            os.remove(mp4_filepath)  

        if image_filepath and not os.path.isfile(image_filepath):
            warn_msg = f"overlay(), the input image file '{image_filepath}' doesn't exist."
            self.logger.warning(warn_msg)
            return
        elif image_filepath:
            image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            if not image_filepath.lower().endswith(image_extensions):
                warn_msg = f"overlay(), the image file '{image_filepath}' does not have a valid image extension."
                self.logger.warning(warn_msg)     
                return   

        # Load the main video clip
        video_clip = self._load_video_file(raw_filepath)
        if video_clip is None:
            warn_msg = f"overlay(), the input video file '{raw_filepath}' cannot be loaded."
            self.logger.warning(warn_msg)
            return
        
        W, H = video_clip.size
        clip_list = [video_clip]  # Start with the main video clip
            
        # 2. Create the subtitle text.
        subtitle_text = subtitle_text.strip()
        if len(subtitle_text.strip()) > 0:
            try:                
                text_clip = TextClip(
                    font=self.NotoSansSC_Light,
                    text=subtitle_text,
                    font_size=subtitle_font_size,
                    color='white',
                    method='label', # method='caption', 
                    # size=(0.8*W, 0.0),
                    # transparent=True
                )
                
                # Scale it down to the desired size, which gives us extra space around the text
                # text_clip = text_clip.resized(height=subtitle_font_size * 2)
                
                # Make sure text_clip has proper duration
                text_duration = subtitle_time_range[1] - subtitle_time_range[0]
                text_clip = text_clip.with_duration(text_duration)
                
                # Position the text clip
                text_clip = text_clip.with_position(subtitle_position, relative=True)
                # text_clip = text_clip.with_position('center')
                text_clip = text_clip.with_start(subtitle_time_range[0])
                
                clip_list.append(text_clip)
                
                info_msg = f"overlay(), subtitle text '{subtitle_text}' created successfully with scaling approach"
                self.logger.info(info_msg)
            except Exception as e:
                warn_msg = f"overlay(), failed to create subtitle clip: {str(e)}"
                self.logger.warning(warn_msg)

        # 3. Create the image clip.
        if image_filepath and os.path.isfile(image_filepath):
            try:
                image_clip = ImageClip(image_filepath)
                if image_width > 0:
                    image_clip = image_clip.resized(width=image_width)
                
                # Make sure image_clip has proper duration
                image_duration = image_time_range[1] - image_time_range[0]
                image_clip = image_clip.with_duration(image_duration)
                
                # Position the image clip
                image_clip = image_clip.with_position(image_position, relative=True)
                image_clip = image_clip.with_start(image_time_range[0])
                
                clip_list.append(image_clip)
                
                info_msg = f"overlay(), image '{image_filepath}' added successfully"
                self.logger.info(info_msg)
            except Exception as e:
                warn_msg = f"overlay(), failed to create image clip from '{image_filepath}': {str(e)}"
                self.logger.warning(warn_msg)

        # 4. Overlay the subtitle text and image to the raw_filepath, to create mp4_filepath.
        info_msg = f"overlay(), start to add "
        if len(subtitle_text) > 0:
            info_msg += f"text '{subtitle_text}' "
        if image_filepath and os.path.isfile(image_filepath):
            info_msg += f"image '{image_filepath}' "
        info_msg += f"to the raw video '{raw_filepath}'..."
        self.logger.info(info_msg)

        try:
            overlaid_clip = CompositeVideoClip(clip_list)
            
            # Write the final video
            overlaid_clip.write_videofile(
                mp4_filepath,
                codec='libx264',
                audio_codec='aac'
            )
        except Exception as e:
            warn_msg = f"overlay(), failed to create composite video: {str(e)}"
            self.logger.warning(warn_msg)
            return

        # 5. Close the clips
        for clip in clip_list:
            try:
                clip.close()
            except Exception as e:
                warn_msg = f"overlay(), an exception is throwned when closing a clip. "
                warn_msg += f"\n\t The error message is '{str(e)}'"
                self.logger.warning(warn_msg)

        try:
            overlaid_clip.close()
        except Exception as e:
            warn_msg = f"overlay(), an exception is throwned when closing a clip. "
            warn_msg += f"\n\t The error message is '{str(e)}'"
            self.logger.warning(warn_msg)


        # 6. Print out the log
        info_msg = f"overlay(), "
        if len(subtitle_text) > 0:
            info_msg += f"text '{subtitle_text}' "
        if image_filepath and os.path.isfile(image_filepath):
            info_msg += f"image '{image_filepath}' "
        info_msg += f"has been added to the raw video '{raw_filepath}'."
        info_msg += f"\n\t The final video is saved at '{mp4_filepath}'."
        self.logger.info(info_msg)

    
    def usage_sample(self):
        project_dir = f"/home/robot/llamedia_studio_20251106/testing"
        input_video_filepaths = [
            f"{project_dir}/input/kdeng_greenscreen.mov",
            f"{project_dir}/input/nyu_corridor.MOV",
            f"{project_dir}/input/TrueStory.mp4",
            f"{project_dir}/input/bicycling_greenscreen.webm",
            f"{project_dir}/input/battle_field.png"
        ]
        output_video_filepaths = [
            f"{project_dir}/output/kdeng_greenscreen",
            f"{project_dir}/output/kdeng_greenscreen.mp4",
            f"{project_dir}/output/nyu_corridor_overlaid.mp4",
            f"{project_dir}/output/nyu_corridor_subclip.mp4",
            f"{project_dir}/output/TrueStory_gray.mp4",
            f"{project_dir}/output/TrueStory_subclip.mp4",
            f"{project_dir}/output/bicycling_greenscreen.mp4",
            f"{project_dir}/output/concatenated_video.mp4"
        ]


        self.overlay(
            raw_filepath=input_video_filepaths[1],
            mp4_filepath=output_video_filepaths[2],
            subtitle_text="你好, NYU! 来自北京的问候。",
            subtitle_font_size=50,
            subtitle_position=[0.2, 0.6],
            subtitle_time_range=[5, 15],
            image_filepath=input_video_filepaths[4],
            image_width=500,
            image_position=[0.2, 0.5], 
            image_time_range=[8, 18]        
        )

        """
        self.video_to_image_sequence(input_video_filepaths[0], output_video_filepaths[0])
        self.image_sequence_to_mp4(output_video_filepaths[0], output_video_filepaths[1])

        self.subclip(output_video_filepaths[2], 5, 15, output_video_filepaths[3])
        self.subclip(input_video_filepaths[2], 5, 15, output_video_filepaths[5])
        self.subclip(input_video_filepaths[0], 5, 15, output_video_filepaths[1])
        self.subclip(input_video_filepaths[3], 5, 15, output_video_filepaths[6])        
        self.black_and_white(output_video_filepaths[5], output_video_filepaths[4])

        self.concatenate([
                output_video_filepaths[2],  # nyu_corridor_overlaid.mp4 - the video with text overlay
                output_video_filepaths[5],  # TrueStory_gray.mp4 - a grayscale version of another video
                output_video_filepaths[1],  # kdeng_greenscreen.mp4 - a converted video
                output_video_filepaths[6],  # bicycling_greenscreen.mp4 - another converted video
                output_video_filepaths[4]   # TrueStory_subclip.mp4 - a subclip from the grayscale video
            ], 
            output_video_filepaths[7]
        )
        """

    @staticmethod
    def usage_demo():
        movie_editor = VideoEditor()
        movie_editor.usage_sample()

