import bpy
import json


class ColorCompositor():
    def __init__(self):
        self.node_tree = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("ColorCompositor").getLogger()

            scene = bpy.context.scene
            scene.use_nodes = True
            self.node_tree = scene.node_tree

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize ColorCompositor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize ColorCompositor class, error message: '{str(e)}'")


    def adjust_color(
            self, 
            bright_contrast=(0.1, 0.2), 
            hue_saturation_value=(0.1, 1.2, 1.0),
            color_balance=[(1, 1, 1), (1.02, 1.02, 1.02), (0.8, 0.8, 0.8)],
            rgb_to_bw=False
        ):
        """
        Adjust color for the input image.
        """
        # --------------------------
        # 1. Set Brightness/Contrast
        # --------------------------
        bright_contrast_node = self.node_tree.nodes.new(type='CompositorNodeBrightContrast')
        bright_contrast_node.location = (-600, 0)
        bright_contrast_node.name = "BrightnessContrast"

        bright_contrast_node.inputs['Bright'].default_value = bright_contrast[0]  # 0.1, Slight brightness boost
        bright_contrast_node.inputs['Contrast'].default_value = bright_contrast[1]  # 0.2, Increase contrast

        # --------------------------
        # 2. Set Hue/Saturation Node
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
        # 6. Return a dict containing in_node object and in_node socket for upstream,
        #    and out_node object and out_node socket for downstream.
        # --------------------------
        in_out = {
            "in_node": bright_contrast_node,
            "in_socket": 0,  # Image input socket name
            "out_node": color_balance_node if rgb_to_bw is False else rgb_to_bw_node, 
            "out_socket": 0  # Image output socket name
        }
        return in_out        


    def denoise(self):
        """
        Denoise the given image, usefully for rendering high definition image.
        """
        denoise_node = self.node_tree.nodes.new(type='CompositorNodeDenoise')
        denoise_node.location = (0, 0)
        denoise_node.name = "Denoise"

        # Return a dict containing in_node object and in_node socket for upstream,
        # and out_node object and out_node socket for downstream.
        in_out = {
            "in_node": denoise_node,
            "in_socket": 0,  # Image input socket name
            "out_node": denoise_node, 
            "out_socket": 0  # Image output socket name
        }
        return in_out


    def blur(
            self, 
            blur_factor=(10, 20)   # Blurring percentage along X and Y axes.
        ):
        """
        Blur the given image.
        """
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
