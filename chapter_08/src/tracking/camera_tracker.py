import cv2
import numpy as np
import os
import json
import subprocess


"""
The purpose of camera tracking is that, given a video, to guess the motion of the camera.

Counter-intuitively, in the viewpoint of camera, the motion of the camera itself only contains 'pan' and 'tilt', 
just like the camera is on a tripod, while the tripod base remains stationary.

1. Pan (Yaw)

The camera rotates around the vertical Z-axis. Pan may allow the camera to follow a moving subject, 
or reveal a wide scene gradually, known as a panorama shot.

2. Tilt (Pitch)

The camera rotates around the horizontal X-axis. Tilt may allows the camera to show the height of an object (like a building), 
or reveal something above or below the frame.

The camera tracking consists of two steps. 
Step 1: Find good things to track. (goodFeaturesToTrack)
Step 2: Follow those things from one frame to the next. (calcOpticalFlowPyrLK)

1. cv2.goodFeaturesToTrack() - Finding the "Features"

    - Input: The function takes a grayscale image (in this case, the first frame of the video).

    - Goal: Its job is to identify points in the image that are "strong" and "unique" enough to be easily tracked. 
        Flat surfaces or simple straight edges are bad for tracking because they are ambiguous. 
        For example, if you are looking at a blank white wall, it's impossible to tell if the camera is moving.

    - Principle (Shi-Tomasi Corner Detection): The algorithm finds corners. 
        A corner is an ideal feature because it has sharp intensity changes in multiple directions. 
        The function scans the image and calculates a "corner quality" score for every pixel.
        It then discards any corners with a score below a certain qualityLevel.
        Finally, to ensure the tracked points are spread out and not all clustered in one spot, 
        it enforces a minDistance between the corners it selects.

    - Output: The function returns a list of the coordinates of the best corners it found. 
        In the script, this list is stored in the p0 variable, representing the initial points to be tracked.


2. cv2.calcOpticalFlowPyrLK() - Calculating the "Optical Flow"

    - Input: This function takes the previous frame (prev_frame_gray), the current frame (curr_frame_gray), 
        and the list of points to track from the previous frame (p0).

    - Goal: For each point in p0, it tries to find its new location in the current frame. 
        The "flow" is the motion vector that connects the old position to the new one.

    - Principle (Lucas-Kanade Optical Flow with Pyramids):
        * Core Assumption: The algorithm makes a key assumption called brightness constancy. 
            It assumes that the pixels in a small neighborhood around a feature point 
            will look almost identical in the next frame; they will just be in a different location.

        * The Lucas-Kanade (LK) Method: For each point from p0, the function looks at
            a small window of pixels around it (defined by winSize). 
            It then searches in the new frame for a window of pixels that is the most similar. 
            This search is an iterative process that tries to minimize the difference between the two windows.

        * The Pyramid (Pyr) Method: A problem arises with fast motion. 
            If a feature moves too far, the search in the next frame will fail. 
            To solve this, the algorithm uses an image pyramid. 
            It creates smaller, lower-resolution versions of both the old and new frames. 
            It first calculates the motion in the smallest, most blurred image (where the movement appears smaller). 
            It uses this result as a starting guess for the next level up in the pyramid, 
            refining the search at each step until it reaches the full-resolution image. 
            This allows it to accurately track features that move larger distances.

    - Output:
        * p1: A list containing the new coordinates of the tracked points in the current frame.
        * st (status): A list of 1s and 0s. A 1 means the corresponding point was successfully tracked. 
            A 0 means the point was "lost" (e.g., it moved out of the frame, was covered by something else, 
            or its appearance changed too much).
"""
class CameraTracker:
    def __init__(self):
        self.logger = None
        self.opencv_renderer = None
        self.video_capturer = None

        self.input_filepath = ""
        self.video_settings = {}

        # Parameters for ShiTomasi corner detection (features we want to track)
        self.feature_params = dict(
            maxCorners=200,      # Increased max corners for better Homography estimation
            qualityLevel=0.01,   # Lower quality level to find more features
            minDistance=15,      # Increased min distance for better spread
            blockSize=7          
        )

        # Parameters for Lucas-Kanade optical flow (tracking algorithm)
        self.lk_params = dict(
            winSize=(15, 15),    
            maxLevel=2,          
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )

        self.prev_frame_gray = None
        self.p0 = []
        self.cumulative_translation = np.array([0.0, 0.0], dtype=np.float64)
        self.cumulative_translation_list = []

        self.arrow_scale = 15

        self.tmp_output_filepath = ""
        self.output_filepath = ""

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("CameraTracker").getLogger()
            self.logger.info(f"CameraTracker class initialized.")

            from camera.renderer_opencv import OpencvRenderer
            self.opencv_renderer = OpencvRenderer()

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize CameraTracker class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize CameraTracker class, error message: '{e}'")


    def open_video_capturer(
            self, 
            input_filepath=""
        ):
        if not os.path.exists(input_filepath):
            warn_msg = f"open_video_capturer(), the input video file cannot be found at: '{input_filepath}'."
            self.logger.warn(warn_msg)
            return
        self.input_filepath = input_filepath.strip()

        if self.video_capturer:
            self.video_capturer.release()
            self.video_capturer = None
            
        self.video_capturer = cv2.VideoCapture(self.input_filepath)

        if not self.video_capturer.isOpened():
            warn_msg = f"open_video_capturer(), cannot open the input video file: '{input_filepath}'."
            self.logger.warn(warn_msg)


    def get_video_settings(
            self,
            input_filepath=""
        ) -> dict:
        """
        Args:
            input_filepath (str): The full path for the input video file. This is mandatory. 
                From this video, this script detects the motion of the camera, including 'pan' and 'tilt'.    

        Returns:
            first_frame (NumPy array): The first frame of the video file, represented as a NumPy array.     
        """
        video_settings = {}

        # 1. Double check if the input filepath is valid.
        self.open_video_capturer(
            input_filepath=input_filepath
        )

        # 2. Get the video settings. 
        ret, first_frame = self.video_capturer.read()
        if not ret:
            warn_msg = f"get_video_settings(), error occurs when reading the first frame of the input video file: "
            warn_msg += f"'{self.video_capturer}'."
            self.logger.warn(warn_msg)
            return None
        
        total_frames = int(self.video_capturer.get(cv2.CAP_PROP_FRAME_COUNT))
        video_settings["frame_start"] = 1
        video_settings["frame_end"] = video_settings["frame_start"] + total_frames - 1

        video_settings["fps"] = self.video_capturer.get(cv2.CAP_PROP_FPS)

        resolution_y, resolution_x, _ = first_frame.shape
        # Make sure dimensions are even numbers for better browser compatibility
        if resolution_y % 2 != 0:
            resolution_y -= 1
        if resolution_x % 2 != 0:
            resolution_x -= 1     
        video_settings["resolution_x"] = resolution_x
        video_settings["resolution_y"] = resolution_y   
        
        # 3. End the motion tracking.
        self.video_capturer.release()

        return video_settings


    def find_features(
            self,
            input_filepath=""
        ):
        # 1. Get video settings.
        if (("resolution_x" not in self.video_settings) or 
            ("resolution_y" not in self.video_settings)
            ):
            self.video_settings = self.get_video_settings(
                input_filepath=input_filepath
            )
        resolution_x = self.video_settings["resolution_x"]
        resolution_y = self.video_settings["resolution_y"]

        # 2. Get the first frame
        self.open_video_capturer(
            input_filepath=input_filepath
        )

        ret, first_frame = self.video_capturer.read()
        if not ret:
            warn_msg = f"find_features(), error occurs when reading the first frame of the input video file: "
            warn_msg += f"'{self.video_capturer}'."
            self.logger.warn(warn_msg)
            return None
        
        # 3. Find the features to track.
        first_frame = cv2.resize(
            first_frame, 
            (resolution_x, resolution_y)
        )

        self.prev_frame_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

        self.p0 = cv2.goodFeaturesToTrack(
            self.prev_frame_gray, 
            mask=None, 
            **(self.feature_params)
        )

        # 4. End the motion tracking.
        self.video_capturer.release()


    def detect_motion(
            self,
            input_filepath="",
            output_filepath=""
        ) -> list:
        """
        Execute the camera tracking process, which mainly consists of two steps.
        Step 1: Find good things to track. (goodFeaturesToTrack)
        Step 2: Follow those things from one frame to the next. (calcOpticalFlowPyrLK)

        Args:
            input_filepath (str): The full path for the input video file. This is mandatory. 
                Given this video, this function detects the motion of the camera, including 'pan' and 'tilt'.
            output_filepath (str): The full path for the output video file. This is optional. 
                In case you want to generate a mp4 video to see the camera motion, give the filepath to generate the video file.

        Returns:
            A list of pan and tilt, its length is equal to the length of input video's frame number.     
        """ 
        # 1. Initialize video capture
        self.video_settings = self.get_video_settings(
            input_filepath=input_filepath
        )

        # 2. Find the features to track.
        self.find_features(
            input_filepath=input_filepath
        )

        # 3. In case the user input an output video filepath, then render the mp4 video. 
        self.output_filepath = output_filepath.strip()
        if len(self.output_filepath) > 0:
            self.opencv_renderer.set_video_settings(
                resolution_x=self.video_settings["resolution_x"], 
                resolution_y=self.video_settings["resolution_y"],  
                frame_start=self.video_settings["frame_start"],
                frame_end=self.video_settings["frame_end"],
                fps=self.video_settings["fps"],
                output_filepath=self.output_filepath
            )
            self.opencv_renderer.start_rendering()

        # 4. Open video capturer.
        self.open_video_capturer(
            input_filepath=input_filepath
        )

        # 5. Enumerate all the frames.
        frame_idx = 0  
        while self.video_capturer.isOpened():
            frame_idx += 1
            ret, curr_frame = self.video_capturer.read()
            if not ret:
                break
            self.process_frame(curr_frame)

        # 6. End the motion tracking.
        self.video_capturer.release()
        if len(self.output_filepath) > 0:
            self.opencv_renderer.end_rendering()
        
        info_msg = f"detect_motion(), Successfully generate a mp4 video to illustrate the camera motion detection: "
        info_msg += f"\n\t'{self.output_filepath}'"
        self.logger.info(info_msg)

        # 6. Return the list of historic cumulative translations.
        return self.cumulative_translation_list


    def process_frame(
            self,
            frame=None
        ):
        """
        Process each frame of the input video. 
        Step 1: Find good things to track. (goodFeaturesToTrack)
        Step 2: Follow those things from one frame to the next. (calcOpticalFlowPyrLK)

        Args:
            frame (obj): The current frame to process. 
        """ 
        # 1. Calculate Optical Flow (Track features)
        if ((frame.shape[0] != self.video_settings["resolution_y"]) or 
            (frame.shape[1] != self.video_settings["resolution_x"])
            ):
            frame = cv2.resize(
                frame, 
                (self.video_settings["resolution_x"], self.video_settings["resolution_y"])
            )
        curr_frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        p1, st, err = cv2.calcOpticalFlowPyrLK(
            self.prev_frame_gray, 
            curr_frame_gray, 
            self.p0, 
            None, 
            **(self.lk_params)
        )

        #  Select only the good points (features successfully tracked).
        if p1 is not None and np.sum(st) > 10: # Ensure we have enough points
            good_new = p1[st == 1]
            good_old = self.p0[st == 1]
            
            # 2. Calculate Translation (Pan/Tilt) by averaging feature movement.
            #    This gives us the frame-to-frame (relative) motion.
            avg_displacement = np.mean(good_new - good_old, axis=0).flatten()
            delta_tx, delta_ty = avg_displacement

            self.cumulative_translation += avg_displacement
            cumulative_tx, cumulative_ty = self.cumulative_translation
            self.cumulative_translation_list.append((cumulative_tx, cumulative_ty))

            # 3. Update for next iteration
            self.prev_frame_gray = curr_frame_gray.copy()
            
            # Re-detect features if too few remain
            if len(good_new) < 50:
                self.p0 = cv2.goodFeaturesToTrack(
                    self.prev_frame_gray, 
                    mask=None, 
                    **(self.feature_params)
                )
            else:
                # Keep only the features that were successfully tracked
                self.p0 = good_new.reshape(-1, 1, 2)

            # 4. Render the current frame to the output video file.
            if len(self.output_filepath) > 0:
                arrow_start = (
                    self.video_settings["resolution_x"] // 2, 
                    self.video_settings["resolution_y"] // 2
                )
                arrow_end = (
                    int(arrow_start[0] + delta_tx * self.arrow_scale), 
                    int(arrow_start[1] + delta_ty * self.arrow_scale)
                )
                cumulative_pan_tilt = f"CUMULATIVE Pan: {cumulative_tx:0.2f}, Tilt: {cumulative_ty:0.2f}"
                relative_pan_tilt = f"RELATIVE Pan: {delta_tx:0.2f}, Tilt: {delta_ty:0.2f}"

                self.render_frame(
                    frame=frame,
                    arrow_start=arrow_start,
                    arrow_end=arrow_end,
                    cumulative_pan_tilt=cumulative_pan_tilt,
                    relative_pan_tilt=relative_pan_tilt
                )


    def render_frame(
            self,
            frame=None,
            arrow_start=(0, 0),
            arrow_end=(0, 0),
            cumulative_pan_tilt="",
            relative_pan_tilt=""
        ):
        # Draw the relative translation arrow (Green)
        frame = cv2.arrowedLine(
            frame, 
            arrow_start, arrow_end, 
            (0, 255, 0), 
            3, 
            tipLength=0.3
        )

        # Cumulative Text (White)
        cv2.putText(
            frame, 
            cumulative_pan_tilt, 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (255, 255, 255), 
            2
        )
        cv2.putText(
            frame, 
            "Cumulative Pan/Tilt [WHITE]", 
            (10, 70), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (255, 255, 255), 
            1
        )

        # Relative Text (Green)
        cv2.putText(
            frame, 
            relative_pan_tilt, 
            (self.video_settings["resolution_x"] - 400, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, 
            (0, 255, 0), 
            2
        )
        cv2.putText(
            frame, 
            "Relative Pan/Tilt [GREEN]", 
            (self.video_settings["resolution_x"] - 400, 70), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (0, 255, 0), 
            1
        )

        self.opencv_renderer.frame_rendering(frame)


    def apply_camera_motion(
            self, 
            input_filepath="", 
            camera_pan_tilt=[],
            output_filepath=""
        ):
        """
        Apply the camera's pan and tilt to the input video file, to mimick the viewport of the camera. 

        Args:
            input_filepath (str): The full path for the input video file. 
            camera_pan_tilt (list): The motion of the camera, including 'pan' and 'tilt'.
                Notice that the length of the camera's motion list, may NOT be equal to the number of frames of the input video.
            output_filepath (str): The full path for the output video file. 
                When the camera's viewport moves outside of the input video frame, 
                the output video frame may be regionally or totally black with alpha 0 (transparent).

        Returns:
            A list of pan and tilt, its length is equal to the length of input video's frame number.     
        """ 
        # 1. Initialize video capture
        video_settings = self.get_video_settings(
            input_filepath=input_filepath
        )

        # 2. In case the user input an output video filepath, then render the mp4 video. 
        output_filepath = output_filepath.strip()
        if len(output_filepath) > 0:
            self.opencv_renderer.set_video_settings(
                resolution_x=video_settings["resolution_x"], 
                resolution_y=video_settings["resolution_y"],  
                frame_start=video_settings["frame_start"],
                frame_end=video_settings["frame_end"],
                fps=video_settings["fps"],
                output_filepath=output_filepath
            )
            self.opencv_renderer.start_rendering()
        else:
            warn_msg = f"apply_camera_motion(), output_filepath is not given."
            self.logger.warn(warn_msg)  
            return          

        # 3. Open video capturer.
        self.open_video_capturer(
            input_filepath=input_filepath
        )

        # 4. Enumerate all the frames.
        frame_idx = 0  
        while self.video_capturer.isOpened():
            ret, curr_frame = self.video_capturer.read()
            if not ret:
                break

            motion_index = min(frame_idx, len(camera_pan_tilt) - 1)
            pan_dx, tilt_dy = camera_pan_tilt[motion_index]

            self.transform_frame(
                curr_frame, 
                pan_dx, 
                tilt_dy
            )
            frame_idx += 1

        # 5. End the motion tracking.
        self.video_capturer.release()
        self.opencv_renderer.end_rendering()
        
        info_msg = f"apply_camera_motion(), Successfully apply camera motion, and generate a video of camera's viewport:"
        info_msg += f"\n\t'{output_filepath}'."
        self.logger.info(info_msg)


    def transform_frame(
            self, 
            frame,
            pan_dx, 
            tilt_dy
        ):
        # 1. Get the frame dimensions
        h, w = frame.shape[:2]

        # 2. CRITICAL STEP: Convert the frame from BGR (3 channels) to BGRA (4 channels)
        # This adds the alpha channel, initially set to fully opaque (255).
        frame_bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

        # 3. Define the Affine Transformation Matrix (M)
        # M = [[1, 0, dx], [0, 1, dy]]
        M = np.float32([
            [1, 0, pan_dx], 
            [0, 1, tilt_dy]
        ])

        # 4. Apply the transformation
        #   Since frame_bgra has 4 channels, cv2.warpAffine will fill the exposed 
        #   areas with transparent black (0, 0, 0, 0).
        warped_frame_bgra = cv2.warpAffine(
            frame_bgra, 
            M, 
            (w, h),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0.0, 250.0, 0.0, 0) # Explicitly set fill value to transparent black
        )

        # NOTE: cv2.VideoWriter cannot render the alpha channel, so we convert back to BGR 
        # for display. The transparent areas will appear black in the window, but 
        # the 'warped_frame_bgra' variable itself holds the 4-channel transparent data,
        # ready for saving to PNG sequence or compositing in MoviePy.
        warped_frame_bgr = cv2.cvtColor(warped_frame_bgra, cv2.COLOR_BGRA2BGR)

        # 5. Add the frame to the final video.
        self.opencv_renderer.frame_rendering(warped_frame_bgr)


    def usage_sample(self):
        pan_tilt_list = self.detect_motion(
            input_filepath="/home/robot/movie_blender_studio/input/seine_river.mp4",
            output_filepath="/home/robot/movie_blender_studio/output/camera_tracking.mp4"
        )

        """
        video_settings_str = json.dumps(self.video_settings, indent=2, ensure_ascii=False)
        info_msg = f"usage_sample(), self.video_settings:"
        info_msg += f"\n{video_settings_str}"
        self.logger.info(info_msg)
        print("\n")        
        """

        """
        pan_tilt_list_str = json.dumps(pan_tilt_list, indent=2, ensure_ascii=False)
        info_msg = f"usage_sample(), len(pan_tilt_list)={len(pan_tilt_list)}:"
        info_msg += f"\n{pan_tilt_list_str}"
        self.logger.info(info_msg)        
        """

        self.apply_camera_motion(
            input_filepath="/home/robot/movie_blender_studio/input/walking_greenscreen.MOV", 
            camera_pan_tilt=pan_tilt_list,
            output_filepath="/home/robot/movie_blender_studio/output/walking_in_motion.mp4"
        )


    @staticmethod
    def run_demo():
        camera_tracker = CameraTracker()
        camera_tracker.usage_sample()


if __name__ == "__main__":
    CameraTracker.run_demo()