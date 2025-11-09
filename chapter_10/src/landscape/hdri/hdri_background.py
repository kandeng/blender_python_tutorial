import bpy
import os

class HdriBackground:
    """
    A class to set up background using HDRI image.
    
    Args:
        hdri_filename (str): The file directory and file name of the HDRI image.
    """
    def __init__(self, hdri_filename=""):
        self.logger = None
        self.hdri_filename = hdri_filename

        try:
            from logger.logger import Logger
            self.logger = Logger("HDRi").getLogger()
            info_msg = f"Create a HdriBackground object to setup background"
            info_msg += f", using HDRI image '{self.hdri_filename}'." if len(self.hdri_filename) > 0 else f"."
            self.logger.info(info_msg)

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize HdriBackground class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize HdriBackground class, error message: '{str(e)}'")
 

    def setup_hdri_background(
            self, 
            hdri_filename="",
            light_strength=1.0
        ):
        """
        Set an HDRI image as the scene background and environment light.
        
        Args:
            hdri_filename: Full path to the HDRI image (e.g., .hdr or .exr)
        """
        # Check if the file exists
        if len(hdri_filename) > 0:
            self.hdri_filename = hdri_filename
        if not os.path.exists(self.hdri_filename):
            warn_msg = f"HDRI file not found: '{hdri_filename}'."
            self.logger.warn(warn_msg)
            return
        
        # Get the world environment
        world = bpy.context.scene.world
        if not world:
            # Create a new world if none exists
            world = bpy.data.worlds.new(name="HDRI_World")
            bpy.context.scene.world = world
        
        # Enable nodes for the world shader
        world.use_nodes = True
        tree = world.node_tree
        nodes = tree.nodes
        links = tree.links
        
        # Clear default nodes
        for node in nodes:
            nodes.remove(node)
        
        # Create necessary nodes
        env_tex_node = nodes.new(type='ShaderNodeTexEnvironment')  # Environment texture node
        bg_node = nodes.new(type='ShaderNodeBackground')           # Background shader node
        output_node = nodes.new(type='ShaderNodeOutputWorld')      # World output node
        
        # Position nodes for visibility (optional, but helps in the UI)
        env_tex_node.location = (-300, 0)
        bg_node.location = (0, 0)
        output_node.location = (300, 0)
        
        # Load the HDRI image
        env_tex_node.image = bpy.data.images.load(self.hdri_filename)
        
        # Link the nodes
        links.new(env_tex_node.outputs['Color'], bg_node.inputs['Color'])
        links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])
        
        # Optional: Adjust background strength (lower = darker)
        bg_node.inputs['Strength'].default_value = light_strength
        
        info_msg = f"HDRI background set successfully from: '{self.hdri_filename}',"
        info_msg += f"with light strength={light_strength}"
        self.logger.info(info_msg)



    # --------------------------
    # Example Usage
    # --------------------------
    @staticmethod
    def run_demo():
        # Replace this with the path to your HDRI file (.hdr or .exr)
        hdri_filename = "/home/robot/movie_blender_studio/asset/hdri/kloppenheim_06_4k.exr"  
        
        try:
            hdri_background = HdriBackground(hdri_filename)
            hdri_background.setup_hdri_background(light_strength=2.5)

            # It's good practice to start with a clean scene for a demo.
            bpy.ops.object.select_all(action='SELECT')
            if bpy.context.active_object: bpy.ops.object.delete()

            # Create a ground plane for context.
            bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
            
            # Optional: Configure render settings for better HDRI results
            scene = bpy.context.scene
            
            # Use Cycles for realistic lighting (HDRI works with Eevee too)
            scene.render.engine = 'CYCLES'
            
            # For Eevee, enable environment mapping
            # scene.render.engine = 'BLENDER_EEVEE'
            # scene.eevee.use_environment_mapping = True
            
            print("HDRI setup complete. Render to see the result!")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    HdriBackground.run_demo()