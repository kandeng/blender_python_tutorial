import bpy
import os
import json
import shutil
import datetime

class ImageSequenceCompositor():
    def __init__(self):
        self.logger = None
        self.scene = None
        self.sequence_editor = None 
        self.renderer = None
        self.movie_strip = None
        self.image_compositor = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("ImageSequenceCompositor").getLogger()

            from camera.renderer import Renderer
            self.renderer = Renderer()

            from compositing.image_compositor import ImageCompositor
            self.image_compositor = ImageCompositor()

            # Create a new sequence editor if it doesn't exist
            self.scene = bpy.context.scene
            if not self.scene.sequence_editor:
                self.scene.sequence_editor_create()
            self.sequence_editor = self.scene.sequence_editor 

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize ImageSequenceCompositor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize ImageSequenceCompositor class, error message: '{str(e)}'")
        

    def convert_video_to_image_sequence(
            self, 
            video_filename="", 
            output_dir="", 
            output_format='PNG'
        ):
        """
        Converts a video file into a series of images with sortable names.

        Args:
            video_filename (str): The full file name including the file path of the video file. 
                The valid suffices of the video file are ('mp4', 'mov', etc), case insensitive. 
            output_dir (str): The full file directory name, in which the frame images are stored. 
            output_format (str): The image format of the image sequence. 
                Usually PNG is a better choice than JPEG, because PNG includes the alpha channel.
        """        
        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Clear existing VSE movie_strip objects
        for strip in self.sequence_editor.sequences_all:
            self.sequence_editor.sequences.remove(strip)

        # Use the direct API method to add the movie strip.
        # This does not require a context override and is the most reliable way.
        self.movie_strip = self.sequence_editor.sequences.new_movie(
            name=os.path.basename(video_filename),
            filepath=video_filename,
            channel=1,
            frame_start=1
        )
        
        if not self.movie_strip:
            warn_msg = f"convert_video_to_image_sequence(), the movie strip was not created as expected."
            self.logger.warn(warn_msg)
            return 
        
        # Set the scene's start and end frames to match the video
        self.scene.frame_start = int(self.movie_strip.frame_start)
        self.scene.frame_end = int(self.movie_strip.frame_final_duration)

        # Set render output path and file format to render the frame images.
        self.scene.render.filepath = os.path.join(output_dir, "frame_####")
        self.scene.render.image_settings.file_format = output_format

        bpy.ops.render.render(animation=True)
        
        # Print out the info log.
        info_msg = f"convert_video_to_image_sequence(), successfully convert '{video_filename}' to "
        frame_num = self.scene.frame_end - self.scene.frame_start + 1
        info_msg += f"a sequence of frame images stored in '{output_dir}',"
        info_msg += f"\n\t totally {frame_num} frame images, fps={self.movie_strip.fps}."
        self.logger.info(info_msg)


    def validate_image_sequence(
            self,
            image_seq_dir=""
        ) -> bool:
        """
        Double check if the image files in the image sequence directory are valid.

        Args:
            image_seq_dir (str): The full file directory name, in which the frame images are stored, 
                the filenames of the images are 'frame_###' where '###' are indices in order. 

        Returns:
            True: if all the files of the image sequence are valid. False: otherwise.
        """  
        # 1. Verify if the input image sequence directory exists.
        if not os.path.isdir(image_seq_dir):
            warn_msg = f"assemble_image_sequence_to_video(), input image sequence file directory is not found at '{image_seq_dir}'."
            self.logger.warn(warn_msg)
            return False

        # 2. Verify the number of files in the directory that start with "frame_" is not 0.
        filename_list = []
        for filename in os.listdir(image_seq_dir):
            full_path = os.path.join(image_seq_dir, filename)
            if os.path.isfile(full_path) and filename.startswith("frame_"):
                filename_list.append(full_path)

        if len(filename_list) == 0:
            warn_msg = f"assemble_image_sequence_to_video(), no image file named as 'frame_###' is not found at '{image_seq_dir}'."
            self.logger.warn(warn_msg)
            return False
        
        # 3. Verify if all the frame images are of the same format, including 'png', 'jpg', 'jpeg'.
        file_format_list = []
        for idx, filename in enumerate(filename_list):
            file_extension = os.path.splitext(filename)[1].lstrip('.')
            if file_extension not in file_format_list:
                file_format_list.append(file_extension)

        if len(file_format_list) > 1:
            warn_msg = f"assemble_image_sequence_to_video(), multiple file formats are found in the image sequence: {file_format_list}."
            self.logger.warn(warn_msg)
            return False

        return True     


    def assemble_image_sequence_to_video(
            self, 
            image_seq_dir="", 
            output_filename=""  
        ):
        """
        Assemble a sequence of images, whose filenames are 'frame_###' where '###' are indices in order,
            into a mp4 video file.

        Args:
            image_seq_dir (str): The full file directory name, in which the frame images are stored, 
                the filenames of the images are 'frame_###' where '###' are indices in order. 
            output_filename (str): The full file name of the output file, 
                the format of the video is MPEG4, hence, the suffix of the video file must be '.mp4'.
        """  
        #--------------------------------
        # 1. Verification
        #--------------------------------
        is_valid = self.validate_image_sequence(image_seq_dir)
        if not is_valid:
            warn_msg = f"assemble_image_sequence_to_video(), the files in the image sequence directory are not valid."
            self.logger.warn(warn_msg)
            return
        
        filename_list = []
        for filename in os.listdir(image_seq_dir):
            full_path = os.path.join(image_seq_dir, filename)
            if os.path.isfile(full_path) and filename.startswith("frame_"):
                filename_list.append(full_path)

        #---------------------------------------------------
        # 2. Assemble the image sequence into a mp4 video
        #---------------------------------------------------

        # 1. Set up a temporary video file directory to fit the requirement of renderer.compile_images_to_video()
        full_filename = os.path.basename(output_filename)
        base_filename = os.path.splitext(full_filename)[0]

        now = datetime.datetime.now()
        time_str = now.strftime('%Y%m%d_%H%M%S')

        tmp_video_dir = f"/tmp/{base_filename}_{time_str}"
        video_fps = round(self.movie_strip.fps)

        # 2. Use renderer's API to assemble the image sequence into a MP4 video file.
        self.renderer.compile_images_to_video(
            input_images_dir=image_seq_dir, 
            output_video_dir=tmp_video_dir,
            image_extension="png", 
            frame_duration=len(filename_list),
            fps=video_fps
        )      
        info_msg = f"assemble_image_sequence_to_video(), the temporary video file is in '{tmp_video_dir}' directory,"
        info_msg += f"\n\t totally {len(filename_list)} frames, fps={video_fps}."
        self.logger.info(info_msg)

        #--------------------------------
        # 3. Clean up
        #--------------------------------

        # 1. Find the temporary video file.
        tmp_video_list = []
        for filename in os.listdir(tmp_video_dir):
            full_path = os.path.join(tmp_video_dir, filename)
            if os.path.isfile(full_path) and filename.startswith("video_") and filename.endswith(".mp4"):
                tmp_video_list.append(full_path)

        if len(tmp_video_list) != 1:
            warn_msg = f"assemble_image_sequence_to_video(), '{tmp_video_dir}' directory contains multiple mp4 files."
            warn_msg += f"\n\t we only use the first mp4 file. "
            self.logger.warn(warn_msg)

        # 2. Rename the temporary video file.
        tmp_filename = f"{tmp_video_list[0]}"
        tmp_video_filename = f"{tmp_video_dir}/{base_filename}.mp4"
        os.rename(tmp_filename, tmp_video_filename)


        # 3. Copy the temporary video file to the destination directory
        dest_dir = os.path.dirname(output_filename)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)

        shutil.copy(tmp_video_filename, output_filename)

        # 4. Delete the temporary directory and all its contents
        shutil.rmtree(tmp_video_dir)

        # 5. Print the info
        info_msg = f"assemble_image_sequence_to_video(), assemble the image sequence from '{image_seq_dir}' directory, "
        info_msg += f"\n\t to '{output_filename}' file."
        self.logger.info(info_msg)


    def cinematic_mystify_image_sequence(
            self, 
            input_image_seq_dir="", 
            output_image_seq_dir=""  
        ):
        """
        Assemble a sequence of images, whose filenames are 'frame_###' where '###' are indices in order,
            into a mp4 video file.

        Args:
            input_image_seq_dir (str): The full input file directory name, in which the input frame images are stored, 
                the filenames of the input images are 'frame_###' where '###' are indices in order. 
            output_image_seq_dir (str): The full output file directory name, in which the output frame images are stored, 
                the filenames of the output images keep the same as the input, 'frame_###' where '###' are indices in order. 
        """  
        #--------------------------------
        # 1. Verification
        #--------------------------------
        is_valid = self.validate_image_sequence(input_image_seq_dir)
        if not is_valid:
            warn_msg = f"assemble_image_sequence_to_video(), the files in the image sequence directory are not valid."
            self.logger.warn(warn_msg)
            return
        
        input_filename_list = []
        for filename in os.listdir(input_image_seq_dir):
            full_path = os.path.join(input_image_seq_dir, filename)
            if os.path.isfile(full_path) and filename.startswith("frame_"):
                input_filename_list.append(full_path)

        #---------------------------------------------------
        # 2. Cinematically mystify each frame image
        #---------------------------------------------------
        for input_filename in input_filename_list:
            filename = os.path.basename(input_filename)
            output_image_seq_dir = output_image_seq_dir.rstrip("/")
            output_filename = f"{output_image_seq_dir}/{filename}"

            self.image_compositor.cinematic_mystery(
                input_image_filename=input_filename,
                output_image_filename=output_filename, 
            )

        info_msg = f"cinematic_mystify_image_sequence(), mystify the image sequence from '{input_image_seq_dir}' directory, "
        info_msg += f"\n\t to '{output_image_seq_dir}' directory."
        self.logger.info(info_msg)



    @staticmethod
    def run_demo():
        # Example usage:
        # Make sure to change these paths to your actual video file and desired output directory.
        video_input_filename = "/home/robot/movie_blender_studio/input/nyu_corridor.MOV"
        original_image_seq_directory = "/home/robot/movie_blender_studio/nyu_video_output/nyu_corridor_original"
        cinematic_image_seq_directory = "/home/robot/movie_blender_studio/nyu_video_output/nyu_corridor_cinematic"
        video_output_filename = "/home/robot/movie_blender_studio/nyu_video_output/nyu_corridor.mp4"

        # For this script to work, you must be running it inside Blender's scripting environment.
        image_sequence_compositor = ImageSequenceCompositor()

        image_sequence_compositor.convert_video_to_image_sequence(
            video_filename=video_input_filename, 
            output_dir=original_image_seq_directory
        )       

        image_sequence_compositor.cinematic_mystify_image_sequence(
            input_image_seq_dir= original_image_seq_directory, 
            output_image_seq_dir=cinematic_image_seq_directory
        )

        image_sequence_compositor.assemble_image_sequence_to_video(
            image_seq_dir=cinematic_image_seq_directory, 
            output_filename=video_output_filename
        )
