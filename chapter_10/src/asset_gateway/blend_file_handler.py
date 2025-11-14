import os
import sys
import json
import bpy


class BlendFileHandler:
    """
    To retrieve objects from a .blend file.
    """
    def __init__(
            self, 
            blend_filepath:str=""
        ):
        self.logger = None
        self.blend_filepath=blend_filepath.strip()
        
        try:
            from logger.logger import Logger
            self.logger = Logger("AssetGateway").getLogger()
            self.logger.info(f"BlendFileHandler class initialized.")

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize BlendFileHandler class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize BlendFileHandler class, error message: '{str(e)}'")



    def get_all_asset_names(self) -> dict:
        """
        List all asset names in a single .blend file by temporarily soft linking them to the current 'bpy.data'.

        Returns:
            dict: A dict of all the asset object names in the .blend file
        """
        if not os.path.exists(self.blend_filepath):
            warn_msg = f"get_all_assets(), Source .blend file doesn't exist: '{self.blend_filepath}'."
            self.logger.warning(warn_msg)
            return {}
        
        try:
            with bpy.data.libraries.load(self.blend_filepath, link=True) as (data_from, data_to):
                # data_from.objects contains all object names in the external file
                asset_names = {
                    "Objects": data_from.objects,
                    "Materials": data_from.materials,
                    "Node Groups": data_from.node_groups,
                    "Worlds": data_from.worlds,
                    "Images": data_from.images                 
                }

                asset_names_str = json.dumps(asset_names, ensure_ascii=False, indent=2)
                info_msg = f"get_all_asset_names(), following is all the asset names in the '{self.blend_filepath}' .blend file:\n"
                info_msg += asset_names_str
                self.logger.info(info_msg)
                return asset_names

        except Exception as e:
            warn_msg = f"get_all_asset_names, following exception was thrown when listing all the assets in "
            warn_msg += f"'{self.blend_filepath}' .blend file: {str(e)}\n"
            self.logger.warning(warn_msg)
            return {}


    def get_all_asset_names_obsolete(self) -> dict:
        """
        List all asset names in a single .blend file by temporarily soft linking them to the current 'bpy.data'.

        Returns:
            dict: A dict of all the asset object names in the .blend file
        """
        if not os.path.exists(self.blend_filepath):
            warn_msg = f"get_all_assets(), Source .blend file doesn't exist: '{self.blend_filepath}'."
            self.logger.warning(warn_msg)
            return {}
    
        asset_names = {
            "Objects": [],
            "Materials": [],
            "Node Groups": [],
            "Worlds": [],
            "Images": []
        }
        
        # Store original data to clean up later
        original_objects = set(bpy.data.objects)
        original_materials = set(bpy.data.materials)
        original_node_groups = set(bpy.data.node_groups)
        original_worlds = set(bpy.data.worlds)
        original_images = set(bpy.data.images)
        
        try:
            # Soft link all objects from the external .blend file to the current .blend temporarily
            with bpy.data.libraries.load(self.blend_filepath, link=True) as (data_from, data_to):
                # Link objects
                data_to.objects = data_from.objects
                # Link materials
                data_to.materials = data_from.materials
                # Link node groups
                data_to.node_groups = data_from.node_groups
                # Link worlds
                data_to.worlds = data_from.worlds
                # Link images
                data_to.images = data_from.images
            
            # Check for object assets
            for obj in bpy.data.objects:
                if obj not in original_objects and obj.asset_data:
                    asset_names["Objects"].append(obj.name)
            
            # Check for material assets
            for mat in bpy.data.materials:
                if mat not in original_materials and mat.asset_data:
                    asset_names["Materials"].append(mat.name)
            
            # Check for node group assets
            for ng in bpy.data.node_groups:
                if ng not in original_node_groups and ng.asset_data:
                    asset_names["Node Groups"].append(ng.name)
            
            # Check for world assets
            for world in bpy.data.worlds:
                if world not in original_worlds and world.asset_data:
                    asset_names["Worlds"].append(world.name)
            
            # Check for image assets
            for img in bpy.data.images:
                if img not in original_images and img.asset_data:
                    asset_names["Images"].append(img.name)
        
        finally:
            # Clean up: unlink temporary assets to avoid cluttering the current file
            for obj in bpy.data.objects:
                if obj not in original_objects:
                    bpy.data.objects.remove(obj)
            
            for mat in bpy.data.materials:
                if mat not in original_materials:
                    bpy.data.materials.remove(mat)
            
            for ng in bpy.data.node_groups:
                if ng not in original_node_groups:
                    bpy.data.node_groups.remove(ng)
            
            for world in bpy.data.worlds:
                if world not in original_worlds:
                    bpy.data.worlds.remove(world)
            
            for img in bpy.data.images:
                if img not in original_images:
                    bpy.data.images.remove(img)
        

        asset_names_str = json.dumps(asset_names, ensure_ascii=False, indent=2)
        info_msg = f"get_all_asset_names(), following is all the asset names in the '{self.blend_filepath}' .blend file:\n"
        info_msg += asset_names_str
        self.logger.info(info_msg)
        return asset_names



    def load_objects(
            self,
            object_names:list=[]
        ) -> list:
        """
        Load a list of object from the external .blend file to the current 'bpy.data'.

        Args:
            object_names (list): A list of object names.

        Returns:
            list: The list of object instances loaded into the current 'bpy.data'.
        """
        if not os.path.exists(self.blend_filepath):
            warn_msg = f"load_objects(), Source .blend file doesn't exist: '{self.blend_filepath}'."
            self.logger.warning(warn_msg)
            return []
        
        loaded_objects = []  # To store references to loaded objects in current 'bpy.data'
        try:
            # Append (hard copy) specific objects from external .blend to current 'bpy.data'
            with bpy.data.libraries.load(self.blend_filepath, link=False) as (data_from, data_to):

                # Step 1: Filter external object names to match your target list
                # data_from.objects = list of ALL object names in the external file
                filtered_external_names = [obj_name for obj_name in data_from.objects if obj_name in object_names]
                
                # Step 2: Tell Blender to load these filtered objects, to trigger the full loading procedure.
                data_to.objects = filtered_external_names
            
            # Step 3: Collect the loaded objects (data_to.objects now has the instances)
            loaded_objects = data_to.objects

        except Exception as e:
            warn_msg = f"load_objects(), the following exception is thrown "
            warn_msg += f"when doing 'bpy.data.libraries.load()': '{str(e)}'"
            self.logger.warning(warn_msg)


        info_msg = f"load_objects(), load the following objects into 'bpy.data': \n"
        object_names_str = json.dumps(object_names, ensure_ascii=False, indent=2)
        info_msg += object_names_str
        self.logger.info(info_msg)
        return loaded_objects



    def display_objects(
            self,
            object_instances:list=[]
        ):
        """
        Load a list of objects in the Blender's 3D-viewport.

        Args:
            object_instances (list): A list of (mesh) object instances.
        """        
        bpy.context.scene.render.engine = 'CYCLES'

        # Set up the sun. 
        sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
        sun_data.energy = 30.0  # Strength (irradiance in Watts/m²)
        sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
        sun_obj.location = (5, -10.0, 15.0) 
        bpy.context.collection.objects.link(sun_obj)


        # Display the selected objects.
        for idx, obj in enumerate(object_instances):
            if obj.name not in bpy.context.collection.objects:
                bpy.context.collection.objects.link(obj)

            # Locate the object along Y-axis.
            obj.location = (0.0, (idx + 1) * 2.0, 0.0)
            # Ensure the object is not hidden in the viewport
            obj.hide_viewport = False  # Visible in viewport
            obj.hide_select = False    # Allows selection (optional but useful)
            obj.hide_render = False    # Optional: Ensure it's visible in renders too
            
            # Select the object (highlights it in the viewport)
            obj.select_set(True)
        
        # Optional: Set one of the objects as active (for context, e.g., editing)
        # if object_instances:
        #    bpy.context.view_layer.objects.active = object_instances[0]
        
        # Update the viewport to reflect changes (critical for immediate feedback)
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


    @staticmethod
    def usage_demo():
        blend_filepaths = [
            "/home/robot/.config/blender/4.4/scripts/addons/The_Nature_Generator/asset_library/Nature_Generator_Assets.blend",
            "/home/robot/polygoniq_asset_packs/botaniq_full/blends/models/plants/bq_Tree_Citrus-medica_A_spring-summer-autumn.blend" 
        ]
        
        blend_file_handler = BlendFileHandler(blend_filepaths[0])
        asset_dict = blend_file_handler.get_all_asset_names()

        object_names = []
        target_obj_names = ["tree", "flower", "basic_rock"]

        for obj_name in asset_dict["Objects"]:
            if len(target_obj_names) == 0:
                break
            else:
                for target_single_name in target_obj_names:
                    if target_single_name in obj_name.lower():
                        object_names.append(obj_name)
                        target_obj_names.remove(target_single_name)

        object_instances = blend_file_handler.load_objects(object_names)
        blend_file_handler.display_objects(object_instances)
