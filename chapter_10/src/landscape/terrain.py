import os
import sys
import bpy
import math
import numpy as np
from pathlib import Path


class Terrain:
    """
    A class to generate mountain, valley, lake, flat terrain etc.
    """
    def __init__(self):
        self.logger = None
        
        try:
            from logger.logger import Logger
            self.logger = Logger("Landscape").getLogger()
            self.logger.info(f"Terrain class initialized.")

            self.verify_ant_landscape_addon()

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Terrain class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize Terrain class, error message: '{str(e)}'")


    def verify_ant_landscape_addon(self):
        # List all mesh operators (search for antlandscape/ant_landscape)
        mesh_ops = [op for op in bpy.ops.mesh.__dir__() if ("ant" in op.lower()) or ("land" in op.lower())]
         
        debug_msg = f"verify_ant_landscape_addon(), Available mesh operators with 'ant' or 'land': \n"
        for op in mesh_ops:
            debug_msg += f"- {op} \n"

        # If empty: A.N.T. Landscape is not enabled/installed
        if not mesh_ops:
            debug_msg += f"❌ No A.N.T. Landscape operators found! \n"
        else:
            debug_msg += f"✅ Found A.N.T. Landscape operators! \n"

        self.logger.debug(debug_msg)


    def create_mountain(
            self,
            mountain_name:str=""    
        ):
        """
        Create a mountain using the ANT Landscape build-in addon. 
        The ANT Landscape build-in addon parameters refer to:
        /home/robot/.config/blender/4.4/extensions/blender_org/antlandscape/add_mesh_ant_landscape.py
        class AntAddLandscape(bpy.types.Operator):
            bl_idname = "mesh.landscape_add"
            bl_label = "Another Noise Tool - Landscape"
        """

        try:
            """
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.normals_make_consistent()
            bpy.ops.object.editmode_toggle()
            """

            bpy.ops.mesh.landscape_add(
                ant_terrain_name=mountain_name,
                smooth_mesh=True,
                subdivision_x=128,
                subdivision_y=128,
                mesh_size_x=2.0,
                mesh_size_y=2.0,
                noise_type='hetero_terrain',  # Good for mountainous terrain
                basis_type='BLENDER',
                noise_depth=8,
                dimension=0.8,
                lacunarity=2.0,
                offset=0.9,
                gain=2.5,
                height=0.8,
                height_invert=False,
                height_offset=-0.2,
                maximum=2.0,
                minimum=-0.5,
                random_seed=12345,  # Fixed seed for reproducibility
                refresh=True,  
                auto_refresh=True
            )

        except RuntimeError as e:
            warn_msg = f"create_mountain(), Failed to call 'bpy.ops.mesh.landscape_add()': '{str(e)}'"
            self.logger.warning(warn_msg)
            return

        
        # Get the created landscape object
        mountain_obj = bpy.context.active_object
        if mountain_obj:
            bpy.ops.object.shade_smooth()
            mountain_obj.location = (0, 0, 0)
            mountain_obj.scale = (5, 5, 3)

            info_msg = f"create_mountain(), use ANT_landscape addon to create a mountain '{mountain_obj.name}'."
            self.logger.info(info_msg)
            
        else:
            print("Failed to create mountain")
            warn_msg = f"create_mountain(), Failed to get the mountain object "
            warn_msg += f"created by 'bpy.ops.mesh.landscape_add()'"
            self.logger.info(warn_msg)

        return mountain_obj
            

    @staticmethod
    def usage_demo():
        # Clean up the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True) 
        bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))

        # Create 2 mountains
        terrain = Terrain()

        first_mountain = terrain.create_mountain(mountain_name="first_mountain")
        first_mountain.location = (-8, -8, 0)
        first_mountain.scale = (8, 8, 8)   

        second_mountain = terrain.create_mountain(mountain_name="second_mountain")
        second_mountain.location = (4, 4, 0)
        second_mountain.scale = (4, 4, 4)        

        # Set up the sun. 
        bpy.context.scene.render.engine = 'CYCLES'
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 2.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (15, 10.0, 50.0) 
        bpy.context.collection.objects.link(sun_obj)