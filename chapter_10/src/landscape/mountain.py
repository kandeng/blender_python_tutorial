import os
import sys
import bpy
import math
import numpy as np
from pathlib import Path


class Mountain:
    """
    A class to use ANT_landscape build-in addon to generate mountain, valley, lake, flat terrain etc.
    """
    def __init__(
            self,
            mountain_name:str="",
            mountain_type:str="mountain_1"            
        ):
        self.logger = None
        self.ant_landscape_addon = None
        self.mountain = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Landscape").getLogger()

            from landscape.ant_landscape_addon import ANTLandscapeAddon
            self.ant_landscape_addon = ANTLandscapeAddon()

            mountain_name = mountain_name.strip()
            if len(mountain_name) == 0:
                self.logger.warning(f"Mountain(), mountain_name is emptry.")
                return

            self.mountain = self.ant_landscape_addon.create_landscape(
                landscape_name=mountain_name,
                landscape_preset_type=mountain_type
            )
            self.logger.info(f"Mountain(), mountain '{mountain_name}' is created, of type '{mountain_type}'.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Mountain class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize Mountain class, error message: '{str(e)}'")



    def set_terrain_attributes(
            self, 
            mountain_name:str="",
            mountain_attributes:dict={}
        ):
        self.ant_landscape_addon.set_terrain_attributes(
            terrain_name=mountain_name,
            terrain_attributes=mountain_attributes            
        )



    @staticmethod
    def usage_demo():
        # Clean up the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True) 

        # Create 2 mountains
        first_mountain = Mountain(
            mountain_name="first_mountain"        
        )
        bpy.context.object.location = (5.0, 5.0, 0.0) 
        first_mountain.set_terrain_attributes(
            mountain_name="first_mountain",
            mountain_attributes={
                "height": 1.234
            }            
        ) 

        second_mountain = Mountain(
            mountain_name="second_mountain",
            mountain_type="mountain_2"            
        )
        bpy.context.object.location = (-5.0, -5.0, 0.0) 
        second_mountain.set_terrain_attributes(
            mountain_name="second_mountain",
            mountain_attributes={
                "random_seed": 16,
                "non_exist": "Nonsense"
            }            
        )

        # Set up the sun. 
        bpy.context.scene.render.engine = 'CYCLES'
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 2.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (15, 10.0, 50.0) 
        bpy.context.collection.objects.link(sun_obj)