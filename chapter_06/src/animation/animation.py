import bpy

class Animation:
    def __init__(self, obj=None):
        self.logger = None

        self.obj = obj
        self.keyframe = None
        self.constraint = None
        
        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("Animation").getLogger()
            self.logger.info(f"Animation class initialized, self.obj.name='{self.obj.name}'")

            from animation.keyframe import Keyframe
            from animation.constraint import Constraint
            self.keyframe = Keyframe(self.obj)
            self.constraint = Constraint(self.obj)

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Animation class, error message: '{e}'")
            else:
                print(f"[ERROR] Could not initialize Animation class, error message: '{e}'")
 

    def set_object(self, obj):
        self.obj = obj
        self.keyframe.set_object(self.obj)
        self.constraint.set_object(self.obj)


    def set_parent(self, parent_obj):
        if parent_obj is None:
            self.logger.warn("set_parent(), parent_obj is None")
            return
        else:
            self.logger.info(f"set_parent(), parent_obj.name='{parent_obj.name}'")
            
        # Set the child's parent to the parent object.
        self.obj.parent = parent_obj
        # This line preserves the child's original world-space location by
        # applying the inverse of the parent's world matrix.
        self.obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()


    def circle_around(
            self, 
            target_obj=None,
            radius=-1,
            keyframe_range=(-1, 0)
        ):
        self.keyframe.circle_around(
            target_obj=target_obj,
            radius=radius,
            keyframe_range=keyframe_range       
        )

    def move_straight(
            self, 
            line_coordinates=((0, 0, 0), (5, 0, 0)),
            keyframe_range=(-1, 0)
        ):
        self.keyframe.move_straight(
            line_coordinates=line_coordinates,
            keyframe_range=keyframe_range           
        )        


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
        # 4. Create Spaceship
        # --------------------------
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))  # Create at origin
        space_ship = bpy.context.active_object
        space_ship.name = "Spaceship"
        space_ship.scale = (0.3, 0.6, 0.3)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        # Spaceship material
        space_ship_mat = bpy.data.materials.new(name="SpaceshipMaterial")
        space_ship_mat.diffuse_color = (0.8, 0.8, 0.8, 1)
        space_ship.data.materials.append(space_ship_mat)           

        # --------------------------
        # 5. Using constraint, to move the earth around the sun.
        # --------------------------
        solar_animation = Animation(earth)

        # Make the earth circle around the sun. 
        solar_animation.circle_around(
            target_obj=sun,
            radius=10,
            keyframe_range=(1, 250)  # Full orbit over 250 frames
        )        

        # --------------------------
        # 6. Using constraint, to move the moon around the earth.
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
        # 7. Using keyframes, to move the spaceship along a straight line.
        # --------------------------
        solar_animation.set_object(space_ship)

        solar_animation.move_straight(
            line_coordinates=((12, -10, -1), (12, 10, 1)),
            keyframe_range=(1, 250)  # Movement over 250 frames
        )

        # --------------------------
        # 8. Set the animation frame range for the Blender UI.
        # --------------------------
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 250