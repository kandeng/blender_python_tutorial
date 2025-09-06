import os
import random
import json
import bpy


class Compositor:
    def __init__(self):
        self.logger = None
        self.node_tree = None
        self.camera = None

        self.base_node_names = []

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("Compositor").getLogger()

            from editor.editor_node import EditorNode
            self.editor_node = EditorNode(editor_name="Compositor", editor_type="COMPOSITING")
            self.node_tree = self.editor_node.node_tree

            from camera.camera import Camera
            self.camera = Camera("CompositorCamera")

            self._create_base_nodes()
            self.logger.info(f"Compositor class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Compositor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize Compositor class, error message: '{str(e)}'")


    def _create_base_nodes(self):   
        # 1. Image node (input image)
        image_node = self.node_tree.nodes.new(type='CompositorNodeImage')
        image_node.location = (-1000, -300)
        image_node.name = "Compositor_InputImage"
        self.base_node_names.append(image_node.name)

        # 2. Render Layers node (as requested, even if we use an image)
        render_layers = self.node_tree.nodes.new(type='CompositorNodeRLayers')
        render_layers.location = (-1000, 0)
        render_layers.name = "Compositor_RenderLayers"
        self.base_node_names.append(render_layers.name)
   
        # 3. Mix node (blend image with noise)
        mix_node = self.node_tree.nodes.new(type='CompositorNodeMixRGB')
        mix_node.location = (0, -300)
        mix_node.name = "Compositor_MixRGB"
        self.base_node_names.append(mix_node.name)

        mix_node.blend_type = 'MULTIPLY'  # Darkens image where noise is present
        mix_node.inputs['Fac'].default_value = 0.3  # Noise strength (30%)
        
        # 4. Composite node (final output)
        composite_node = self.node_tree.nodes.new(type='CompositorNodeComposite')
        composite_node.location = (300, 300)
        composite_node.name = "Compositor_Composite"
        self.base_node_names.append(composite_node.name)
        
        # 5. Viewer node (preview)
        viewer_node = self.node_tree.nodes.new(type='CompositorNodeViewer')
        viewer_node.location = (300, -300)
        viewer_node.name = "Compositor_Viewer"
        self.base_node_names.append(viewer_node.name)


    def remove_nonbase_nodes(self):
        try:
            # Clear default nodes
            for node in self.node_tree.nodes:
                if node.name not in self.base_node_names:
                    self.node_tree.nodes.remove(node)
            
            info_msg = f"remove_nonbase_nodes(), Remove all the compositing nodes except the base nodes."
            self.logger.info(info_msg)

        except Exception as e:
            warn_msg = f"Could not reset Compositor class, "
            warn_msg += f"error message: '{str(e)}'."
            self.logger.warn(warn_msg)


    def load_image(
            self, 
            single_image_filename=""
        ):
        if not os.path.exists(single_image_filename):
            warn_msg = f"load_image(), Input image not found: {single_image_filename}."
            self.logger.warn(warn_msg)
            return
    
        input_image = bpy.data.images.load(single_image_filename)
        image_node = self.editor_node.get_node("Compositor_InputImage")
        image_node.image = input_image
  

    def image_processing_decorator(func):
        """
        A decorator function for all image processing functions.
        """
        def wrapper(self, *args, **kwargs):
            # 1. Clear up the useless compositing nodes.
            self.remove_nonbase_nodes()

            # 2. Load the input image to the InputImage node.
            input_image = kwargs.get("input_image_filename", "")
            self.load_image(single_image_filename=input_image)

            # 3. Call the func with its parameters.
            in_out = func(self, *args, **kwargs)
            in_node = in_out["in_node"]
            in_socket = in_out["in_socket"]
            out_node = in_out["out_node"]
            out_socket = in_out["out_socket"]

            # 4. Get the base nodes.
            image_node = self.editor_node.get_node("Compositor_InputImage")
            composite_node = self.editor_node.get_node("Compositor_Composite")
            viewer_node = self.editor_node.get_node("Compositor_Viewer")

            # 5. Link nodes together
            links = self.node_tree.links
            links.new(image_node.outputs['Image'], in_node.inputs[in_socket])

            links.new(out_node.outputs[out_socket], composite_node.inputs['Image'])
            links.new(out_node.outputs[out_socket], viewer_node.inputs['Image'])

            # 6. Render the scene into an image.
            output_image = kwargs.get("output_image_filename", "")
            self.camera.renderer.set_image_settings(      
                engine='CYCLES', 
                resolution_x=640, 
                resolution_y=360, 
                samples=32
            )
            self.camera.renderer.render_single_images(
                image_output_filename=output_image
            )

        # Return the wrapper function
        return wrapper


    @image_processing_decorator
    def denoise(
            self, 
            input_image_filename="",
            output_image_filename=""
        ):
        """
        Denoise the given image, usefully for rendering high definition image.

        Args:
            input_image_filename (str): The input file directory and name.
            output_image_filename (str): The output file directory and name.
        """
        # 1. Denoise node
        denoise_node = self.node_tree.nodes.new(type='CompositorNodeDenoise')
        denoise_node.location = (0, 0)
        denoise_node.name = "Denoise"

        # 2. Return a dict containing in_node object and in_node socket for upstream,
        #    and out_node object and out_node socket for downstream.
        in_out = {
            "in_node": denoise_node,
            "in_socket": 0,  # Image input socket name
            "out_node": denoise_node, 
            "out_socket": 0  # Image output socket name
        }
        return in_out


    @image_processing_decorator
    def blur(
            self, 
            input_image_filename="",
            output_image_filename="",
            blur_factor=(10, 20)   # Blurring percentage along X and Y axes.
        ):
        """
        Blur he given image.

        Args:
            input_image_filename (str): The input file directory and name.
            output_image_filename (str): The output file directory and name.
        """
        # 1. Create the blur node and set its attributes.
        blur_node = self.node_tree.nodes.new(type='CompositorNodeBlur')
        blur_node.location = (0, 0)
        blur_node.name = "Blur"

        blur_node.use_gamma_correction = True
        blur_node.use_relative = True
        blur_node.use_bokeh = True
        blur_node.use_variable_size = True
        blur_node.filter_type = 'FLAT'  # Valid values are ('FLAT', 'GAUSS', 'MITCH'..)
        blur_node.aspect_correction = 'NONE'   # Valid values are ('X', 'Y', 'NONE')
        blur_node.factor_x = blur_factor[0]
        blur_node.factor_y = blur_factor[1]

        # 2. Return a dict containing in_node object and in_node socket for upstream,
        #    and out_node object and out_node socket for downstream.
        in_out = {
            "in_node": blur_node,
            "in_socket": 0,  # Image input socket name
            "out_node": blur_node, 
            "out_socket": 0  # Image output socket name
        }
        return in_out


    @image_processing_decorator
    def adjust_color(
            self, 
            input_image_filename="",
            output_image_filename="", 
            bright_contrast=(0.1, 0.2), 
            hue_saturation_value=(0.1, 1.2, 1.0),
            color_balance=[(1, 1, 1), (1.02, 1.02, 1.02), (0.8, 0.8, 0.8)],
            rgb_to_bw=False
        ):
        """
        Adjust color for the input image.

        Args:
            input_image_filename (str): The input file directory and name.
            output_image_filename (str): The output file directory and name.
        """

        # --------------------------
        # 1. Brightness/Contrast Node
        # --------------------------
        bright_contrast_node = self.node_tree.nodes.new(type='CompositorNodeBrightContrast')
        bright_contrast_node.location = (-600, 0)
        bright_contrast_node.name = "BrightnessContrast"

        bright_contrast_node.inputs['Bright'].default_value = bright_contrast[0]  # 0.1, Slight brightness boost
        bright_contrast_node.inputs['Contrast'].default_value = bright_contrast[1]  # 0.2, Increase contrast

        # --------------------------
        # 2. Hue/Saturation Node
        # --------------------------
        hue_sat_node = self.node_tree.nodes.new(type='CompositorNodeHueSat')
        hue_sat_node.location = (-600, 300)
        hue_sat_node.name = "HueSaturationValue"

        hue_sat_node.inputs['Hue'].default_value = hue_saturation_value[0]    # 0.1, Slight color shift
        hue_sat_node.inputs['Saturation'].default_value = hue_saturation_value[1]   # 1.2, More vibrant colors
        hue_sat_node.inputs['Value'].default_value = hue_saturation_value[2]    # 1.0, No value change        

        # --------------------------
        # 3. Color Balance Node
        # --------------------------
        color_balance_node = self.node_tree.nodes.new(type='CompositorNodeColorBalance')
        color_balance_node.location = (-300, 0)
        color_balance_node.name = "ColorBalance"

        color_balance_node.lift = color_balance[0]
        color_balance_node.gamma = color_balance[1]
        color_balance_node.gain = color_balance[2]

        # --------------------------
        # 4. Color Balance Node
        # --------------------------
        rgb_to_bw_node = self.node_tree.nodes.new(type='CompositorNodeRGBToBW')
        rgb_to_bw_node.location = (0, 300)
        rgb_to_bw_node.name="RGBtoBW"


        # --------------------------
        # 5. Link All Nodes Together
        # --------------------------
        links = self.node_tree.links
        links.new(bright_contrast_node.outputs['Image'], hue_sat_node.inputs['Image'])
        links.new(hue_sat_node.outputs['Image'], color_balance_node.inputs['Image'])

        if rgb_to_bw is True:
            links.new(color_balance_node.outputs[0], rgb_to_bw_node.inputs[0])
    
        # --------------------------
        # 5. Return a dict containing in_node object and in_node socket for upstream,
        #    and out_node object and out_node socket for downstream.
        # --------------------------
        in_out = {
            "in_node": bright_contrast_node,
            "in_socket": 0,  # Image input socket name
            "out_node": color_balance_node if rgb_to_bw is False else rgb_to_bw_node, 
            "out_socket": 0  # Image output socket name
        }
        return in_out        


    @staticmethod
    def run_demo():
        image_compositor = Compositor()
        base_node_names = image_compositor.base_node_names 
        base_node_names_str = json.dumps(base_node_names, indent=2, ensure_ascii=False)
        image_compositor.logger.debug(f"Base nodes: \n\t{base_node_names_str}")

        input_image = "/home/robot/movie_blender_studio/input/balloons_noisy.png"
        input_image = "/home/robot/movie_blender_studio/input/battle_field.png"
        output_image= "/home/robot/movie_blender_studio/output/composition_image.png"
        
        """
        image_compositor.denoise(
            input_image_filename=input_image
        )
        image_compositor.adjust_color(
            input_image_filename=input_image,
            output_image_filename="", 
            bright_contrast=(0.1, 0.2), 
            hue_saturation_value=(0.1, 1.2, 1.0),
            color_balance=[(0.9, 1, 1.1), (0.99, 1.0, 1.01), (0.79, 0.8, 0.81)]
        )        
        """
        image_compositor.blur(
            input_image_filename=input_image,
            output_image_filename=output_image,
            blur_factor=(1, 2) 
        )



if __name__ == "__main__":
    Compositor.run_demo()