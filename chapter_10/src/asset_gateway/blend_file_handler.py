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


    # bpy.data.objects
    def get_objects(
            self,
            object_names:list=[]
        ) -> list:
        """
        Find the object instances from 'bpy.data.objects' given their names.

        Args:
            object_names (list): A list of object names.

        Returns:
            list: The list of object instances in 'bpy.data.objects'.
        """
        object_names_lower = [s.lower() if isinstance(s, str) else s for s in object_names]
        try:
            object_instances = []
            for obj_instance in bpy.data.objects:
                if obj_instance.name.lower() in object_names_lower:
                    object_instances.append(obj_instance)

            info_msg = f"get_objects(), given object names: '{object_names}', "
            info_msg += f"find these objects in 'bpy.data.objects': \n"
            object_instances_names = [obj.name for obj in object_instances]
            info_msg += f"\t{object_instances_names}"
            self.logger.info(info_msg)

            # Make the objects visible in the current view layer
            for obj_instance in object_instances:
                if obj_instance.name not in bpy.context.collection.objects:
                    bpy.context.collection.objects.link(obj_instance) 

            return object_instances
        except Exception as e:
            warn_msg = f"get_objects(), the following exception is thrown "
            warn_msg += f"when get '{object_names}' from 'bpy.data.objects': '{str(e)}'"
            self.logger.warning(warn_msg)


    def get_materials(
            self, 
            object_instance: object=None
        ) -> list:
        """
        Given a mesh object instance, get the names of the material that this object used. 
        
        Returns:
            list: The list of the material names.
        """
        material_name_list = []
        
        try:
            if object_instance.data and object_instance.data.materials:
                material_name_list = [m.name for m in object_instance.data.materials]

                material_name_list_str = json.dumps(material_name_list, ensure_ascii=False, indent=2)
                info_msg = f"get_materials(), '{object_instance.name}' attached Materials: '{material_name_list_str}'."
                self.logger.info(info_msg)

            else:
                info_msg = f"get_materials(), '{object_instance.name}' doesn't have any attached Materials."
                self.logger.info(info_msg)

        except Exception as e:
            warn_msg = f"get_materials(), an exception was thrown when getting the attached materials \n"
            warn_msg += f"of an object instance '{object_instance.name}': '{str(e)}'."
            self.logger.warning(warn_msg)
        
        return material_name_list



    def load_modifiers(
            self,
            object_instance: object=None,
            modifier_names:list=[]
        ) -> list:
        """
        Load a list of modifiers from the external .blend file to the current 'bpy.data.node_groups'.

        Args:
            modifier_names (list): A list of modifier names.

        Returns:
            list: The list of modifier instances loaded into the current 'bpy.data.node_groups'.
        """
        if not os.path.exists(self.blend_filepath):
            warn_msg = f"load_modifiers(), Source .blend file doesn't exist: '{self.blend_filepath}'."
            self.logger.warning(warn_msg)
            return []
        
        loaded_node_groups = []  # To store references to loaded modifiers in current 'bpy.data.node_groups'
        try:
            # Append (hard copy) specific modifiers from external .blend to current 'bpy.data.node_groups'
            with bpy.data.libraries.load(self.blend_filepath, link=False) as (data_from, data_to):

                # Step 1: Filter external modifier names to match the target list
                filtered_external_names = [mod_name for mod_name in data_from.node_groups if mod_name in modifier_names]
                
                # Step 2: Tell Blender to load these filtered modifiers, to trigger the full loading procedure.
                data_to.node_groups = filtered_external_names
            
            # Step 3: Collect the loaded objects (data_to.objects now has the instances)
            loaded_node_groups = data_to.node_groups

        except Exception as e:
            warn_msg = f"load_modifiers(), the following exception is thrown "
            warn_msg += f"when doing 'bpy.data.:libraries.load()': '{str(e)}'"
            self.logger.warning(warn_msg)

        modifier_list = []
        try:
            # Add a modifier for each imported Node Group
            for idx, node_group in enumerate(loaded_node_groups):
                mod_name = f"Llamedia_{node_group.name}"  
                # modifier = object_instance.modifiers.new(name=mod_name, type='GEOMETRY_NODES')
                modifier = object_instance.modifiers.new(name=mod_name, type='NODES')
                modifier.node_group = node_group  
                modifier_list.append(modifier)

                info_msg = f"load_modifiers(), create a new modifier '{mod_name}', "
                info_msg += f"and link '{node_group.name}' to it."
                self.logger.info(info_msg)

        except Exception as e:
            warn_msg = f"load_modifiers(), the following exception is thrown "
            warn_msg += f"when creating a new modifier and link '{node_group.name}' to it: '{str(e)}'"
            self.logger.warning(warn_msg)
            return []

        return modifier_list
          

    def get_modifiers(
            self, 
            object_instance: object=None
        ) -> list:
        """
        Given a mesh object instance, get the names of the modifiers of this object's geometry node groups. 
        
        Returns:
            list: The list of the names of the modifiers of this object's geometry node groups.
        """
        modifier_list = []

        try:
            if object_instance.modifiers:
                for idx, item in enumerate(object_instance.modifiers):
                    modifier_list.append(item.name)

                modifier_list_str = json.dumps(modifier_list, ensure_ascii=False, indent=2)
                info_msg = f"get_modifiers(), '{object_instance.name}' attached geometry node modifier: '{modifier_list_str}'."
                self.logger.info(info_msg)

            else:
                info_msg = f"get_modifiers(), '{object_instance.name}' doesn't have any attached geometry node modifier."
                self.logger.info(info_msg)

        except Exception as e:
            warn_msg = f"get_modifiers(), an exception was thrown when getting the attached geometry node modifier \n"
            warn_msg += f"of an object instance '{object_instance.name}': '{str(e)}'."
            self.logger.warning(warn_msg)

        return modifier_list
    

    def set_material_properties(
            self, 
            object_instance: object=None,
            material_name: str="",
            node_name: str="",
            node_attributes: dict={}
        ):
        if object_instance is None:
            warn_msg = f"set_material_properties(), 'object_instance' is None."
            self.logger.warning(warn_msg)
            return 
        
        # 1. Find the material object
        target_materials = []
        target_material_names = []
        try:
            # if object_instance.data and object_instance.data.materials:
            for idx, material_obj in enumerate(object_instance.data.materials):
                # self.logger.debug(f" material[{idx}] '{material_obj.name}'")

                if material_name.lower() in material_obj.name.lower():
                    target_materials.append(material_obj)
                    target_material_names.append(material_obj.name)
            
            info_msg = f"set_material_properties(), given 'material_name'=='{material_name}', "
            info_msg += f"find these 'target_materials'=='{target_material_names}'."
            self.logger.info(info_msg)
        except Exception as e:
            warn_msg = f"set_material_properties(), the following exception was thrown "
            warn_msg += f"when getting the materials of the mesh object '{object_instance.name}': '{str(e)}'"
            self.logger.warning(warn_msg)
            return
        
        for idx, target_material in enumerate(target_materials):
            # 2. Find the shader node object
            target_node = None
            try:
                for idx, node in enumerate(target_material.node_tree.nodes):
                    # self.logger.debug(f"get_node(), [{idx}] node.name=='{node.name}'")
                    if node_name.lower() in node.name.lower():
                        target_node = node
                        break

                info_msg = f"set_material_properties(), given 'node_name'=='{node_name}', "
                info_msg += f"find the 'target_node'=='{target_node.name}'."
                self.logger.info(info_msg)
            except Exception as e:
                warn_msg = f"set_material_properties(), the following exception was thrown "
                warn_msg += f"when getting the shader nodes of the material '{material_name}': '{str(e)}'"
                self.logger.warning(warn_msg)
                return

            # 3. Set the attribute values
            info_msg = f"set_material_properties(), set attributes to shader node '{target_node.name}'."
            try:
                for attr_name, attr_value in node_attributes.items():
                    target_node.inputs[attr_name].default_value = attr_value
                    info_msg += f"\n\t attribute '{attr_name}' = value '{attr_value}' "

            except Exception as e:
                warn_msg = f"set_material_properties(), the following exception was thrown "
                warn_msg += f"when setting the attributes of a shader nodes '{target_node.name}': '{str(e)}'"
                self.logger.warning(warn_msg)
                return
            self.logger.info(info_msg)


    def set_modifier_properties(
            self, 
            object_instance: object=None,
            modifier_name: str="",
            node_name: str="",
            node_attributes: dict={}
        ):
        if object_instance is None:
            warn_msg = f"set_modifier_properties(), 'object_instance' is None."
            self.logger.warning(warn_msg)
            return 

        # 1. Find the modifier object
        target_modifiers = []
        target_modifier_names = []
        try:
            for idx, modifier_obj in enumerate(object_instance.modifiers):
                self.logger.debug(f" modifier[{idx}] '{modifier_obj.name}'")

                if modifier_name.lower() in modifier_obj.name.lower():
                    target_modifiers.append(modifier_obj)
                    target_modifier_names.append(modifier_obj.name)
            
            info_msg = f"set_modifier_properties(), given 'modifier_name'=='{modifier_name}', "
            info_msg += f"find these 'target_modifiers'=='{target_modifier_names}'."
            self.logger.info(info_msg)
        except Exception as e:
            warn_msg = f"set_modifier_properties(), the following exception was thrown "
            warn_msg += f"when getting the materials of the mesh object '{object_instance.name}': '{str(e)}'"
            self.logger.warning(warn_msg)
            return

        for idx, target_modifier in enumerate(target_modifiers):
            # 2. In case the node_name is not given, try to set attributes directly. 
            if len(node_name) == 0:
                info_msg = f"set_modifier_properties(), set attributes to modifier '{target_modifier.name}', "
                info_msg += f"without accessing its internal nodes."
                try:
                    for attr_name, attr_value in node_attributes.items():
                        target_modifier[attr_name] = attr_value
                        info_msg += f"\n\t attribute '{attr_name}' = value '{attr_value}' "
                except Exception as e:
                    warn_msg = f"set_modifier_properties(), the following exception was thrown "
                    warn_msg += f"when setting the attributes to the modifier '{target_node.name}' "
                    warn_msg += f"without accessing its internal nodes: '{str(e)}'"
                    self.logger.warning(warn_msg)
                    return
                self.logger.info(info_msg)

            # 3.1 Find the modifier node first, then set its attributes
            target_node = None
            try:
                for idx, node in enumerate(target_modifier.node_tree.nodes):
                    # self.logger.debug(f"get_node(), [{idx}] node.name=='{node.name}'")
                    if node_name.lower() in node.name.lower():
                        target_node = node
                        break

                info_msg = f"set_modifier_properties(), given 'node_name'=='{node_name}', "
                info_msg += f"find the 'target_node'=='{target_node.name}'."
                self.logger.info(info_msg)
            except Exception as e:
                warn_msg = f"set_modifier_properties(), the following exception was thrown "
                warn_msg += f"when getting the node '{node_name}' of the modifier '{modifier_name}': '{str(e)}'"
                self.logger.warning(warn_msg)
                return

            # 3.2 Set the node's attribute values
            info_msg = f"set_modifier_properties(), set attributes to modifier node '{target_node.name}'."
            try:
                for attr_name, attr_value in node_attributes.items():
                    target_node.inputs[attr_name].default_value = attr_value
                    info_msg += f"\n\t attribute '{attr_name}' = value '{attr_value}' "

            except Exception as e:
                warn_msg = f"set_modifier_properties(), the following exception was thrown "
                warn_msg += f"when setting the attributes of a modifier nodes '{target_node.name}': '{str(e)}'"
                self.logger.warning(warn_msg)
                return
            self.logger.info(info_msg)



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

