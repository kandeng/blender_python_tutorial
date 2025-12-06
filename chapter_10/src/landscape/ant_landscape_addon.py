import bpy
import os
import sys
import json


class ANTLandscapeAddon:
    """
    A class to build a mountain covered by snow and two kinds of rocks,
    using ANT-Landscape build-in addon.

    Reference:
    CGBoost course - Master 3D Environment 
    https://www.cgboost.com/courses/master-3d-environments-in-blender
    第 4 章-ANT景观-孤山, 18:50-34:30
    """

    def __init__(self):
        """
        Initializes the Mountain and ensures the ANT.Landscape addon is enabled.
        """
        self.logger = None
        self.landscape_object = None
        self.material_texture = None

        try:
            from logger.logger import Logger
            self.logger = Logger("Landscape").getLogger()

            if self.is_ant_landscape_addon_available():
                debug_msg = f"ANTLandscapeAddon(), the usage of class 'ANTLandscapeAddon': \n"
                debug_msg += f"\t landscape = ANTLandscapeAddon() \n"
                debug_msg += f"\t landscape.create_landscape( \n"
                debug_msg += f"\t     landscape_name='my_landscape_name', \n"
                debug_msg += f"\t     landscape_preset_type='mountain_1' \n"
                debug_msg += f"\t ) \n"
                debug_msg += f"The valid 'landscape_preset_type' are: \n"
                debug_msg += f"   'abstract', 'another_noise',  'billow', \n"
                debug_msg += f"   'canyon', 'canyons', 'cauliflower_hills', 'cliff', 'crystalline', \n"
                debug_msg += f"   'default', 'default_large', 'dunes', 'flatstones', 'gully', \n"
                debug_msg += f"   'lakes_1', 'lakes_2', 'large_terrain', 'mesa', 'mounds', 'mountain_1', 'mountain_2', \n"
                debug_msg += f"   'planet', 'planet_noise', 'ridged', 'river', 'rock', 'slick_rock', \n"
                debug_msg += f"   'techno_cell', 'tech_effect', 'vlnoise_turbulence', 'volcano', 'voronoi_hills', 'yin_yang' \n"
                self.logger.debug(debug_msg)
                
        except ImportError:
            print("[ERROR] Could not import ANTLandscapeAddon class. ")


    def is_ant_landscape_addon_available(self) -> bool:
        # List all mesh operators (search for antlandscape/ant_landscape)
        mesh_ops = [op for op in bpy.ops.mesh.__dir__() if ("ant" in op.lower()) or ("land" in op.lower()) or ("preset" in op.lower())]
         
        debug_msg = f"verify_ant_landscape_addon(), Available mesh operators with 'ant' or 'land': \n"
        for op in mesh_ops:
            debug_msg += f"- {op} \n"

        # If empty: A.N.T. Landscape is not enabled/installed
        is_ant_landscape_addon_available = False
        if not mesh_ops:
            debug_msg += f"❌ No A.N.T. Landscape operators found! \n"
            is_ant_landscape_addon_available = False
        else:
            debug_msg += f"✅ Found A.N.T. Landscape operators! \n"
            is_ant_landscape_addon_available = True

        self.logger.debug(debug_msg)
        return is_ant_landscape_addon_available
    


    def create_landscape(
            self, 
            landscape_name:str="",
            landscape_preset_type:str=""
        ):
        # 1. Get the preset parameters.
        preset_kwargs = self.get_preset_terrain(
            preset_terrain=landscape_preset_type
        ) 
        
        # 2. Use ANT.Landscape addon to create terrain.
        try:
            bpy.ops.mesh.landscape_add(
                ant_terrain_name = landscape_name,
                **preset_kwargs
            )

            self.landscape_object = bpy.context.active_object
            bpy.ops.object.shade_smooth()

        except RuntimeError as e:
            warn_msg = f"create_landscape(), Failed to call 'bpy.ops.mesh.landscape_add()': '{str(e)}'"
            self.logger.warning(warn_msg)
            return
        

        # 3. Create the material for the newly created terrain.
        from modeling.material_texture import MaterialTexture
        self.material_texture = MaterialTexture(
            object_instance=self.landscape_object,
            material_name=f"{landscape_name}_material"
        )


    def get_preset_terrain(
            self,
            preset_terrain:str=""
        ) -> dict:
        match preset_terrain.lower():
            case "mountain_1":
                return ANTLandscapeAddon.preset_mountain_1
            case "mountain_2":
                return ANTLandscapeAddon.preset_mountain_2


    def set_terrain_attributes(
            self, 
            terrain_name:str="",
            terrain_attributes: dict={}
        ):
        
        # 1. Get the terrain object.
        terrain_obj = bpy.data.objects.get(terrain_name)
        if not terrain_obj:
            warn_msg = f"set_terrain_attributes(), terrain '{terrain_name}' does not exist.\n"
            self.logger.warning(warn_msg)
            return 
        
        # 2. Set the terrain object to be active.
        terrain_obj.select_set(True)
        bpy.context.view_layer.objects.active = terrain_obj
    
        # 3. Set the attributes to the terrain object.
        valid_attributes = []
        for attr_name, attr_value in terrain_attributes.items():
            # self.logger.debug(f"set_terrain_attributes(), attribute name='{attr_name}', value='{attr_value}'")
            if attr_name.lower() == "height":
                bpy.context.object.ant_landscape.height = float(attr_value)
                valid_attributes.append(attr_name)

            else:
                debug_msg = f"set_terrain_attributes(), terrain attribute '{attr_name}' does not exist. \n"
                debug_msg += f"\tThe valid terrain attribute names are:\n\t"
                for valid_attr_name in  bpy.context.object.ant_landscape.__dir__():
                    debug_msg += f"'{valid_attr_name}', "
                self.logger.debug(f"{debug_msg} \n")
        
        bpy.ops.mesh.ant_landscape_refresh()

        # 4. Print out the info message.
        if len(valid_attributes) > 0:
            info_msg = f"set_terrain_attributes(), set the following attributes to terrain '{terrain_name}': \n"
            for idx, valid_attr_name in enumerate(valid_attributes):
                attr_value = terrain_attributes[valid_attr_name]
                info_msg += f"[{idx}] attribute name='{valid_attr_name}', value={attr_value}\n"
            self.logger.info(info_msg)



    """
    Reference:
    /home/robot//.config/blender/4.4/extensions/blender_org/
    antlandscape/presets/operator/mesh.landscape_add/mountain_1.py
    """
    preset_mountain_1 = {
        "land_material":'',
        "water_material":'',
        "texture_block":'',
        "at_cursor":True,
        "smooth_mesh":True,
        "tri_face":False,
        "sphere_mesh":False,
        "subdivision_x":128,
        "subdivision_y":128,
        "mesh_size":2.0,
        "mesh_size_x":2.0,
        "mesh_size_y":2.0,
        "random_seed":3,
        "noise_offset_x":0.0,
        "noise_offset_y":0.0,
        "noise_offset_z":0.0,
        "noise_size_x":1.0,
        "noise_size_y":1.0,
        "noise_size_z":1.0,
        "noise_size":0.75,
        "noise_type":'ridged_multi_fractal',
        "basis_type":'BLENDER',
        "vl_basis_type":'VORONOI_F2F1',
        "distortion":1.0,
        "hard_noise":'0',
        "noise_depth":12,
        "amplitude":0.5,
        "frequency":2.0,
        "dimension":1.0,
        "lacunarity":2.0,
        "offset":0.880000114440918,
        "gain":4.199997901916504,
        "marble_bias":'0',
        "marble_sharp":'0',
        "marble_shape":'2',
        "height":0.5,
        "height_invert":False,
        "height_offset":0.25,
        "fx_mixfactor":0.0,
        "fx_mix_mode":'0',
        "fx_type":'0',
        "fx_bias":'0',
        "fx_turb":0.0,
        "fx_depth":0,
        "fx_amplitude":0.5,
        "fx_frequency":1.5,
        "fx_size":1.0,
        "fx_loc_x":0.0,
        "fx_loc_y":0.0,
        "fx_height":0.5,
        "fx_invert":False,
        "fx_offset":0.0,
        "edge_falloff":'3',
        "falloff_x":2.0,
        "falloff_y":2.0,
        "edge_level":0.0,
        "maximum":1.0,
        "minimum":-1.0,
        "vert_group":'',
        "strata":5.0,
        "strata_type":'0',
        "water_plane":False,
        "water_level":0.009999999776482582,
        "remove_double":False,
        "show_main_settings":True,
        "show_noise_settings":True,
        "show_displace_settings":True,
        "refresh":True,
        "auto_refresh":True
    }
    

    """
    Reference:
    /home/robot//.config/blender/4.4/extensions/blender_org/
    antlandscape/presets/operator/mesh.landscape_add/mountain_2.py
    """
    preset_mountain_2 = {
        "land_material":'',
        "water_material":'',
        "texture_block":'',
        "at_cursor":True,
        "smooth_mesh":True,
        "tri_face": False,
        "sphere_mesh": False,
        "subdivision_x":128,
        "subdivision_y":128,
        "mesh_size":2.0,
        "mesh_size_x":2.0,
        "mesh_size_y":2.0,
        "random_seed":134,
        "noise_offset_x":0.0,
        "noise_offset_y":0.0,
        "noise_offset_z":0.0,
        "noise_size_x":1.0,
        "noise_size_y":1.0,
        "noise_size_z":1.0,
        "noise_size":1.0,
        "noise_type":'vl_hTerrain',
        "basis_type":'BLENDER',
        "vl_basis_type":'VORONOI_F1',
        "distortion":1.0,
        "hard_noise":'1',
        "noise_depth":8,
        "amplitude":0.5,
        "frequency":1.75,
        "dimension":1.0,
        "lacunarity":2.0,
        "offset":1.0,
        "gain":3.0,
        "marble_bias":'2',
        "marble_sharp":'0',
        "marble_shape":'1',
        "height":0.4000000059604645,
        "height_invert":False,
        "height_offset":0.0,
        "fx_mixfactor":0.0,
        "fx_mix_mode":'0',
        "fx_type":'0',
        "fx_bias":'0',
        "fx_turb":0.0,
        "fx_depth":0,
        "fx_amplitude":0.5,
        "fx_frequency":1.5,
        "fx_size":1.0,
        "fx_loc_x":0.0,
        "fx_loc_y":0.0,
        "fx_height":0.5,
        "fx_invert":False,
        "fx_offset":0.0,
        "edge_falloff":'3',
        "falloff_x":2.5,
        "falloff_y":2.5,
        "edge_level":0.0,
        "maximum":1.0,
        "minimum":0.0,
        "vert_group":'',
        "strata":0.5,
        "strata_type":'3',
        "water_plane":False,
        "water_level":0.009999999776482582,
        "remove_double":False,
        "show_main_settings":True,
        "show_noise_settings":True,
        "show_displace_settings":True,
        "refresh":True,
        "auto_refresh":True
    }
    

    @staticmethod
    def usage_demo():
        # Clean up the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True) 

        """
        # Create 2 mountains
        first_mountain = ANTLandscapeAddon(landscape_name="first_mountain")
        first_mountain.location = (-8, -8, 0)
        first_mountain.scale = (8, 8, 8)   

        second_mountain = ANTLandscapeAddon(landscape_name="second_mountain")
        second_mountain.location = (4, 4, 0)
        second_mountain.scale = (4, 4, 4)          
        """
        mountain = ANTLandscapeAddon()
        mountain.create_landscape(
            landscape_name="ant_mountain",
            landscape_preset_type="mountain_2"
        )

        # bpy.context.object.ant_landscape.height = 1.6
        # bpy.ops.mesh.ant_landscape_refresh()
        mountain.set_terrain_attributes(
            terrain_name="ant_mountain",
            terrain_attributes={
                "height": 1.234,
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