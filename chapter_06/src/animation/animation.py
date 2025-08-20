import bpy
from math import radians

class Animation:
    def __init__(self):
        self.logger = None

        self.obj = None
        # The frame_range is a tuple (start_frame, end_frame, step)
        self.frame_range = (1, 100, 1)
        
        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("Animation").getLogger()
            self.logger.info(f"Animation class initialized.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not import Animation class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not import Animation class, error message: '{e}'")
 

    def set_object(self, obj):
        self.obj = obj


    def set_keyframe(self, frame, location=None, rotation=None, scale=None):
        """
        Sets the object's transformation and adds keyframes for the specified properties.

        Args:
            obj (bpy.types.Object): The object to keyframe.
            frame (int): The frame number to insert the keyframe on.
            location (tuple, optional): The (X, Y, Z) location. Defaults to None.
            rotation (tuple, optional): The (X, Y, Z) Euler rotation in degrees ranged within (0, 360.0). Defaults to None.
            scale (tuple, optional): The (X, Y, Z) scale. Defaults to None.
        """
        info_msg = f"set_keyframe(), frame={frame}, location={location}, "
        info_msg += f"rotation={rotation}, scale={scale}"
        self.logger.info(f"set_keyframe(), .")

        if location is not None:
            try:
                self.obj.location = location
                self.obj.keyframe_insert(data_path="location", frame=frame)
                self.logger.info(f"Set location keyframe for '{self.obj.name}' on frame {frame}.")
            except Exception as e:
                self.logger.error(f"Could not set location keyframe for '{self.obj.name}': {e}")

        if rotation is not None:
            try:
                # Convert degrees to radians for Blender's internal representation
                rotation_rad = [radians(angle) for angle in rotation]
                self.obj.rotation_euler = rotation_rad
                self.obj.keyframe_insert(data_path="rotation_euler", frame=frame)
                self.logger.info(f"Set rotation keyframe for '{self.obj.name}' on frame {frame}.")
            except Exception as e:
                self.logger.error(f"Could not set rotation keyframe for '{self.obj.name}': {e}")

        if scale is not None:
            try:
                self.obj.scale = scale
                self.obj.keyframe_insert(data_path="scale", frame=frame)
                self.logger.info(f"Set scale keyframe for '{self.obj.name}' on frame {frame}.")
            except Exception as e:
                self.logger.error(f"Could not set scale keyframe for '{self.obj.name}': {e}")

        if location is None and rotation is None and scale is None:
            try:
                self.obj.keyframe_insert(data_path="location", frame=frame)
                self.obj.keyframe_insert(data_path="rotation_euler", frame=frame)
                self.obj.keyframe_insert(data_path="scale", frame=frame)
                self.logger.info(f"Set an empty keyframe for '{self.obj.name}' on frame {frame}.")
            except Exception as e:
                self.logger.error(f"Could not set an empty keyframe for '{self.obj.name}': {e}")


    def set_interpolation(self, data_path, interpolation_type='BEZIER', keyframe_indices=None):
        """
        Sets the interpolation mode for specific keyframe points in the object's action.

        Args:
            data_path (str): The name of the property that was keyframed. 
                             The transformation data path is one of ("location", "scale", "rotation_euler").
                             The material data path is something like f"nodes['{principled_node.name}'].inputs[6].default_value".
            interpolation_type (str): The interpolation type to apply ('BEZIER', 'LINEAR', 'CONSTANT').
            keyframe_indices (list, optional): A list of integer indices of the keyframes to modify.
                                               If None, all keyframes will be modified.
        """
        # Ensure the object has animation data and an action.
        if not self.obj.animation_data or not self.obj.animation_data.action:
            self.logger.error("No animation data found on object. Skipping interpolation setup.")
            return
        else:
            info_msg = f"set_interpolation(), data_path='{data_path}', "
            info_msg += f"interpolation_type='{interpolation_type}, "
            info_msg += f"keyframe_indices='{keyframe_indices}'."
            self.logger.info(info_msg)

        for fcurve in self.obj.animation_data.action.fcurves:
            if fcurve.data_path == data_path:
                for i, kp in enumerate(fcurve.keyframe_points):
                    # List of valid interpolation types
                    valid_types = ['BEZIER', 'LINEAR', 'CONSTANT', 'SINE', 'QUAD', 'QUART', 'QUINT', 'EXPO', 'CIRC', 'BACK', 'BOUNCE', 'ELASTIC']
                    
                    if interpolation_type.upper() not in valid_types:
                        warn_msg = f"Invalid interpolation type '{interpolation_type}'. "
                        warn_msg += f"Supported types are: {', '.join(valid_types)}"
                        self.logger.warn(warn_msg)
                        continue

                    kp_idx = round(kp.co.x)
                    if keyframe_indices is not None and kp_idx in keyframe_indices:
                        kp.interpolation = interpolation_type.upper()   

                        debug_msg = f"set_interpolation(), successfully set data_path='{data_path}', "
                        debug_msg += f"interpolation_type='{interpolation_type}, "
                        debug_msg += f"at {kp_idx}'s keyframe."
                        self.logger.debug(debug_msg)           


    def create_material(self, material_name="AnimatedMaterial"):
        """
        Creates a new material with a Principled BSDF shader and assigns it to the object.
        
        Args:
            material_name (str): The name for the new material.
            
        Returns:
            bpy.types.Material: The created material.
        """
        # Create a new material
        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True
        
        # Get the material's node tree
        nodes = material.node_tree.nodes
        
        # Clear default nodes
        nodes.clear()
        
        # Create a Principled BSDF shader node
        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.location = (0, 0)
        
        # Create an output node
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (300, 0)
        
        # Connect the nodes
        links = material.node_tree.links
        links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
        
        # Assign the material to the object
        if self.obj.data.materials:
            self.obj.data.materials[0] = material
        else:
            self.obj.data.materials.append(material)
            
        self.logger.info(f"Created and assigned material '{material_name}' to '{self.obj.name}'.")
        return material
    
    def set_material_keyframe(self, frame, base_color=None, metallic=None, roughness=None):
        """
        Sets keyframes for material properties.
        
        Args:
            frame (int): The frame number to insert the keyframe on.
            base_color (tuple, optional): RGBA color values (0-1). Defaults to None.
            metallic (float, optional): Metallic value (0-1). Defaults to None.
            roughness (float, optional): Roughness value (0-1). Defaults to None.
        """
        if not self.obj.data.materials:
            self.logger.warning(f"No material found on '{self.obj.name}'. Creating a new material.")
            material = self.create_material()
        else:
            info_msg = f"For testing purpose, set_material_keyframe(), frame={frame}, "
            info_msg += f"base_color={base_color}, metallic={metallic}, roughness={roughness}"
            self.logger.warn(info_msg)
            material = self.obj.data.materials[0]
            
        nodes = material.node_tree.nodes
        principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
        
        if not principled_node:
            self.logger.error("No Principled BSDF node found in material.")
            return
            
        self.logger.info(f"Set material keyframe at [{frame}].")
        
        if base_color is not None:
            try:
                principled_node.inputs['Base Color'].default_value = base_color
                material.node_tree.keyframe_insert(
                    data_path=f'nodes["{principled_node.name}"].inputs[0].default_value', 
                    frame=frame
                )
                self.logger.info(f"Set base color keyframe for '{self.obj.name}' on frame {frame}.")
            except Exception as e:
                self.logger.error(f"Could not set base color keyframe for '{self.obj.name}': {e}")

        if metallic is not None:
            try:
                principled_node.inputs['Metallic'].default_value = metallic
                material.node_tree.keyframe_insert(
                    data_path=f'nodes["{principled_node.name}"].inputs[6].default_value', 
                    frame=frame
                )
                self.logger.info(f"Set metallic keyframe for '{self.obj.name}' on frame {frame}.")
            except Exception as e:
                self.logger.error(f"Could not set metallic keyframe for '{self.obj.name}': {e}")

        if roughness is not None:
            try:
                principled_node.inputs['Roughness'].default_value = roughness
                material.node_tree.keyframe_insert(
                    data_path=f'nodes["{principled_node.name}"].inputs[9].default_value', 
                    frame=frame
                )
                self.logger.info(f"Set roughness keyframe for '{self.obj.name}' on frame {frame}.")
            except Exception as e:
                self.logger.error(f"Could not set roughness keyframe for '{self.obj.name}': {e}")            


    def create_camera_track_to_animation(self, camera, path_radius=10):
        """
        Creates a camera animation where the camera circles a target object.

        Args:
            camera (bpy.types.Object): The camera object.
            target (bpy.types.Object): The object for the camera to track.
            start_frame (int): The starting frame of the animation.
            end_frame (int): The ending frame of the animation.
            path_radius (float): The radius of the circular path for the camera.
        """
        if not camera:
            print("[ERROR] Camera or target object not specified.")
            return

        print(f"[INFO] Creating camera tracking animation for '{camera.name}' targeting '{self.obj.name}'.")

        # Add a Track To constraint to the camera
        track_to = camera.constraints.new(type='TRACK_TO')
        track_to.target = self.obj
        track_to.track_axis = 'TRACK_NEGATIVE_Z'
        track_to.up_axis = 'UP_Y'

        # Create a circular path for the camera to follow
        bpy.ops.curve.primitive_bezier_circle_add(radius=path_radius, enter_editmode=False, location=(0, 0, 0))
        path_curve = bpy.context.active_object
        path_curve.name = "CameraPath"

        # Add a Follow Path constraint to the camera
        follow_path = camera.constraints.new(type='FOLLOW_PATH')
        follow_path.target = path_curve
        follow_path.use_curve_follow = True
        follow_path.forward_axis = 'FORWARD_Y'

        # Animate the camera's movement along the path
        path_curve.data.path_duration = self.frame_range[2] - self.frame_range[0]
        path_curve.data.eval_time = 0
        path_curve.data.keyframe_insert(data_path='eval_time', frame=self.frame_range[0])
        path_curve.data.eval_time = self.frame_range[2] - self.frame_range[0]
        path_curve.data.keyframe_insert(data_path='eval_time', frame=self.frame_range[0])

        print("[SUCCESS] Camera tracking animation created.")

    
    def setup_render_settings(self, output_path="", resolution_x=1920, resolution_y=1080):
        """
        Configures basic render settings for an animation.

        Args:
            output_path (str): The directory and file prefix for the rendered frames.
            start_frame (int): The first frame to render.
            end_frame (int): The last frame to render.
            resolution_x (int): The width of the output image.
            resolution_y (int): The height of the output image.
        """
        scene = bpy.context.scene
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = output_path
        scene.frame_start = self.frame_range[0]
        scene.frame_end = self.frame_range[1]
        scene.render.resolution_x = resolution_x
        scene.render.resolution_y = resolution_y
        
        print(f"[INFO] Render settings configured:")
        print(f"  - Output Path: {output_path}")
        print(f"  - Frame Range: {self.frame_range[0]}-{self.frame_range[1]}")
        print(f"  - Resolution: {resolution_x}x{resolution_y}")
    

    @staticmethod
    def run_demo():
        """
        A static method to demonstrate the functionality of the Animation class.
        """
        print("[INFO] --- Running Animation Class Demo ---")

        # --- Setup the scene ---
        # Clear existing objects
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        # Create a cube to be the target
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
        cube = bpy.context.active_object
        cube.name = "TargetCube"

        # Create a ground plane
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))

        # Create a camera
        bpy.ops.object.camera_add(location=(10, 10, 5))
        camera = bpy.context.active_object
        camera.name = "MainCamera"
        bpy.context.scene.camera = camera

        # --- Animate the cube ---
        animator = Animation()
        animator.set_object(cube)
        
        # Create and assign a material to the cube
        material = animator.create_material("AnimatedCubeMaterial")
        
        # Keyframe initial state for transformation
        animator.set_keyframe(
            frame=1, 
            location=(0, 0, 1), 
            rotation=(0, 0, 0),
            scale=(1, 1, 1)
        )
        
        # Keyframe initial state for material
        animator.set_material_keyframe(
            frame=1,
            base_color=(1.0, 0.0, 0.0, 1.0),  # Red
            metallic=0.0,
            roughness=0.5
        )
        
        # Animate rotation and location for frame 50
        animator.set_keyframe(
            frame=50, 
            location=(0, 0, 5), 
            rotation=(0, 0, 180)
        )
        
        # Animate material properties at frame 50
        animator.set_material_keyframe(
            frame=50,
            base_color=(0.0, 1.0, 0.0, 1.0),  # Green
            metallic=0.5,
            roughness=0.2
        )

        # Keep the object un-moved from frame 50 to 80.
        animator.set_keyframe(
            frame=80
        )
        
        # Change material at frame 80
        animator.set_material_keyframe(
            frame=80,
            base_color=(0.0, 0.0, 1.0, 1.0),  # Blue
            metallic=0.8,
            roughness=0.1
        )

        # Animate rotation and location for frame 100
        animator.set_keyframe(
            frame=100, 
            location=(0, 0, 1), 
            rotation=(0, 0, 240),
            scale=(1, 2.0, 3.0)
        )
        
        # Final material state at frame 100
        animator.set_material_keyframe(
            frame=100,
            base_color=(1.0, 1.0, 0.0, 1.0),  # Yellow
            metallic=0.3,
            roughness=0.7
        )

        """
        Don't set_interpolation() for material.

        material = animator.obj.data.materials[0]    
        nodes = material.node_tree.nodes
        principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
        data_path = f'nodes["{principled_node.name}"].inputs[0].default_value'        
        """
        data_path = "location"
        animator.set_interpolation(data_path, "CONSTANT", [1, 80])

        # --- Animate the camera ---
        animator.create_camera_track_to_animation(camera, path_radius=15)
        animator.setup_render_settings()

        print("\n[SUCCESS] --- Animation Demo Finished ---")
        print("The scene is now set up for rendering. You can render the animation from the Render menu.")


if __name__ == "__main__":
    Animation.run_demo()
