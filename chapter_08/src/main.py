import bpy
import sys
import os
import json
import pprint


class BlenderImporter:
    def __init__(self):
        self.blend_file_path = "/"

        from dotenv import load_dotenv
        load_dotenv("./sys_config/sys_config.env")

        log_dir= os.getenv("LOG_DIR")
        print(f"\n[INFO] The log is store in this file directory: '{log_dir}'")


    def get_script_directory(self):
        # Get the directory of the current script
        try:
            # When script is run from Blender's Text Editor or as embedded script
            if bpy.data.texts:
                # Get the directory of the blend file if it exists, otherwise use current working directory
                if bpy.data.filepath:  # If blend file is saved
                    print(f"[INFO] The blend python script is saved")
                    dir_path = os.path.dirname(bpy.data.filepath)
                else:  # If blend file is not saved
                    print(f"[INFO] The blend python script is not saved")
                    dir_path = os.path.dirname(bpy.data.texts[0].filepath) if bpy.data.texts[0].filepath else os.getcwd()
            else:
                # When script is run as external file
                print(f"[INFO] script is run as external filed")
                dir_path = os.path.dirname(os.path.abspath(__file__))
        except:
            # Fallback to current working directory
            print(f"[INFO] Fallback to current working directory")
            dir_path = os.getcwd()

        # Ensure we have an absolute path
        dir_path = os.path.abspath(dir_path)

        # Get blend file path
        self.blend_file_path = bpy.data.filepath if bpy.data.filepath else dir_path
        # print(f"[INFO] blend_file_path='{self.blend_file_path}'")


    @staticmethod
    def append_script_directory():
        blender_importer = BlenderImporter()
        blender_importer.get_script_directory()

        # --- Add local modules to Python path ---
        # This allows us to import the classes from the other scripts in the same directory.
        if blender_importer.blend_file_path not in sys.path:
            sys.path.append(blender_importer.blend_file_path)
            print(f"[INFO] Added custom script directory '{blender_importer.blend_file_path}' to Python path.")

"""
To run this script:
$ cd /home/robot/movie_blender_studio
$ blender --python main.py
"""
if __name__ in "__main__":
    BlenderImporter.append_script_directory()

    # Clear the scene and create a sample mesh to texture
    bpy.ops.object.select_all(action='SELECT')
    if bpy.context.active_object: bpy.ops.object.delete()

    """
    from model.rock_generator import RockGenerator
    RockGenerator.run_demo()      
    """
   
    """
    from editor.editor_node import EditorNode
    EditorNode.run_demo()     
    """
   
    """
    from modifier.modifier_generator import ModifierGenerator
    ModifierGenerator.run_demo()     
    """
    
    """
    from material.texture_shader import TextureShader
    TextureShader.run_demo()
    """

    """
    from model.water_generator import WaterGenerator
    WaterGenerator.run_demo()        
    """

    """
    from model.riverbed_generator import RiverbedGenerator
    RiverbedGenerator.run_demo()        
    """
   
    """
    from hdri.dome_with_hdri_and_sun_generator import DomeHdriGenerator
    DomeHdriGenerator.run_demo()
    """

    """
    from scene.rocky_river_terrain import RockyRiverTerrain
    RockyRiverTerrain.run_demo()        
    """
           
    """
    from logger.logger import LlamediaLogger
    LlamediaLogger.run_demo()    
    """

    """
    from animation.keyframe import Keyframe
    Keyframe.run_demo()          
    """

    """
    from animation.constraint import Constraint
    Constraint.run_demo()       
    """

    """
    from animation.animation import Animation
    Animation.run_demo()      
    """
    
    """
    from camera.camera import Camera
    Camera.run_demo()       
    """
 
    """
    from camera.renderer import Renderer
    Renderer.run_demo()    
    """

    """
    from hdri.hdri_background import HdriBackground
    HdriBackground.run_demo()      
    """
 
    """
    from video.video_editor import VideoEditor
    VideoEditor.run_demo()       
    """
    
    """
    from compositing.image_compositor import ImageCompositor
    ImageCompositor.run_demo()         
    """
    
    """
    from compositing.video_compositor import VideoCompositor
    VideoCompositor.run_demo()          
    """

    """
    from video.image_sequence_strip import ImageSequenceStrip
    ImageSequenceStrip.run_demo()         
    """
    
    """
    from compositing.green_screen_compositor import GreenScreenCompositor
    GreenScreenCompositor.run_demo()    
    """

    """
    from tracking.motion_tracker import MotionTracker
    MotionTracker.run_demo()
    """
    
    """
    from camera.renderer_opencv import OpencvRenderer
    OpencvRenderer.run_demo()    
    """

    from tracking.camera_tracker import CameraTracker
    CameraTracker.run_demo()    
    



        
    
