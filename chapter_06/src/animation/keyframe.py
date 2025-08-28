import bpy
import math
from mathutils import Vector

class Keyframe:
    def __init__(self, obj=None):
        self.logger = None

        self.obj = obj
        self.keyframe = None
        self.constraint = None

        try:
            from logger.logger import LlamediaLogger
            # Stream the log to the 'Animation' subdirectory in the log directory.
            self.logger = LlamediaLogger("Animation").getLogger()
            self.logger.info(f"Keyframe class initialized.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Keyframe class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize Keyframe class, error message: '{e}'")
 

    def set_object(self, obj):
        self.obj = obj


    def set_transform_keyframe(
            self, 
            frame_idx=-1
        ):
        """
        Set a keyframe with the object's current transformation, including location, rotation, and scale.

        Args:
            obj (bpy.types.Object): The object to keyframe.
            frame_idx  (int): The frame index to insert the keyframe on.
        """
        # Ensure the object has animation data and an action.
        if not self.obj:
            self.logger.warn("set_transform_keyframe(): self.obj is None.")
            return
        
        # Check if the keyframe index is valid
        if frame_idx < 0:
            self.logger.warn(f"set_transform_keyframe(): Keyframe index {frame_idx} is out of range.")
            return        

        try:
            self.obj.keyframe_insert(data_path="location", frame=frame_idx)
            self.obj.keyframe_insert(data_path="rotation_euler", frame=frame_idx)
            self.obj.keyframe_insert(data_path="scale", frame=frame_idx)
        except Exception as e:
            warn_msg = f"set_transform_keyframe(): Could not set a keyframe for '{self.obj.name}'. "
            warn_msg += f"The error message is: '{e}'"
            self.logger.warn(warn_msg)

        rotation_degree = (
            math.degrees(self.obj.rotation_euler.x),
            math.degrees(self.obj.rotation_euler.y),
            math.degrees(self.obj.rotation_euler.z)
        )
        info_msg = f"set_transform_keyframe(), frame={frame_idx}, location={self.obj.location}, "
        info_msg += f"rotation={rotation_degree}, scale={self.obj.scale}."
        self.logger.info(info_msg)
 


    def set_material_keyframe(
            self, 
            frame_idx=-1, 
            node_name="", 
            node_properties=[]
        ):
        """
        Set a keyframe with one of the shader node of the object's material.

        Args:
            obj (bpy.types.Object): The object to keyframe.
            frame_idx (int): The frame index to insert the keyframe on.
            node_name (str): The name of the node, e.g. 'MY_OBJ_BSDF_NODE'.
            node_properties: A list of the node's input socket names.
        """
        if not self.obj.data.materials:
            self.logger.warn(f"set_material_keyframe(), no material is found with '{self.obj.name}'.")
            return 
        else:
            info_msg = f"set_material_keyframe(), frame={frame_idx}, "
            info_msg += f"node_name={node_name}, node_properties={node_properties}."
            self.logger.info(info_msg)
            
        material = self.obj.data.materials[0]
        nodes = material.node_tree.nodes
        shader_node = next((node for node in nodes if node.name == node_name), None)
        
        if not shader_node:
            warn_msg = f"For the '{self.obj.name}' object, "
            warn_msg += f"no shader node with name '{node_name}' is found in its material."
            self.logger.warn(warn_msg)
            return

        for input_socket_name in node_properties:
            try:
                node_input_idx = -1
                for idx, input_socket in enumerate(shader_node.inputs):
                    if input_socket.name == input_socket_name:
                        node_input_idx = idx
                        break

                if node_input_idx == -1:
                    warn_msg = f"For shader node '{node_name}', input socket '{input_socket_name}' is not found."
                    self.logger.warn(warn_msg)
                    continue

                data_path_str = f'nodes["{shader_node.name}"].inputs[{node_input_idx}].default_value', 

                material.node_tree.keyframe_insert(
                    data_path=data_path_str, 
                    frame=frame_idx
                )
            except Exception as e:
                warn_msg = f"Could not set shader node's property keyframe for '{self.obj.name}', "
                warn_msg += f"with input socket name '{input_socket_name}'."
                self.logger.warn(f"{warn_msg}. The error message is: '{e}'")
                continue



    def set_interpolation(
            self, 
            frame_idx=-1, 
            fcurve_data_path="",
            fcurve_array_idx=-1,
            interpolation_type=""
        ):
        """
        Sets the interpolation mode for specific keyframe points in the object's action.

        Args:
            frame_idx: The index of the keyframe to set the interpolation.
            fcurve_data_path (str): The search filter of the fcurver to be interpolated. 
                The transformation data path is one of ("location", "scale", "rotation_euler").
                The material data path is something like f"nodes['{principled_node.name}'].inputs[6].default_value".
            fcurve_array_idx (int): The index of the fcurve. 
                For example, the array index of the x-fcurve of location is 0, and z-fcurve of location is 2.
            interpolation_type (str): The interpolation type to apply ('BEZIER', 'LINEAR', 'CONSTANT').
        """
        # Ensure the object has animation data and an action.
        if not self.obj:
            self.logger.warn("set_interpolation(): self.obj is None")
            return
        
        # List of valid interpolation types
        valid_types = ['BEZIER', 'LINEAR', 'CONSTANT', 'SINE', 'QUAD', 'QUART', 'QUINT', 'EXPO', 'CIRC', 'BACK', 'BOUNCE', 'ELASTIC']
        if interpolation_type.upper() not in valid_types:
            warn_msg = f"Invalid interpolation type '{interpolation_type}'. "
            warn_msg += f"Supported types are: {', '.join(valid_types)}"
            self.logger.warn(warn_msg)
            return        
        
        fcurve = None
        for curv in self.obj.animation_data.action.fcurves:
            if curv.data_path.upper() == fcurve_data_path.upper() and curv.array_index == fcurve_array_idx:
                fcurve = curv
        if not fcurve:
            self.logger.warn(f"control_keyframe_handles(): F-Curve for '{fcurve_data_path}' not found.")
            return
                      
        # Check if the keyframe index is valid
        if frame_idx < 0:
            warn_msg = f"control_keyframe_handles(): Keyframe index {frame_idx} is out of range. "
            warn_msg += f"\n\t len(fcurve.keyframe_points) = {len(fcurve.keyframe_points)}"
            self.logger.warn(warn_msg)
            return
        
        # Set interpolation
        keyframe_point = None
        for kf_pnt in fcurve.keyframe_points:
            if round(kf_pnt.co.x) == frame_idx:
                keyframe_point = kf_pnt

        if keyframe_point:
            keyframe_point.interpolation = interpolation_type.upper()   
        else:
            warn_msg = f"set_interpolation(), keyframe at index {frame_idx} doesn't exist."
            return 

        # Print out the log info.
        info_msg = f"set_interpolation(), frame_idx={frame_idx}, interpolation_type='{interpolation_type}, \n"
        info_msg += f"\t fcurve_data_path='{fcurve_data_path}', fcurve_array_idx='{fcurve_array_idx}'."
        self.logger.info(info_msg)



    def control_bezier_handle(
            self, 
            fcurve_data_path="", 
            frame_idx=-1, 
            fcurve_handle_left_value=None,
            fcurve_handle_right_value=None
        ):
        """
        Controls the left and right Bezier handles for a specific keyframe.

        Args:
            fcurve_data_path (str): The data path of the property to animate (e.g., "location").
            keyframe_index (int): The index of the keyframe point to modify (starts at 0).
            fcurve_handle_left_value (float, optional): A value to determine the vertical position of the left handles, 
            fcurve_handle_right_value (float, optional): A value to determine the vertical position of the right handles,
                and always set the horizontal positions of the left and right handlers at -5 and +5.
        """
        # Ensure the object has animation data and an action.
        if not self.obj.animation_data or not self.obj.animation_data.action:
            self.logger.warn("control_bezier_handle(): self.obj has no animation data.")
            return
        
        # Ensure the fcurve exist.
        fcurve = None
        for curv in self.obj.animation_data.action.fcurves:
            if curv.data_path.upper() == fcurve_data_path.upper():
                fcurve = curv
        if not fcurve:
            self.logger.warn(f"control_bezier_handle(): F-Curve for '{fcurve_data_path}' not found.")
            return
        
        # Check if the keyframe index is valid
        if frame_idx < 0:
            self.logger.warn(f"control_bezier_handle(): Keyframe index {frame_idx} is out of range.")
            return

        # Ensure the interpolation type of the keyframe is "BEZIER"
        keyframe_point = None
        for kf_pnt in fcurve.keyframe_points:
            if round(kf_pnt.co.x) == frame_idx:
                keyframe_point = kf_pnt
        
        if not keyframe_point:
            warn_msg += f"keyframe at index {frame_idx} doesn't exist.."
            self.logger.warn(warn_msg)
            return
                    
        if keyframe_point.interpolation.upper() != 'BEZIER':
            warn_msg = f"control_bezier_handle(): This function is only for Bezier interpolation. \n"
            warn_msg += f"\t But for {frame_idx}'th keyframe, its interpolation typoe is '{keyframe_point.interpolation}'."
            self.logger.warn(warn_msg)
            return
        
        # Set the handle type
        # The valid types of the handler are ('FREE', 'ALIGNED', or 'AUTO'),
        # to control the handler, always use 'FREE' type.
        keyframe_point.handle_left_type = "FREE"
        keyframe_point.handle_right_type = "FREE"
        
        # Construct the handle vectors based on the keyframe's properties and the provided value.
        if fcurve_handle_left_value and fcurve_handle_right_value:
            # Get the keyframe's frame and value
            kf_frame = keyframe_point.co.x
            kf_value = keyframe_point.co.y
            
            # We construct the handles relative to the keyframe's position.
            # This keeps the logic simple and predictable.
            left_handle_vec = Vector((kf_frame - 5, kf_value + fcurve_handle_left_value))
            right_handle_vec = Vector((kf_frame + 5, kf_value + fcurve_handle_right_value))
            
            keyframe_point.handle_left = left_handle_vec
            keyframe_point.handle_right = right_handle_vec
        
        info_msg = f"control_bezier_handle(): Successfully modified keyframe "
        info_msg += f"at index {frame_idx} for data_path='{fcurve_data_path}', "
        info_msg += f"\n\t with fcurve_handle_left_value={fcurve_handle_left_value}, "
        info_msg += f"fcurve_handle_right_value={fcurve_handle_right_value}."
        self.logger.info(info_msg)



    def move_straight(
            self, 
            line_coordinates=((0, 0, 0), (5, 0, 0)),
            keyframe_range=(-1, 0)
        ):
        """
        Move self.obj straight alone a line. Suggest not to use this, this method is too complicated and easy to make mistake. Instead, use keyframes is more robust.

        Args:
            line_coordinates (tuple, tuple): The two tuples (x, y, z) for the line's start and end points.
            keyframe_range (tuple): The keyframe indices that the constraint starts and ends.        
        """
        if not self.obj:
            warn_msg = f"move_straight(): self.obj doesn't exist."
            self.logger.warn(warn_msg)
            return
        
        if len(line_coordinates) != 2:
            warn_msg = f"move_straight(): the line coordinates '{line_coordinates}' is not valid."
            self.logger.warn(warn_msg)
            return      
        elif len(line_coordinates[0]) != 3:
            warn_msg = f"move_straight(): line_coordinates[0] '{line_coordinates}' is not valid."
            self.logger.warn(warn_msg)
            return      
        elif len(line_coordinates[1]) != 3:
            warn_msg = f"move_straight(): line_coordinates[1] '{line_coordinates}' is not valid."
            self.logger.warn(warn_msg)
            return      
            
        if len(keyframe_range) != 2:
            warn_msg = f"move_straight(): the keyframe range '{keyframe_range}' is not valid."
            self.logger.warn(warn_msg)
            return     
        

        self.obj.location = line_coordinates[0]
        self.set_transform_keyframe(frame_idx=keyframe_range[0])

        self.obj.location = line_coordinates[1]
        self.set_transform_keyframe(frame_idx=keyframe_range[1])


    @staticmethod
    def run_demo():
        # --- 1. Scene Setup ---
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        cube = bpy.context.object
        cube.name = "Bouncing_Cube"

        keyframe = Keyframe(cube)
        
        # --- 2. Create an initial animation with keyframes ---
        # Keyframe 1: Start low
        cube.location.z = 0.0
        keyframe.set_transform_keyframe(frame_idx=1)
        
        # Keyframe 2: Bounce up
        cube.location.z = 5.0
        keyframe.set_transform_keyframe(frame_idx=25)
        
        # Keyframe 3: Fall back down
        cube.location.z = 0.0
        keyframe.set_transform_keyframe(frame_idx=50)

        # --- 3. Use the function to control the Bezier handles ---
        # We will modify the second keyframe (index 1) which is at frame 25.
        keyframe.set_interpolation(
            frame_idx=25, 
            fcurve_data_path="location",
            fcurve_array_idx=0,
            interpolation_type="Bezier"
        )
        
        # Control the Bezier handlers at keyframe 25. 
        keyframe.control_bezier_handle(
            fcurve_data_path="location", 
            frame_idx=25, 
            fcurve_handle_left_value=-2.0,  # The vertical distance of the left handle from the keyframe value
            fcurve_handle_right_value=3.0   # The vertical distance of the right handle from the keyframe value
        )


        # --- 4. Create a cube for moving straight.
        #
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))  # Create at origin
        space_ship = bpy.context.active_object
        space_ship.name = "space_ship"
        space_ship.scale = (0.3, 0.6, 0.3)

        space_ship_mat = bpy.data.materials.new(name="SpaceShipMaterial")
        space_ship_mat.diffuse_color = (0.3, 0.6, 0.6, 1)
        space_ship.data.materials.append(space_ship_mat)   

        keyframe.set_object(space_ship)
        keyframe.move_straight(
            line_coordinates=((12, -10, -1), (12, 10, 1)),
            keyframe_range=(1, 50)  
        )


        # --- 5. Set the scene frame range
        # 
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 50
        
        print("Animation setup complete. Play the animation to see the controlled Bezier handles.")



if __name__ == "__main__":
    Keyframe.run_demo()