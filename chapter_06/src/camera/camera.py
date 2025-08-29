import bpy
import mathutils
from math import radians, sin, cos
from typing import Any
import pprint

class Camera:
    """
    A class to control and animate a camera in Blender.
    
    This class provides methods to manipulate a camera's properties,
    set up tracking constraints, and create simple animations.
    
    Args:
        camera_name (str): The name of the camera object to control.
                           Defaults to "Camera".
    """
    def __init__(self, camera_name="myCamera"):
        self.logger = None
        self.camera = None
        self.renderer = None
        self.animation = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("Camera").getLogger()
            self.logger.info(f"Create a Camera object named '{camera_name}'.")

            from camera.renderer import Renderer
            self.renderer = Renderer()
            self.camera = self._create_camera(camera_name)

            from animation.animation import Animation
            self.animation = Animation(self.camera)

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Camera class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize Camera class, error message: '{e}'")
 

    
    def _create_camera(self, camera_name="Camera"):
        bpy.ops.object.camera_add(location=(10, -10, 0))
        bpy.context.object.name = camera_name
        self.camera = bpy.context.object
        
        # Set this camera as the active camera for the scene
        bpy.context.scene.camera = self.camera
        
        return self.camera


    def set_activate(self):
        self.logger.info(f"Set camera '{self.camera.name}' to be active.")
        bpy.context.scene.camera = self.camera
        bpy.context.view_layer.objects.active = self.camera


    def get_properties(self) -> dict:
        info_msg = f"get_properties(), the returned json contains some important properties of the camera and lens. "
        info_msg += f"\n\tWhen setting property, you can assign the value to the property, e.g. "
        info_msg += f"self.camera.data.sensor_fit = 'HORIZONTAL'"
        self.logger.info(info_msg)

        camera_properties = {}  
        focal_length_msg = f"The lens focal length is {self.camera.data.lens}"
        camera_properties["self.camera.data.lens"] = focal_length_msg
    
        camera_properties["self.camera.data.dof.use_dof"] = self.camera.data.dof.use_dof
        camera_properties["self.camera.data.dof.aperture_fstop"] = self.camera.data.dof.aperture_fstop
        
        focus_obj_name = self.camera.data.dof.focus_object.name if self.camera.data.dof.focus_object else "None"
        camera_properties["self.camera.data.dof.focus_object"] = f"The name of the focus object is '{focus_obj_name}'"

        sensor_fit_msg = f"The current sensor fit is 'self.camera.data.sensor_fit'. "
        sensor_fit_msg += f"The valid values of sensor fit are 'AUTO', 'HORIZONTAL', 'VERTICAL'."
        camera_properties["self.camera.data.sensor_fit"] = sensor_fit_msg

        return camera_properties


    def rotate_trackball(self, center_point=(0, 0, 0), radius=10, angle_degrees=0):
        """
        Moves the camera to a new position, rotating it like a trackball around a center point.
        
        Args:
            center_point (tuple): The (x, y, z) coordinates of the center of rotation.
            radius (float): The distance from the center point.
            angle_degrees (float): The angle of rotation around the Z-axis in degrees.
        """
        info_msg = f"The camera will rotate like a trackball "
        info_msg += f"around a center point at {center_point} with radius {radius}."
        self.logger.info(info_msg)
        
        angle_rad = radians(angle_degrees)
        x = center_point[0] + radius * cos(angle_rad)
        y = center_point[1] + radius * sin(angle_rad)
        z = center_point[2] + radius * cos(radians(45)) # Slight Z-axis offset for better view
        
        self.camera.location = (x, y, z)
        
        # Clear any existing constraints to allow manual rotation
        for constraint in self.camera.constraints:
            if constraint.type == 'TRACK_TO':
                self.camera.constraints.remove(constraint)
        
        # Point the camera back towards the center
        direction = mathutils.Vector(center_point) - self.camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        self.camera.rotation_euler = rot_quat.to_euler()
        

    def move_on_track(self, curve_object: str|Any=None, duration_frames=250, start_frame=1):
        """
        Moves the camera along a specified 3D curve using a Follow Path constraint.
        
        This method is now corrected to ensure the camera completes the full path.
        
        Args:
            curve_object_name (str): The name of the curve object to follow.
            duration_frames (int): The total number of frames for the animation to complete.
            start_frame (int): The starting frame for the animation.
        """
        curve = None
        if curve_object is None:
            error_msg = f"The curve object is None."
            self.logger.error(error_msg)
            return 
        else:
            if isinstance(curve_object, str):
                curve = bpy.data.objects.get(str(curve_object))
            else:
                curve = curve_object

            if not curve or curve.type != 'CURVE':
                error_msg = f"The curve object '{str(curve_object)}' is not a valid curve."
                self.logger.error(error_msg)
                return
            else:
                info_msg = f"Make the camera moving along the track '{curve.name}'"
                self.logger.info(info_msg)

        # Clear existing path constraints to avoid conflicts
        for constraint in self.camera.constraints:
            if constraint.type == 'FOLLOW_PATH':
                self.camera.constraints.remove(constraint)
        
        # Add the Follow Path constraint
        constraint = self.camera.constraints.new(type='FOLLOW_PATH')
        constraint.target = curve
        constraint.use_curve_follow = True
        
       # Ensure the animation runs from start (0%) to end (100%) of the path
        constraint.offset = 0.0
        self.camera.keyframe_insert(data_path='constraints["Follow Path"].offset', frame=start_frame)
        
        # Set the final keyframe at the end of the specified duration
        end_frame = start_frame + duration_frames
        constraint.offset = 100.0
        self.camera.keyframe_insert(data_path='constraints["Follow Path"].offset', frame=end_frame)


    def target_object(self, target_object: str | Any =None):
        """
        Sets a 'Track To' constraint on the camera to point it at a target object.
        
        Args:
            target_object: It can be either the name string of the object to track, or the target blender object instance.
        """
        target = None
        if isinstance(target_object, str):
            target = bpy.data.objects.get(str(target_object))
            if not target:
                error_msg = f"Could not find the input object named '{str(target_object)}'."
                self.logger.error(error_msg)
                return
            
        elif target_object is None:
            self.logger.error(f"The input 'target_object' is none.")
            return
            
        # Add the 'Track To' constraint
        constraint = self.camera.constraints.new(type='TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
        self.logger.info(f"The camera now tracking object: {target.name}")


    """
    $ cd /home/robot/movie_blender_studio
    $ blender --python main.py
    """
    @staticmethod
    def run_demo_v1():
        # Clean up existing objects for a fresh start
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        # Create a cube as a target object
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -1))
        bpy.context.object.name = "TargetCube"
        
        demo_camera = Camera("DemoCamera")
        demo_camera.set_activate()
       
        # Use the methods to manipulate the camera
        
        # Get the camera properties
        camera_properties = demo_camera.get_properties()
        print(f"\n[INFO] Camera properties: ")
        pprint.pprint(camera_properties)
        
        
        #
        #  Demo 1. The camera moves along a circle, and lens always targets at the cube.
        #
        # Step 1. Create a path (Bezier curve) for the camera to follow
        bpy.ops.curve.primitive_bezier_circle_add(radius=10)
        path = bpy.context.object
        path.name = "CameraPath"
        path.location.z = 2     

        # Step 2. Make the camera follow the curve and track the target
        demo_camera.move_on_track(path.name, duration_frames=249)
        demo_camera.target_object("TargetCube")
        
        # Step 3. Set the frame range
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 250
        
        # Step 4. Rendering a MP4 video
        demo_camera.set_activate()
        demo_camera.renderer.render_frame_images(
            output_path="output/tmp_images"
            )
        demo_camera.renderer.compile_images_to_video(
            input_images_dir="output/tmp_images",
            output_video_dir="output/video_output"
            )        


        #
        #  Demo 2. The camera is locked to a trackball, you can change the orientation of the camera,
        #          but it is always locked to the origin.
        #  When running demo 2, remember to comment out the demo 1. 
        #
        """
        # Move the camera to a "trackball" position
        demo_camera.camera.scale=(2,2,2)
        demo_camera.rotate_trackball(radius=6, angle_degrees=45)        
        """


    """
    $ cd /home/robot/movie_blender_studio
    $ blender --python main.py
    """
    @staticmethod
    def run_demo():
        # Clear default objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # --------------------------
        # 1. Create Sun
        # --------------------------
        bpy.ops.mesh.primitive_uv_sphere_add(radius=2, location=(0, 0, 0))
        sun = bpy.context.active_object
        sun.name = "Sun"

        # Sun material
        sun_mat = bpy.data.materials.new(name="SunMaterial")
        sun_mat.diffuse_color = (1, 0.8, 0.2, 1)
        sun.data.materials.append(sun_mat)

        # --------------------------
        # 2. Create Earth 
        # --------------------------
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8)
        earth = bpy.context.active_object
        earth.name = "Earth"
        # earth.location = (0, -10.0, 0)
        # bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

        # Earth material
        earth_mat = bpy.data.materials.new(name="EarthMaterial")
        earth_mat.diffuse_color = (0.2, 0.3, 1, 1)
        earth.data.materials.append(earth_mat)    

        # Lock Z location
        earth.lock_location[2] = True   

        # --------------------------
        # 3. Create Moon
        # --------------------------
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4)
        moon = bpy.context.active_object
        moon.name = "Moon"

        # Moon material
        moon_mat = bpy.data.materials.new(name="MoonMaterial")
        moon_mat.diffuse_color = (0.2, 0.8, 0.2, 1)
        moon.data.materials.append(moon_mat)    

        # Lock Z location
        moon.lock_location[2] = True    

        # --------------------------
        # 4. Create solar animation.
        # --------------------------
        from animation.animation import Animation
        solar_animation = Animation(earth)

        # Make the earth circle around the sun. 
        solar_animation.circle_around(
            target_obj=sun,
            radius=10,
            keyframe_range=(1, 250)  # Full orbit over 250 frames
        )        

        # --------------------------
        # 5. Using animation, to move the moon around the earth.
        # --------------------------
        solar_animation.set_object(moon)

        # Make the moon circle around the earth. 
        solar_animation.circle_around(
            target_obj=earth,
            radius=4,
            keyframe_range=(1, 80)  # Full orbit over 250 frames
        )     
        solar_animation.circle_around(
            target_obj=earth,
            radius=4,
            keyframe_range=(81, 160)  # Full orbit over 250 frames
        )          
        solar_animation.circle_around(
            target_obj=earth,
            radius=4,
            keyframe_range=(161, 250)  # Full orbit over 250 frames
        )         

        # --------------------------
        # 6. Create solar_camera
        # --------------------------
        solar_camera = Camera("SolarCamera")
        solar_camera.set_activate()
        solar_camera.camera.data.lens = 20.0
        camera_properties = solar_camera.get_properties()
        print(f"\n[INFO] Camera properties: ")
        pprint.pprint(camera_properties)

        # --------------------------
        # 7. Using animation, to move the camera along a straight line.
        # --------------------------
        solar_camera.animation.move_straight(
            line_coordinates=((12, -10, 10), (12, 10, 10)),
            keyframe_range=(1, 250)  # Movement over 250 frames
        )

        solar_camera.animation.track_to(
            target_obj=sun, 
            track_axis="TRACK_NEGATIVE_Z", 
            up_axis="UP_Y"            
        )

        # --------------------------
        # 8. Set the Blender UI.
        # --------------------------
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 250    

        # Check if a world exists, create one if not.
        if not bpy.context.scene.world:
            bpy.context.scene.world = bpy.data.worlds.new("World")

        bpy.context.scene.world.use_nodes = True
        background_node = bpy.context.scene.world.node_tree.nodes["Background"]
        background_node.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1.0)     

        # --------------------------
        # 9. Rendering a MP4 video.
        # --------------------------
        solar_camera.set_activate()
        solar_camera.renderer.render_frame_images(
            output_path="output/tmp_images"
        )
        solar_camera.renderer.compile_images_to_video(
            input_images_dir="output/tmp_images",
            output_video_dir="output/video_output"
        )      
        
  

if __name__ == "__main__":
    Camera.run_demo()