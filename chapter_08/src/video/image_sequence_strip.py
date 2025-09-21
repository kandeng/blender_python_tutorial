import bpy
import os
import shutil
import json
import re


class ImageSequenceStrip:
    def __init__(
            self
        ):
        self.logger = None
        self.channel = None

        self.strip_name=""       
        self.strip_content = None
        self.frame_start = 0
        self.frame_duration = 0

        self.frame_image_filenames = []
        self.scene_settings = {}
        self.scene_settings_filename = "scene_settings.json"


        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("ImageSequenceStrip").getLogger()

            from video.video_channel import VideoChannel
            if not self.channel:
                self.channel = VideoChannel()

            self.logger.info(f"ImageSequenceStrip class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize ImageSequenceStrip class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize ImageSequenceStrip class, error message: '{str(e)}'")


    def _load_image_sequence(
            self, 
            image_sequence_dir=""
        ):
        """
        Load a sequence of image files, to self.frame_image_filenames. 

        Args:
            image_sequence_dir (str): The file directory stores the image sequence, 
                the valid suffices of the images are (".JPG", ".JPEG", ".PNG", etc), case insensitive. 
        """
        frame_filenames = [f for f in os.listdir(image_sequence_dir)]
        for image_filename in frame_filenames:
            filename_with_suffix = os.path.basename(image_filename)
            filename, suffix = os.path.splitext(filename_with_suffix)
            if suffix.upper() in ['.PNG', '.JPG', '.JPEG']:
                self.frame_image_filenames.append(image_filename)

        if len(self.frame_image_filenames) == 0:
            warn_msg = f"_load_image_sequence(), no frame images are found."
            self.logger.warn(warn_msg)
            return

        self.frame_image_filenames.sort(key=lambda x: int(''.join(filter(str.isdigit, x))))

        for idx, image_filename in enumerate(self.frame_image_filenames):
            filepath=os.path.join(image_sequence_dir, image_filename)
            self.frame_image_filenames[idx] = filepath

        frame_image_filenames_str = json.dumps(self.frame_image_filenames, indent=2, ensure_ascii=False)
        debug_msg = f"_load_image_sequence(), self.frame_image_filenames:\n{frame_image_filenames_str}\n"
        # self.logger.debug(debug_msg)

        image_sequence_dir = image_sequence_dir.rstrip('/')
        scene_settings_filename = f"{image_sequence_dir}/{self.scene_settings_filename}"
        with open(scene_settings_filename, 'r') as file:
            self.scene_settings = json.load(file)



    def _get_file_list(self) -> list:
        file_list = []

        # 1. If strip_fps == scene_fps, return the full self.frame_image_filenames
        strip_fps = self.scene_settings["scene.render.fps"] 
        strip_fps_base = self.scene_settings["scene.render.fps_base"] 
        strip_fps = strip_fps / strip_fps_base

        scene_fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base 
        if strip_fps == scene_fps:
            file_list = [{"name": os.path.basename(f)} for f in self.frame_image_filenames]  
            return file_list

        # 2. Select some of the image from self.frame_image_filenames
        speed_factor = strip_fps / scene_fps
        current_index_float = 1.0

        while int(current_index_float) < len(self.frame_image_filenames):
            current_filename = self.frame_image_filenames[int(current_index_float)]
            file_list.append({"name": os.path.basename(current_filename)})

            # Increment the index by the floating-valued speed_factor
            current_index_float += speed_factor

        return file_list
    

    def _add_image_strip(
            self, 
            image_sequence_scene=None,
            image_sequence_dir="",
            frame_start=0,
            channel=0
        ):
        # 1. Create 'sequence_editor' if needed.
        if not image_sequence_scene:
            warn_msg = f"_add_image_strip(), 'image_sequence_scene' is None."
            self.logger.warn(warn_msg)
            return None
        
        if not image_sequence_scene.sequence_editor:
            image_sequence_scene.sequence_editor_create()
        sequencer = image_sequence_scene.sequence_editor


        # 2. Find or create a sequence area for 'bpy.ops' context.
        sequencer_area = None
        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                sequencer_area = area
                break        

        temp_area_change = False
        if not sequencer_area and bpy.context.screen.areas:
            sequencer_area = bpy.context.screen.areas[0]
            original_area_type = sequencer_area.type
            sequencer_area.type = 'SEQUENCE_EDITOR'
            temp_area_change = True


        # 3. Create image sequence strip using 'bpy.ops' with proper context 
        files = self._get_file_list() 
        try:
            if sequencer_area:
                with bpy.context.temp_override(area=sequencer_area, scene=image_sequence_scene):
                    bpy.ops.sequencer.image_strip_add(
                        directory=image_sequence_dir,
                        files=files,
                        relative_path=False,
                        frame_start=frame_start,
                        channel=channel
                    )
            else:
                warn_msg = f"_add_image_strip(), fallback for 'image_strip_add': "
                warn_msg += f"try without context override."
                self.logger.warn(warn_msg)

                bpy.ops.sequencer.image_strip_add(
                    directory=image_sequence_dir,
                    files=files,
                    relative_path=False,
                    frame_start=frame_start,
                    channel=channel
                )
        except Exception as e:
            warn_msg = f"_add_image_strip(), exception thrown by 'image_strip_add': \n\t{str(e)}\n"
            self.logger.warn(warn_msg)
            return None         


        # 4. Restore area type if we changed it temporarily
        if temp_area_change:
            sequencer_area.type = original_area_type 

        # 5. Get the created strip
        imgseq_strip = sequencer.active_strip
        
        # Make sure the strip covers all frames
        if imgseq_strip:
            imgseq_strip.frame_final_end = len(self.frame_image_filenames)

        return imgseq_strip



    def upload_image_sequence(
            self, 
            image_sequence_dir=""
        ):
        """
        Upload from a sequence of image files, to Blender video sequence editor.

        Args:
            image_sequence_dir (str): The file directory stores the image sequence, 
                the valid suffices of the images are (".JPG", ".JPEG", ".PNG", etc), case insensitive. 
        """
        # 1. Get all the image filenames, and sort them. 
        self._load_image_sequence(
            image_sequence_dir=image_sequence_dir
        )

        # 2. Add image sequence strip to video sequence editor.
        image_sequence_dir_name = os.path.basename(image_sequence_dir)
        self.strip_name = f"raw_{image_sequence_dir_name}"
        channel_idx = self.channel.raw_image_channel
        self.frame_start = self.channel.get_channel_end(channel_idx)

        self.strip_content = self._add_image_strip(
                image_sequence_scene=bpy.context.scene,
                image_sequence_dir=image_sequence_dir,
                frame_start=self.frame_start,
                channel=channel_idx
            )
        
        if self.strip_content:
            self.strip_content.name = self.strip_name
            self.frame_duration = self.strip_content.frame_final_end - self.strip_content.frame_start


        # 3. Print out the info log.
        info_msg = f"upload_image_sequence(), upload an image sequence from directory '{image_sequence_dir}', "
        info_msg += f"to Blender video sequence editor."
        self.logger.info(info_msg)


    def assemble_image_sequence_to_mp4(
            self, 
            image_sequence_dir="",
            mp4_filename=""
        ):
        """
        Upload from a sequence of image files, to Blender video sequence editor, with a temporary scene,
            then render the temporary scene to a MP4 video file. 

        Args:
            image_sequence_dir (str): The file directory stores the image sequence, 
                the valid suffices of the images are (".JPG", ".JPEG", ".PNG", etc), case insensitive. 
            mp4_filename (str): The full filename of the output MP4 video file.
        """
        # 1. Get all the image filenames, and sort them. 
        self._load_image_sequence(
            image_sequence_dir=image_sequence_dir
        )

        # 2. Create a temporary scene, 'imgseq_scene'.
        original_scene = bpy.context.scene
        imgseq_scene = bpy.data.scenes.new(name="TmpImageSequenceScene")
        bpy.context.window.scene = imgseq_scene  # Set as active scene

        
        try:
            # 3. Add image strip for the image sequence in the temporary scene.
            imgseq_strip = self._add_image_strip(
                image_sequence_scene=imgseq_scene,
                image_sequence_dir=image_sequence_dir,
                frame_start=1,
                channel=1
            )

            # 4. Set the temporary scene settings, as well as the output settings.
            imgseq_scene.render.resolution_x = self.scene_settings["scene.render.resolution_x"]  
            imgseq_scene.render.resolution_y = self.scene_settings["scene.render.resolution_y"] 
            imgseq_scene.render.resolution_percentage = self.scene_settings["scene.render.resolution_percentage"] 
            imgseq_scene.frame_start = self.scene_settings["scene.frame_start"] 
            imgseq_scene.frame_end = self.scene_settings["scene.frame_end"] 
            imgseq_scene.render.fps = self.scene_settings["scene.render.fps"] 
            imgseq_scene.render.fps_base = self.scene_settings["scene.render.fps_base"] 
    
            imgseq_scene.render.image_settings.file_format = "FFMPEG"
            imgseq_scene.render.ffmpeg.format = "MPEG4"
            imgseq_scene.render.ffmpeg.codec = "H264"
            imgseq_scene.render.ffmpeg.constant_rate_factor = "HIGH"
            imgseq_scene.render.filepath = mp4_filename
            

            # 5. Render the temporary scene to a MP4 video file.
            info_msg = f"render_image_sequence_to_mp4(), start to render the image sequence from directory '{image_sequence_dir}', "
            info_msg += f"to a MP4 file '{mp4_filename}'..."
            self.logger.info(info_msg)

            bpy.ops.render.render(animation=True)

            info_msg = f"render_image_sequence_to_mp4(), rendering the image sequence from directory '{image_sequence_dir}', "
            info_msg += f"to a MP4 file '{mp4_filename}', completed."
            self.logger.info(info_msg)

        finally:
            # 6. Delete temporary scene and restore original
            debug_msg = f"render_image_sequence_to_mp4(), the temporary scene '{imgseq_scene.name}' will be deleted now."
            self.logger.debug(debug_msg)
            bpy.context.window.scene = original_scene
            bpy.data.scenes.remove(imgseq_scene)


    def _dump_scene_settings(
            self, 
            scene=None,
            json_filename=""
        ) -> str:
        """
        Save the scene's settings to a JSON file, and return the 'dict' object of the settings. 
        If json_filename="", then the JSON file is not save, only return the 'dict' object.

        Args:
            scene (obj): The object instance of the scene. The default one is 'bpy.context.scene'.
            json_filename (str): The full name of a json file that stores the scene's settings, 
                the valid suffices of the images are (".JSON"), case insensitive. 

        Returns:
            A string whose content is the dict object of the scene's settings.
        """
        scene_output_settings = {
            "scene.render.resolution_x": scene.render.resolution_x,
            "scene.render.resolution_y": scene.render.resolution_y,
            "scene.render.resolution_percentage": scene.render.resolution_percentage,
            "scene.frame_start": scene.frame_start,
            "scene.frame_end": scene.frame_end,
            "scene.render.fps": scene.render.fps, 
            "scene.render.fps_base": scene.render.fps_base,
            "scene.render.filepath": scene.render.filepath,
            "scene.render.image_settings.file_format": scene.render.image_settings.file_format
        }
        scene_output_settings_str = json.dumps(scene_output_settings, indent=2, ensure_ascii=False)
        debug_msg = f"render_to_image_sequence(), scene_output_settings:\n{scene_output_settings_str}\n"
        # self.logger.debug(debug_msg)  

        if len(json_filename) > 0:
            directory_path = os.path.dirname(json_filename)
            os.makedirs(directory_path, exist_ok=True)

            with open(json_filename, "w") as fo:
                fo.write(scene_output_settings_str)
                    
        return  scene_output_settings_str   


    def render_to_image_sequence(
            self, 
            image_sequence_dir=""
        ):
        """
        Upload from a video files, to Blender video sequence editor.

        Args:
            image_sequence_dir (str): The file directory stores the image sequence, 
                the filenames the image sequence will be "frame_###.png". 
        """  
        # 1. Unify the settings of all strips in all channels in 'bpy.context.scene'
        scene = bpy.context.scene
        scene.render.image_settings.file_format = "PNG"

        shutil.rmtree(image_sequence_dir)
        os.makedirs(image_sequence_dir, exist_ok=True)
        scene.render.filepath = os.path.join(image_sequence_dir, "frame_")  # Output path + prefix

        self.channel.unify_scene_settings()

        """
        scene_output_settings = {
            "scene.render.resolution_x": scene.render.resolution_x,
            "scene.render.resolution_y": scene.render.resolution_y,
            "scene.render.resolution_percentage": scene.render.resolution_percentage,
            "scene.frame_start": scene.frame_start,
            "scene.frame_end": scene.frame_end,
            "scene.render.fps": scene.render.fps, 
            "scene.render.fps_base": scene.render.fps_base,
            "scene.render.filepath": scene.render.filepath,
            "scene.render.image_settings.file_format": scene.render.image_settings.file_format
        }
        scene_output_settings_str = json.dumps(scene_output_settings, indent=2, ensure_ascii=False)
        """
        json_filepath = f"{image_sequence_dir.rstrip('/')}/scene_settings.json"
        scene_output_settings_str = self._dump_scene_settings(
            scene=bpy.context.scene,
            json_filename=json_filepath
        )
        debug_msg = f"render_to_image_sequence(), scene_output_settings:\n{scene_output_settings_str}\n"
        self.logger.debug(debug_msg)        


        # 2. Render 'bpy.context.scene' to an image sequence.
        info_msg = f"render_to_image_sequence(), start to render 'bpy.context.scene' "
        info_msg += f"to an image sequence in directory '{image_sequence_dir}'..."
        self.logger.info(info_msg)

        bpy.ops.render.render(animation=True)

        info_msg = f"render_to_image_sequence(), rendering 'bpy.context.scene' "
        info_msg += f"to an image sequence in directory '{image_sequence_dir}', completed."
        self.logger.info(info_msg)


    def disassemble_video_to_image_sequence(
            self, 
            video_filename="",
            image_sequence_dir=""
        ):
        """
        Dissemble a video files, to an image sequence, using a temporary scene.

        Args:
            video_filename (str): The full file name of the video, 
                the valid suffices of the video file are (".MP4", ".MOV", etc), case insensitive. 
            image_sequence_dir (str): The file directory stores the image sequence, 
                the filenames the image sequence will be "frame_###.png". 
        """
        # 1. Create a temporary scene, and keep 'bpy.context.scene' untouched.
        original_scene = bpy.context.scene
        temp_scene = bpy.data.scenes.new(name="TmpScene-Video2ImageSequence")
        bpy.context.window.scene = temp_scene  # Set as active scene

        try:
            # 2. Import video into temporary scene's VSE
            temp_scene.sequence_editor_create()
            sequencer = temp_scene.sequence_editor
            strip = sequencer.strips.new_movie(
                name="TmpInputVideo",
                filepath=video_filename,
                frame_start=1,
                channel=1
            )
            
            # 3. Set the temporary scene's settings 
            temp_scene.render.resolution_x = strip.elements[0].orig_width
            temp_scene.render.resolution_y = strip.elements[0].orig_height
            temp_scene.render.resolution_percentage = 100
            temp_scene.frame_start = 1
            temp_scene.frame_end = strip.frame_final_end - 1 # Total frames
            temp_scene.render.fps = round(strip.fps)
            temp_scene.render.fps_base = 1
            temp_scene.render.image_settings.file_format = "PNG"

            if os.path.isdir(image_sequence_dir):
                shutil.rmtree(image_sequence_dir)
            os.makedirs(image_sequence_dir, exist_ok=True)
            temp_scene.render.filepath = os.path.join(image_sequence_dir, "frame_")  # Output path + prefix

            # 4. Dump the scene settings to the json file in the image sequence directory.
            json_dir = image_sequence_dir.rstrip('/')
            json_filename = f"{json_dir}/{self.scene_settings_filename}"
            scene_settings_str = self._dump_scene_settings(
                scene=temp_scene,
                json_filename=json_filename
            )
            # self.logger.debug(scene_settings_str)

            # 5. Render the video sequence in the temporary scene into an image sequence.
            info_msg = f"disassemble_video_to_image_sequence(), start to disassemble the video file '{video_filename}', "
            info_msg += f"to an image sequence in directory '{image_sequence_dir}'..."
            self.logger.info(info_msg)

            bpy.ops.render.render(animation=True)

            info_msg = f"disassemble_video_to_image_sequence(), disassembling the video file '{video_filename}', "
            info_msg += f"to an image sequence in directory '{image_sequence_dir}', completed."
            self.logger.info(info_msg)
        
        finally:
            # 5. Cleanup: Delete temporary scene and restore original
            bpy.context.window.scene = original_scene
            bpy.data.scenes.remove(temp_scene)
            info_msg = f"disassemble_video_to_image_sequence(), delete the temporary scene."
            self.logger.info(info_msg)    


    @staticmethod
    def run_demo():
        input_video = "/home/robot/movie_blender_studio/input/bicycling_greenscreen.webm"
        image_sequence_dir = "/home/robot/movie_blender_studio/output/bicycling_greenscreen_imgseq"
        output_video = "/home/robot/movie_blender_studio/output/bicycling_greenscreen_20250921_2.MP4"

        imgseq_strip = ImageSequenceStrip()

        """
        imgseq_strip.disassemble_video_to_image_sequence(
            video_filename=input_video,
            image_sequence_dir=image_sequence_dir          
        )        
        """
       
        imgseq_strip.assemble_image_sequence_to_mp4(
            image_sequence_dir=image_sequence_dir,
            mp4_filename=output_video
        )
