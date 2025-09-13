import bpy
import json


class CinematicCompositor():
    def __init__(self):
        self.node_tree = None 
        self.cinematic_node = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("CinematicCompositor").getLogger()

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
            self.logger.debug(debug_msg)

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
        # 1. Create the cinematic node.
        self.create_cinematic_node()

        # 2. Set the cinematic node's attributes.
        self.cinematic_node.inputs[6].default_value = 1
        # self.cinematic_node.inputs[7].default_value = (0.00264851, 0.00906155, 1, 1)
        self.cinematic_node.inputs[8].default_value = 0.663158

        # 3. Return a dict containing in_node object and in_node socket for upstream,
        #    and out_node object and out_node socket for downstream.
        in_out = {
            "in_node": self.cinematic_node,
            "in_socket": 0,  # Image input socket name
            "out_node": self.cinematic_node, 
            "out_socket": 0  # Image output socket name
        }
        return in_out

