import bpy
from mathutils import Vector

class Constraint:
    def __init__(self, obj=None):
        self.logger = None
        self.obj = obj

        try:
            from logger.logger import LlamediaLogger
            # Stream the log to the 'Animation' subdirectory in the log directory.
            self.logger = LlamediaLogger("Animation").getLogger()
            self.logger.info(f"Constraint class initialized.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Constraint class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize Constraint class, error message: '{e}'")
 

    def set_object(self, obj):
        self.obj = obj

    
    def track_to(
            self, 
            target_obj=None, 
            track_axis="", 
            up_axis=""
        ) -> bpy.types.Object:
        """
        Make the self.obj always faces to the target object, no matter where and how the self.obj moves. 

        Args:
            target_obj (bpy.types.Object): The target object that self.obj tracks to.
            track_axis (str): The valid values are ('FORWARD_X', 'FORWARD_Y', 'FORWARD_Z', 'TRACK_NEGATIVE_X', 'TRACK_NEGATIVE_Y', 'TRACK_NEGATIVE_Z').
            up_axis (str): The valid values are 'UP_Y'...
            return: The constraint target object that self.obj tracks to.
        """
        if not self.obj:
            warn_msg = f"track_to(): self.obj doesn't exist."
            self.logger.warn(warn_msg)
            return
        
        if not target_obj:
            warn_msg = f"track_to(): target_obj doesn't exist."
            self.logger.warn(warn_msg)
            return            

        # Add a Track To constraint to self.obj
        track_to = self.obj.constraints.new(type='TRACK_TO')
        track_to.name = target_obj.name
        track_to.target = target_obj
        track_to.track_axis = track_axis if len(track_axis) > 0 else 'TRACK_NEGATIVE_Z'
        track_to.up_axis = up_axis if len(up_axis) > 0 else 'UP_Y'

        info_msg = f"track_to(): self.obj '{self.obj.name}' will always track to target object '{target_obj.name}',"
        info_msg += f"\n\t track_axis='{track_to.track_axis}', up_axis='{track_to.up_axis}'."
        self.logger.info(info_msg)

        return track_to

    
    def follow_path(
            self,
            path_curve=None,
            forward_axis="",
            up_axis=""
        ) -> bpy.types.Object:
        """
        Make the self.obj move along a path curve. 

        Args:
            path_curve (bpy.types.Object): The path curve for self.obj to follow.
            forward_axis (str): The valid values are ('FORWARD_X', 'FORWARD_Y', 'FORWARD_Z', 'TRACK_NEGATIVE_X', 'TRACK_NEGATIVE_Y', 'TRACK_NEGATIVE_Z').
            up_axis (str): The valid values are 'UP_Z'...
            return: The constraint path curve object that self.obj tracks to.
        """
        if not self.obj:
            warn_msg = f"follow_path(): self.obj doesn't exist."
            self.logger.warn(warn_msg)
            return
        
        if not path_curve:
            warn_msg = f"follow_path(): path_curve is None."
            self.logger.warn(warn_msg)
            return         

        # Add a Follow Path constraint to self.obj
        follow_path = self.obj.constraints.new(type='FOLLOW_PATH')
        follow_path.name = path_curve.name
        follow_path.target = path_curve
        follow_path.use_curve_follow = True
        follow_path.forward_axis = forward_axis if len(forward_axis) > 0 else 'FORWARD_Y' 
        follow_path.up_axis = up_axis if len(up_axis) > 0 else 'UP_Z'
        follow_path.use_fixed_location = False  # Allow movement along the path
        
        info_msg = f"follow_path(): self.obj '{self.obj.name}' will follow the path '{path_curve.name}',"
        info_msg += f"\n\t forward_axis='{follow_path.forward_axis}', up_axis='{follow_path.up_axis}'."
        self.logger.info(info_msg)

        return follow_path


    def set_constraint_keyframes(
            self, 
            constraint=None,
            keyframe_range=(-1, 0)
        ):
        """
        Set the starting keyframe and ending keyframe for the constraint to play. 

        Args:
            constraint (bpy.types.Object): The constraint object, 
                e.g. the target object to track to, and the curve path to follow.
            keyframe_range (tuple): The keyframe indices that the constraint starts and ends.
        """      
        if not self.obj:
            warn_msg = f"set_constraint_keyframes(): self.obj doesn't exist."
            self.logger.warn(warn_msg)
            return
        
        if not constraint:
            warn_msg = f"set_constraint_keyframes(): the input constraint is None."
            self.logger.warn(warn_msg)
            return         
        
        if len(keyframe_range) != 2:
            warn_msg = f"set_constraint_keyframes(): the keyframe range {keyframe_range} is not valid."
            self.logger.warn(warn_msg)
            return         

        # For other constraints like Track To, we use eval_time on the target's data
        constraint_data = constraint.target.data
        bpy.context.scene.frame_set(keyframe_range[0])
        constraint_data.eval_time = keyframe_range[0]
        constraint_data.keyframe_insert(data_path="eval_time", frame=keyframe_range[0])

        bpy.context.scene.frame_set(keyframe_range[1])
        constraint_data.eval_time = keyframe_range[1]
        constraint_data.keyframe_insert(data_path="eval_time", frame=keyframe_range[1])

        info_msg = f"set_constraint_keyframes(): self.obj '{self.obj.name}' "
        info_msg += f"will play the constraint '{constraint.name}',"
        info_msg += f"\n\t in the keyframe range '{keyframe_range}'."
        self.logger.info(info_msg)  


    def circle_around(
            self, 
            target_obj=None,
            radius=-1,
            keyframe_range=(-1, 0)
        ):
        """
        Make self.obj moves around the target object. 

        Args:
            target_obj (bpy.types.Object): The target object to circle around.
            radius (float): The radius of the circle.
            keyframe_range (tuple): The keyframe indices that the constraint starts and ends.
        """      
        if not self.obj:
            warn_msg = f"circle_around(): self.obj doesn't exist."
            self.logger.warn(warn_msg)
            return
        
        if not target_obj:
            warn_msg = f"circle_around(): the input target_obj is None."
            self.logger.warn(warn_msg)
            return         

        if radius <= 0:
            warn_msg = f"circle_around(): the radius of the circle, radius={radius}, is not valid."
            self.logger.warn(warn_msg)
            return     

        if len(keyframe_range) != 2:
            warn_msg = f"circle_around(): the keyframe range '{keyframe_range}' is not valid."
            self.logger.warn(warn_msg)
            return         
        
        _ = self.track_to(
            target_obj=target_obj, 
            track_axis='TRACK_Z', #'TRACK_NEGATIVE_Z', 
            up_axis='UP_Y'
        ) 

        bpy.ops.curve.primitive_bezier_circle_add(
            radius=radius, 
            location=target_obj.location
        )
        circle_curve = bpy.context.active_object
        circle_curve.name="earth_orbit"
        circle_curve.data.path_duration = keyframe_range[1] - keyframe_range[0] + 1  
        
        circle_constraint = self.follow_path(
            path_curve=circle_curve,
            forward_axis='FORWARD_X',
            up_axis='UP_Z'
        ) 
        
        self.set_constraint_keyframes(
            constraint=circle_constraint,
            keyframe_range=keyframe_range
        )

        info_msg = f"circle_around(): self.obj '{self.obj.name}' will circle around " 
        info_msg += f"the target object '{target_obj.name}',"
        info_msg += f"\n\t in the keyframe range '{keyframe_range}'."
        self.logger.info(info_msg)  



    def create_line(
            self,
            line_name="Line",
            line_coordinates=((0, 0, 0), (5, 0, 0))
        ) -> bpy.types.Object:
        """
        Create a straight line between two points using a Nurbs path.
        
        Args:
            line_name (str): Name for the line object.
            line_coordinates (tuple, tuple): The two tuples (x, y, z) for the line's start and end points.
            return (bpy.types.Object): The created line object. 
        """
        if len(line_coordinates) != 2:
            warn_msg = f"create_line(): the line coordinates '{line_coordinates}' is not valid."
            self.logger.warn(warn_msg)
            return      
        elif len(line_coordinates[0]) != 3:
            warn_msg = f"create_line(): line_coordinates[0] '{line_coordinates}' is not valid."
            self.logger.warn(warn_msg)
            return      
        elif len(line_coordinates[1]) != 3:
            warn_msg = f"create_line(): line_coordinates[1] '{line_coordinates}' is not valid."
            self.logger.warn(warn_msg)
            return    
        
        # Create a new curve data block.
        # The 'nurbs' type tells Blender it's a NURBS curve.
        curve_data = bpy.data.curves.new(name=line_name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.use_path = True  # Enable path evaluation

        # Create a new spline within the curve data block.
        # We specify the type as 'NURBS' to ensure it's a NURBS spline.
        spline = curve_data.splines.new(type='NURBS')
        
        # Add two points to the spline. We first resize it to hold 2 points.
        spline.points.add(count=1) # Adds one point, so we have a total of 2.

        # Access the two points and set their coordinates.
        # Note: For NURBS, the location is stored in the 'co' attribute.
        spline.points[0].co = Vector(line_coordinates[0] + (1.0,)) # The fourth value is the 'weight'.
        spline.points[1].co = Vector(line_coordinates[1] + (1.0,))
        
        # Configure the NURBS spline for proper path following
        spline.use_endpoint_u = True  # Makes the curve reach the endpoints
        spline.order_u = 2  # Linear curve between two points
        
        # Create a new object and link the curve data to it.
        straight_line = bpy.data.objects.new(line_name, curve_data)
        
        # Link the new object to the scene's collection to make it visible.
        bpy.context.collection.objects.link(straight_line)

        # Select and make the new object active for immediate use.
        bpy.context.view_layer.objects.active = straight_line
        straight_line.select_set(True)

        info_msg = f"create_line(): create a straight line with NURBS, named '{line_name}', " 
        info_msg += f"starting from '{line_coordinates[0]}', ending with '{line_coordinates[1]}'."
        self.logger.info(info_msg)      

        return straight_line


    def move_straight(
            self, 
            line_coordinates=((0, 0, 0), (5, 0, 0)),
            keyframe_range=(-1, 0)
        ):
        """
        Move self.obj straight alone a line. 

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

        line_name="straight_line"
        straight_line = self.create_line(
            line_name=line_name,
            line_coordinates=line_coordinates
        )
        straight_line.data.path_duration = keyframe_range[1] - keyframe_range[0] + 1  
        
        # Create the Follow Path constraint
        forward_axis_rectified = ""
        if line_coordinates[0][1] > line_coordinates[1][1]:  # If start Y > end Y
            forward_axis_rectified = 'TRACK_NEGATIVE_Y'
        else:
            forward_axis_rectified = 'FORWARD_Y'

        line_constraint = self.follow_path(
            path_curve=straight_line,
            forward_axis=forward_axis_rectified,
            up_axis='UP_Z'
        ) 
        
        # Set the offset to start at the beginning of the path
        line_constraint.offset = 0
        line_constraint.use_curve_follow = True

        self.set_constraint_keyframes(
            constraint=line_constraint,
            keyframe_range=keyframe_range
        )

        info_msg = f"move_straight(): move self.obj '{self.obj.name}' "
        info_msg += f"along a straight line, named '{line_name}', " 
        info_msg += f"\n\t starting from '{line_coordinates[0]}', ending with '{line_coordinates[1]}'."
        self.logger.info(info_msg)          



    @staticmethod
    def run_demo():
        # Clear default objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # --------------------------
        # 1. Create Sun at (0, 0, 0)
        # --------------------------
        # Create the sun.
        bpy.ops.mesh.primitive_uv_sphere_add(radius=2, location=(0, 0, 0))
        sun = bpy.context.active_object
        sun.name = "Sun"

        # Sun material
        sun_mat = bpy.data.materials.new(name="SunMaterial")
        sun_mat.diffuse_color = (1, 0.8, 0.2, 1)
        sun.data.materials.append(sun_mat)

        # --------------------------
        # 2. Earth setup with correct keyframing
        # --------------------------
        # Create the earth
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8)
        earth = bpy.context.active_object
        earth.name = "Earth"

        # Earth material
        earth_mat = bpy.data.materials.new(name="EarthMaterial")
        earth_mat.diffuse_color = (0.2, 0.3, 1, 1)
        earth.data.materials.append(earth_mat)    

        # Lock Z location
        earth.lock_location[2] = True    

        # --------------------------
        # 3. Setup the constraints and animation keyframes.
        # --------------------------
        earth_around_sun = Constraint(earth)

        # Make the earth track to the sun. 
        earth_constraint = earth_around_sun.circle_around(
            target_obj=sun,
            radius=10,
            keyframe_range=(1, 250)  # Full orbit over 250 frames
        )        


        # --------------------------
        # 4. Setup the constraints and animation keyframes.
        # --------------------------
        # Create spaceship at origin first, then apply scale and constraint
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))  # Create at origin
        space_ship = bpy.context.active_object
        space_ship.name = "space_ship"
        space_ship.scale = (0.3, 0.6, 0.3)
        
        # Apply transforms to make sure scale is applied
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        space_ship_mat = bpy.data.materials.new(name="SpaceShipMaterial")
        space_ship_mat.diffuse_color = (0.3, 0.6, 0.6, 1)
        space_ship.data.materials.append(space_ship_mat)   

        # --------------------------
        # 5. Setup the constraints and animation keyframes.
        # --------------------------
        earth_around_sun.set_object(space_ship)

        earth_around_sun.move_straight(
            line_coordinates=((12, -10, -1), (12, 10, 1)),
            keyframe_range=(1, 250)  # Movement over 250 frames
        )



if __name__ == "__main__":
    Constraint.run_demo()