import cv2
import numpy as np
import os
import subprocess

class OpencvRenderer:
    def __init__(self):
        self.logger = None
        self.resolution_x=0
        self.resolution_y=0
        self.frame_start=0
        self.frame_end=0

        self.fps = 0.0
        self.fps_base = 1.0
        self.codec = 'mp4v'

        self.video_writer = None
        self.tmp_output_filepath = ""
        self.output_filepath = ""

        try:
            from logger.logger import Logger
            self.logger = Logger("OpencvRenderer").getLogger()
            self.logger.info(f"OpencvRenderer class initialized.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize OpencvRenderer class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize OpencvRenderer class, error message: '{e}'")
 

    def set_video_settings(
            self, 
            resolution_x=0,
            resolution_y=0,
            frame_start=0,
            frame_end=0,
            fps=0,
            output_filepath=""
        ):
        """
        Set the Blender rendering engine setting to prepare the rendering of a MP3 audio.

        Args:
            resolution_x (int): The width of the rendered output in pixels.
            resolution_y (int): The height of the rendered output in pixels.
            frame_start (int): The index of starting frame.
            frame_end (int): The index of end frame.
            fps (float): Base frame rate.
                Notice that, fps_base is forcely set to 1.0. 
            output_filepath (str): The full path for the output file.

        The popular resolutions are:
            - 480p: 854 * 480 (16:9)
            - 360p: 640 * 360 (16:9)
            - 720p (HD): 1280 * 720 (16:9)
            - 1080p (Full HD/FHD): 1920 * 1080 (16:9)
            - 720p (HD vertical 9:16): 720 * 1280 
            - 1080p (Full HD Mobile vertical 9:16): 1080 * 1920
        """ 
        if len(output_filepath) > 0:
            dir_path = os.path.dirname(output_filepath)
            base_filename = os.path.basename(output_filepath)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            self.tmp_output_filepath = f"/tmp/{base_filename}"
            self.output_filepath = output_filepath.strip()

        if (resolution_x > 0 and resolution_y > 0):
            self.resolution_x = resolution_x
            self.resolution_y = resolution_y

        if (frame_start > 0 and frame_end > 0):
            self.frame_start = frame_start
            self.frame_end = frame_end

        if fps > 0:
            self.fps = fps


    def start_rendering(self):
        """
        Start the rendering process.
        """
        # Check if there's an active camera in the scene
        fourcc = cv2.VideoWriter_fourcc(*(self.codec))
        self.video_writer = cv2.VideoWriter(
            self.tmp_output_filepath, 
            fourcc, 
            self.fps, 
            (self.resolution_x, self.resolution_y)
        )


    def frame_rendering(self, frame):
        """
        Write a frame to the OpenCV video_writer.

        Args:
            frame (obj): An numpy object of (resolution_y, resolution_x, (rgb)).
                e.g. frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
        """ 
        if self.video_writer is None:
            warn_msg = f"frame_rendering(), self.video_writer is None"
            self.logger.warn(warn_msg)
            return
        
        if not self.video_writer.isOpened():
            warn_msg = f"frame_rendering(), self.video_writer is not openned."
            self.logger.warn(warn_msg)
            return
        
        self.video_writer.write(frame)
        

    def end_rendering(self):
        """
        End the rendering process. 
        Using ffmeg to convert the output file to support displaying in chrome browser.
        """
        if self.video_writer is not None:
            self.video_writer.release()

        ffmpeg_command = [
            'ffmpeg',
            '-i', self.tmp_output_filepath,
            '-vcodec', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-y', # Overwrite output file if it exists
            self.output_filepath
        ]
        
        try:
            result = subprocess.run(
                ffmpeg_command, 
                check=True, 
                capture_output=True, 
                text=True
            )

            info_msg = f"end_rendering(), Successfully generate a mp4 video file: '{self.output_filepath}'."
            info_msg += f"\n\t Also, the temporary file '{self.tmp_output_filepath}' has been deleted."
            self.logger.info(info_msg)
            debug_msg = f"end_rendering(), {result.stderr}"
            self.logger.debug(f"{debug_msg}")

        except FileNotFoundError:
            warn_msg = f"end_rendering(), 'ffmpeg' command not found."
            warn_msg += f"\n\t Please install ffmpeg on your system to automatically re-encode the video."
            self.logger.warn(warn_msg)

        except subprocess.CalledProcessError as e:
            warn_msg = f"end_rendering(), FFMPEG returned non-zero exit status '{e.returncode}': '{e.stderr}'"
            self.logger.warn(warn_msg)


        try:
            if os.path.exists(self.tmp_output_filepath):
                os.remove(self.tmp_output_filepath)
        except PermissionError:
            warn_msg = f"end_rendering(), permission denied. Cannot delete '{self.tmp_output_filepath}'."
            self.logger.warn(warn_msg)
        except IsADirectoryError:
            warn_msg = f"end_rendering(), '{self.tmp_output_filepath}' is a directory, not a file. "
            self.logger.warn(warn_msg)
        except OSError as e:
            warn_msg = f"end_rendering(), an OS error occurred during deletion: \n\t'{e}'\n"
            self.logger.warn(warn_msg)


    def usage_sample(
            self,
            output_filepath=""   
        ):
        """
        As a usage sample, generates a simple video file with colored frames.

        Args:
            output_filename (str): The name of the output video file.
        """
        self.set_video_settings(
            resolution_x=640, 
            resolution_y=360,  
            frame_start=1,
            frame_end=240,
            fps=24,
            output_filepath=output_filepath
        )

        self.start_rendering()

        for i in range(self.frame_start, self.frame_end+1):
            # Create a blank frame (black)
            frame = np.zeros((self.resolution_y, self.resolution_x, 3), dtype=np.uint8)

            # Draw a moving colored rectangle on the frame
            color = (i * 2 % 256, (i + 50) * 2 % 256, (i + 100) * 2 % 256)  # Dynamic color
            cv2.rectangle(
                frame, 
                (i * 5 % self.resolution_x, i * 3 % self.resolution_y), 
                (i * 5 % self.resolution_x + 100, i * 3 % self.resolution_y + 80), 
                color, 
                -1  # -1 for filled rectangle
            )  

            # Write the frame to the video file
            self.frame_rendering(frame)

        self.end_rendering()

    
    @staticmethod
    def run_demo():
        cv2_renderer = OpencvRenderer()
        output_filepath = "/home/robot/movie_blender_studio/output/sample_opencv_video.mp4"
        cv2_renderer.usage_sample(output_filepath)
        print(f"\n[INFO] Successfully generate a mp4 sample video file: '{output_filepath}'\n")


if __name__ == "__main__":
    OpencvRenderer.run_demo()