import bpy
import json


class CinematicCompositor():
    def __init__(self):
        self.node_tree = None 
        self.cinematic_node = None

        try:
            from logger.logger import Logger
            self.logger = Logger("CinematicCompositor").getLogger()

            scene = bpy.context.scene
            if not scene.use_nodes:
                scene.use_nodes = True
            self.node_tree = scene.node_tree

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize CinematicCompositor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize CinematicCompositor class, error message: '{str(e)}'")
        

    def create_cinematic_node(self):
        # Execute the operator that adds the node group to the scene.
        # This single command replicates the "Apply effect" button-click behavior, 
        # referring to ~/.config/blender/4.4/scripts/addons/Cinematic Compositor Addon v2/__init__.py
        if self.cinematic_node and type(self.cinematic_node).__name__ == "CompositorNodeGroup":
            debug_msg = f"create_cinematic_node(), self.cinematic_node already exists, "
            debug_msg += f"no need to execute create_cinematic_node() again."
            self.logger.debug(debug_msg)
            return
        
        try:
            bpy.ops.ccg.add_node_group('INVOKE_DEFAULT')
            debug_msg = "create_cinematic_node(), Successfully executed 'ccg.add_node_group' operator."
            # self.logger.debug(debug_msg)

        except Exception as e:
            warn_msg = f"create_cinematic_node(), Error to run 'bpy.ops.ccg.add_node_group('INVOKE_DEFAULT')', "
            warn_msg += f"Check if the add-on is loaded. The error message is 'str(e)'"
            self.logger.warn(warn_msg)

        # Find the newly added node. The source code reveals it's named "CinematicCompositor",
        # referring to ~/.config/blender/4.4/scripts/addons/Cinematic Compositor Addon v2/__init__.py
        try:
            self.cinematic_node = self.node_tree.nodes.get("CinematicCompositor")
            
            if self.cinematic_node:
                self.cinematic_node.location.x = 200
                self.cinematic_node.location.y = 300

                info_msg = f"create_cinematic_node(), cinematic node is registered in the scene.node_tree, and it is enabled."
                self.logger.info(info_msg)
            else:
                warn_msg = f"create_cinematic_node(), the 'CinematicCompositor' node was not found in the scene.node_tree."
                self.logger.warn(warn_msg)
                
        except Exception as e:
            warn_msg = f"create_cinematic_node(), an unexpected error occurred while finding the cinematic node,"
            warn_msg += f"the error message is: {str(e)}"
            self.logger.warn(warn_msg)


    def cinematic_mystery(self):
        """
        Make the color tone as green-grey, a feeling of mystery or depressed.
        """
        # 1. Set the cinematic node's attributes.
        self.logger.debug(f"len(self.cinematic_node.inputs) = {len(self.cinematic_node.inputs)}")

        self.cinematic_node.inputs[2].default_value = 0.5    # Teal & Orange
        self.cinematic_node.inputs[3].default_value = 0.0      # Golden Look
        self.cinematic_node.inputs[4].default_value = 0.0      # B&W Effect
        self.cinematic_node.inputs[5].default_value = (1.0, 0.0, 0.0, 1.0)     # Color Focus
        self.cinematic_node.inputs[6].default_value = 1.0    # Color Focus Factor
        self.cinematic_node.inputs[7].default_value = (0.0, 1.0, 1.0, 1.0)   # Tint color
        self.cinematic_node.inputs[8].default_value = 1.0     # Tint color Factor
        self.cinematic_node.inputs[9].default_value = 1.0     # Overall Film Emulation
        self.cinematic_node.inputs[10].default_value = 1.0     # Film Emulation Constract
        self.cinematic_node.inputs[11].default_value = 0.2     # Film Emulation Halation
        self.cinematic_node.inputs[12].default_value = 1.0     # Film Emulation Bloom
        self.cinematic_node.inputs[13].default_value = 0.1     # Film Emulation Soft Highlights
        self.cinematic_node.inputs[14].default_value = 0.1     # Film Emulation Sharpness
        self.cinematic_node.inputs[15].default_value = 200     # Lens Flare Threshold
        self.cinematic_node.inputs[16].default_value = 1.0     # Lens Flare Strength
        # self.cinematic_node.inputs[17].default_value = None     # Custom Mask
        self.cinematic_node.inputs[18].default_value = 0.0     # Use Custom Mask Only
        self.cinematic_node.inputs[19].default_value = 0.0     # Glare Strength
        self.cinematic_node.inputs[20].default_value = (0.2, 0.4, 1.0, 1.0)     # Anamorphic Glare Tint Color
        self.cinematic_node.inputs[21].default_value = 1.0     # Anamorphic Glare Tint Strength
        self.cinematic_node.inputs[22].default_value = (0.0, 1.0, 0.0, 1.0)     # Mirrors Tint Color
        self.cinematic_node.inputs[23].default_value = 1.0     # Mirrors Tint Strength
        self.cinematic_node.inputs[24].default_value = (0.0, 0.0, 0.1, 1.0)     # Antiglare Tint Color
        self.cinematic_node.inputs[25].default_value = 1.0     # Antiglare Tint Strength
        self.cinematic_node.inputs[26].default_value = 1.0     # Circles Strength
        self.cinematic_node.inputs[27].default_value = 0.3     # Haze Strength
        self.cinematic_node.inputs[28].default_value = 0.5     # Lens Distortion
        self.cinematic_node.inputs[29].default_value = 1.0     # Chromatic Aberration
        self.cinematic_node.inputs[30].default_value = 1.0     # Vignette Strength
        self.cinematic_node.inputs[31].default_value = 1.0     # Film Grain Factor
        self.cinematic_node.inputs[32].default_value = 0.0     # Overlays Strength
        self.cinematic_node.inputs[33].default_value = 1.0     # Overlays Scratches
        self.cinematic_node.inputs[34].default_value = 1.0     # Overlays Stains
        self.cinematic_node.inputs[35].default_value = 1.0     # Overlays Fingerprints
        # self.cinematic_node.inputs[36].default_value = None     # Custom Texture
        self.cinematic_node.inputs[37].default_value = 1.0     # Custom Texture Opacity
        self.cinematic_node.inputs[38].default_value = 0.0     # Black Bars Factor


        # 2. Return a dict containing in_node object and in_node socket for upstream,
        #    and out_node object and out_node socket for downstream.
        in_out = {
            "in_node": self.cinematic_node,
            "in_socket": [0, 1],  # Image/Alpha input socket ids
            "out_node": self.cinematic_node, 
            "out_socket": [0, 1]  # Image/Alpha output socket ids
        }
        return in_out

