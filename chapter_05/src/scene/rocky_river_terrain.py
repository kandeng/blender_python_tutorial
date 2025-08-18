# 
# A scene with a riverbed, a water surface, some rocks, and landscape HDRi
# 
import os
import sys
import random
import pprint

import bpy


class RockyRiverTerrain:
    def __init__(self, plane_width=10, plane_length=20):
        self.riverbed_generator = None 
        self.water_generator = None
        self.rock_generator = None
        self.texture_applier = None

        self.plane_width = plane_width
        self.plane_length = plane_length
        self.subdivisions = [(self.plane_width * 2 - 2), (self.plane_length * 2 - 2)]

        self.rocks = []

        try:
            from model.riverbed_generator import RiverbedGenerator
            self.riverbed_generator = RiverbedGenerator()

            from model.water_generator import WaterGenerator
            self.water_generator = WaterGenerator()

            from model.rock_generator import RockGenerator
            self.rock_generator = RockGenerator()

            from shader_modifier.apply_texture_asset import ApplyTexture
            self.texture_applier = ApplyTexture()

            from hdri.dome_with_hdri_and_sun_generator import DomeHdriGenerator
            self.dome_hdri_generator = DomeHdriGenerator()

        except ImportError as e:
            print(f"[ERROR] Could not import custom class. Exception: '{str(e)}'")  



    def create_riverbed_terrain(self):
        print(f"\n[INFO] Create a riverbed terrain...")

        # 1. Create a flat terrain plane. 
        self.riverbed_generator.create_terrain(
            plane_width=self.plane_width, 
            plane_length=self.plane_length, 
            subdivisions=self.subdivisions
        )     

        # 2. Apply a rocky texture to the flat plane, to avoid fragmentation.
        rocky_texture_directory = "/home/robot/movie_blender_studio/asset/texture/rocks_ground_05_2k.blend/textures"
        self.texture_applier.set_object(self.riverbed_generator.plane)
        self.texture_applier.set_texture_directory(rocky_texture_directory)

        self.texture_applier.create_base_nodes()
        self.texture_applier.create_texture_nodes()
        # After some testing, 3.5 is an appropriate value for the displace strength. 
        self.texture_applier.create_displacement_modifier(disp_strength=3.5)
    
        # 3. Distort the flat to a riverbed. 
        self.riverbed_generator.select_riverbed_vertices()
        self.riverbed_generator.dig_riverbed(min_pit_depth=0.2, max_pit_depth=0.5, pit_radius=2.5)
        self.riverbed_generator.raise_riverbank(min_riverbank_height=0.0, max_riverbank_height=0.2, bump_radius=3.0)
        self.riverbed_generator.align_riverbank_edges(proportional_radius=3.0)

        # 4. Apply a moss texture to the riverbed. 
        moss_texture_directory = "/home/robot/movie_blender_studio/asset/texture/Moss002_2K-JPG"
        self.texture_applier.set_object(self.riverbed_generator.plane)
        self.texture_applier.set_secondary_texture_directory(moss_texture_directory)
        self.texture_applier.apply_another_texture()

        # 5. For testing purpose, print out all the shader nodes. 
        self.riverbed_generator.plane.select_set(True)
        bpy.context.view_layer.objects.active = self.riverbed_generator.plane   
        bpy.ops.object.shade_smooth()
        
        # 6. For testing purpose, print out all the shader nodes. 
        print(f"\n[TEST] Following is a list of all the shader nodes for riverbed:")
        pprint.pprint(self.texture_applier.node_names)
        print(f"\n")
          

    def add_water_to_river(self):
        print(f"\n[INFO] Adding water to the riverbed...")
        self.water_generator.create_water((self.plane_width, self.plane_length), self.subdivisions)

        location_below_horizon = (0.0, 0.0, -1.0 * self.plane_width / 10.0)
        self.water_generator.move_water(location_below_horizon)
        self.water_generator.delete_vertices_beyond_waterlines(
            self.riverbed_generator.left_waterline,
            self.riverbed_generator.right_waterline)
        

    def add_some_rocks(self, num_rocks=10):
        print(f"\n[INFO] Adding {num_rocks} rocks to the scene...")

        # 1. Get all possible locations for the rocks from the riverbed vertices
        riverbed_vertices = self.riverbed_generator.plane.data.vertices
        possible_locations = [riverbed_vertices[i].co for i in self.riverbed_generator.riverbed_indices]

        if len(possible_locations) < num_rocks:
            print(f"[WARNING] Not enough vertices in riverbed to place {num_rocks} rocks.", end=" ")
            print(f"Placing {len(possible_locations)} instead.")
            num_rocks = len(possible_locations)

        # Randomly select locations for the rocks
        selected_locations = random.sample(possible_locations, num_rocks)
        
        # 2. Create some rocks, and apply rock and moss textures to them.
        rock_texture_files = "/home/robot/movie_blender_studio/asset/texture/Rock003_2K-JPG/"
        moss_texture_files = "/home/robot/movie_blender_studio/asset/texture/Moss002_2K-JPG"
   
        for i, loc in enumerate(selected_locations):
            print(f"\n--- Creating Rock {i+1}/{num_rocks} ---")
            
            # Randomize rock properties
            min_scale = self.plane_width * 0.1
            max_scale = self.plane_width * 0.25
            scale = (random.uniform(min_scale, max_scale), random.uniform(min_scale, max_scale), random.uniform(min_scale, max_scale))
            skew = (random.random(), random.random(), random.random())
            rotation = (random.uniform(0, 6.28318), random.uniform(0, 6.28318), random.uniform(0, 6.28318)) # 2*pi

            self.rock_generator.create_rock(scale=scale, skew=skew)
            if self.rock_generator.rock_object:
                self.rock_generator.move_rock(location=loc)
                self.rock_generator.scale_rock(scale=scale)
                # self.rock_generator.rotate_rock(angle=rotation)

                self.rock_generator.texture_applier.use_modifier=True
                self.rock_generator.apply_texture(rock_texture_files)
                self.rock_generator.texture_applier.create_displacement_modifier()

                self.rock_generator.texture_applier.use_modifier=False
                self.rock_generator.apply_secondary_texture(moss_texture_files)

            self.rocks.append(self.rock_generator.rock_object)

        print(f"\n[SUCCESS] Finished adding {num_rocks} rocks.")
    

    def create_hdri_background(self):
        print("\n[INFO] Creating HDRi landscape background...")

        hdri_filename="/home/robot/movie_blender_studio/asset/hdri/kloppenheim_06_4k.exr"
        self.dome_hdri_generator.create(radius=self.plane_length * 0.75, hdri_path=hdri_filename)
        self.dome_hdri_generator.set_hdri_brightness(brightness=2.5)

        if self.riverbed_generator.plane:
            riverbed_dimensions = self.riverbed_generator.plane.dimensions

            self.dome_hdri_generator.set_floor_basin_height(
                rectangular_region= (-0.5 * self.plane_width, -0.5 * self.plane_length, 
                                     0.5 * self.plane_width, 0.5 * self.plane_length),
                height_to_change= -1.0 * riverbed_dimensions[2] 
            )

    @staticmethod
    def run_demo():
        print("[INFO] --- Running RockyRiverTerrain Scene Demo ---")

        # It's good practice to start with a clean scene for a demo.
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.active_object: bpy.ops.object.delete()

        rocky_river_terrain = RockyRiverTerrain(plane_width=20, plane_length=40)
        rocky_river_terrain.create_riverbed_terrain()
        rocky_river_terrain.add_water_to_river()
        rocky_river_terrain.add_some_rocks(num_rocks=10)
        rocky_river_terrain.create_hdri_background()

        dome_floor_z = -0.1 * rocky_river_terrain.plane_length * 0.75
        rocky_river_terrain.riverbed_generator.move_riverbed(location=(0, 0, dome_floor_z))
        rocky_river_terrain.water_generator.move_water(location=(0.0, 0.0, dome_floor_z))

        for rock in rocky_river_terrain.rocks:
            rock.location = (rock.location[0], rock.location[1], rock.location[2]+dome_floor_z)
        


if __name__ == "__main__":
    RockyRiverTerrain.run_demo()
    