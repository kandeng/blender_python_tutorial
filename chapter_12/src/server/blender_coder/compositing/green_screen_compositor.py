import bpy
import os
import json

class GreenScreenCompositor():
    def __init__(self):
        self.scene = None 
        self.compositor_nodes = {}

        self.scene_settings_filename = "scene_settings.json"
        self.scene_settings = {}

        self.image_sequence_strip = None

        try:
            from logger.logger import Logger
            self.logger = Logger("GreenScreenCompositor").getLogger()

            from video.image_sequence_strip import ImageSequenceStrip
            self.image_sequence_strip = ImageSequenceStrip()

            self.scene = bpy.context.scene
            self.scene.use_nodes = True

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize GreenScreenCompositor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize GreenScreenCompositor class, error message: '{str(e)}'")
        

    def create_greenscreen_node(self):
        """
        Referring to https://www.youtube.com/watch?v=KBBkgoDPnZE
        """
        #---------------------------------------------
        # 1. Create the compositor nodes.
        #---------------------------------------------

        # 1. Clear existing nodes (optional)
        for node in self.scene.node_tree.nodes:
            self.scene.node_tree.nodes.remove(node)
            self.compositor_nodes = {}

        # 2. Image input node, not only for one single image, but also for image sequence.
        image_nodename = "Compositor_Image"
        image_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeImage'
        )
        image_node.name=image_nodename
        image_node.location = (-600, 200)
        if image_nodename not in self.compositor_nodes:
            self.compositor_nodes[image_nodename] = image_node

        # 3. Composite node (final output)
        composite_nodename = "Compositor_Composite"
        composite_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeComposite'
        )
        composite_node.name=composite_nodename
        composite_node.location = (1000, 300)
        if composite_nodename not in self.compositor_nodes:
            self.compositor_nodes[composite_nodename] = composite_node
        
        # 4. Viewer node (preview)
        viewer_nodename = "Compositor_Viewer"
        viewer_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeViewer'
        )
        viewer_node.name=viewer_nodename
        viewer_node.location = (1000, -300)
        if viewer_nodename not in self.compositor_nodes:
            self.compositor_nodes[viewer_nodename] = viewer_node

        # 5. Keying node 
        keying_nodename = "Compositor_Keying"
        keying_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeKeying'
        )
        keying_node.name=keying_nodename
        keying_node.location = (0, 200)
        if keying_nodename not in self.compositor_nodes:
            self.compositor_nodes[keying_nodename] = keying_node

        # 6. Alpha over node
        alphaover_nodename = "Compositor_AlphaOver"
        alphaover_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeAlphaOver'
        )
        alphaover_node.name=alphaover_nodename
        alphaover_node.location = (700, 0)
        if alphaover_nodename not in self.compositor_nodes:
            self.compositor_nodes[alphaover_nodename] = alphaover_node

        # 7. Box mask node
        boxmask_nodename = "Compositor_BoxMask"
        boxmask_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeBoxMask'
        )
        boxmask_node.name=boxmask_nodename
        boxmask_node.location = (-600, -200)
        if boxmask_nodename not in self.compositor_nodes:
            self.compositor_nodes[boxmask_nodename] = boxmask_node

        # 8. Invert node
        invert_nodename = "Compositor_Invert"
        invert_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeInvert'    
        )
        invert_node.name=invert_nodename
        invert_node.location = (-300, -200)
        if invert_nodename not in self.compositor_nodes:
            self.compositor_nodes[invert_nodename] = invert_node

        # 9. Color ramp node
        color_ramp_nodename = "Compositor_ColorRamp"
        color_ramp_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeValToRGB'
        )
        color_ramp_node.name=color_ramp_nodename
        color_ramp_node.location = (300, 200)
        if color_ramp_nodename not in self.compositor_nodes:
            self.compositor_nodes[color_ramp_nodename] = color_ramp_node

        # 10. Hue correct node
        hue_correct_nodename = "Compositor_HueCorrect"
        hue_correct_node = self.scene.node_tree.nodes.new(
            type='CompositorNodeHueCorrect'      # type='CompositorNodeCurveRGB'
        )
        hue_correct_node.name=hue_correct_nodename
        hue_correct_node.location = (300, -200)
        if hue_correct_nodename not in self.compositor_nodes:
            self.compositor_nodes[hue_correct_nodename] = hue_correct_node


        #----------------------------------------------------------
        # 2. Set the links between the compositor nodes.
        #----------------------------------------------------------
        links = self.scene.node_tree.links

        links.new(image_node.outputs[0], keying_node.inputs[0])           # 'Image' -> 'Image'
        links.new(image_node.outputs[0], hue_correct_node.inputs[1])      # 'Image' -> 'Image'
        links.new(hue_correct_node.outputs[0], alphaover_node.inputs[2])  # 'Image' -> 'Image'

        links.new(boxmask_node.outputs[0], invert_node.inputs[1])         # 'Mask' -> 'Color'
        # links.new(invert_node.outputs[0], keying_node.inputs[2])          # 'Color' -> 'Garbage Matte'  

        links.new(keying_node.outputs[1], color_ramp_node.inputs[0])      # 'Matte' -> 'Fac'
        links.new(color_ramp_node.outputs[0], alphaover_node.inputs[0])   # 'Matte' -> 'Fac'

        links.new(alphaover_node.outputs[0], composite_node.inputs[0])    # 'Image' -> 'Image'
        links.new(alphaover_node.outputs[0], viewer_node.inputs[0])       # 'Image' -> 'Image'



    def hsv_to_rgb(
            self,
            h=0.0, 
            s=0.0, 
            v=0.0, 
            a=1.0
        ) -> tuple:
        if s:
            if h == 1.0: h = 0.0
            i = int(h*6.0); f = h*6.0 - i
            
            w = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            
            if i==0: return (v, t, w, a)
            if i==1: return (q, v, w, a)
            if i==2: return (w, v, t, a)
            if i==3: return (w, q, v, a)
            if i==4: return (t, w, v, a)
            if i==5: return (v, w, q, a)
        else: return (v, v, v, a)


    def set_greenscreen_settings(self):
        """
        Referring to https://www.youtube.com/watch?v=KBBkgoDPnZE
        """
        #---------------------------------------------
        # 1. Set the keying node's attributes.
        #---------------------------------------------
        keying_nodename = "Compositor_Keying"
        keying_node = self.compositor_nodes[keying_nodename]

        key_color = self.hsv_to_rgb(0.428, 0.984, 0.313, 1.0)
        keying_node.inputs[1].default_value = key_color   # Key color, keying_node.key_color

        keying_node.blur_pre = 3
        keying_node.screen_balance=0.5
        keying_node.despill_factor = 1.0
        keying_node.despill_balance = 0.5
        keying_node.edge_kernel_radius = 3
        keying_node.edge_kernel_tolerance = 0.1
        keying_node.clip_black = 0.0
        keying_node.clip_white = 1.0
        keying_node.dilate_distance = 0   # Dilate/Erode
        keying_node.feather_falloff = 'SMOOTH'
        keying_node.feather_distance = 0
        keying_node.blur_post = 2

        #---------------------------------------------
        # 2. Set the alpha_over node's attributes.
        #---------------------------------------------
        alphaover_nodename = "Compositor_AlphaOver"
        alphaover_node= self.compositor_nodes[alphaover_nodename]

        alphaover_node.use_premultiply = False
        alphaover_node.premul = 0
        alphaover_node.inputs[0].default_value = 1.1    # Fac
        alphaover_node.inputs[1].default_value = (0.0, 0.0, 0.0, 0.0)  # Change image color to be black

        #---------------------------------------------
        # 3. Set the box_mask node's attributes.
        #---------------------------------------------
        boxmask_nodename = "Compositor_BoxMask"
        boxmask_node = self.compositor_nodes[boxmask_nodename]

        """
        boxmask_node.x = 0.6
        boxmask_node.y = 0.4
        boxmask_node.mask_width = 0.25
        boxmask_node.mask_height = 0.15
        boxmask_node.rotation = 0.174533

        boxmask_node.mask_type = 'ADD'
        boxmask_node.inputs[0].default_value = 0.1
        boxmask_node.inputs[1].default_value = 1.9
        """

        #---------------------------------------------
        # 4. Set the invert node's attributes.
        #---------------------------------------------
        invert_nodename = "Compositor_Invert"
        invert_node = self.compositor_nodes[invert_nodename]

        invert_node.invert_rgb = True
        invert_node.invert_alpha = False
        invert_node.inputs[0].default_value = 1.0   # Fac
        invert_node.inputs[1].default_value = (1.0, 1.0, 1.0, 1.0)

        #---------------------------------------------
        # 5. Set the color ramp node's attributes.
        #---------------------------------------------
        colorramp_nodename = "Compositor_ColorRamp"        
        colorramp_node = self.compositor_nodes[colorramp_nodename]

        colorramp_node.color_ramp.color_mode = 'RGB'
        colorramp_node.color_ramp.interpolation = 'LINEAR'

        colorramp_node.color_ramp.elements[0].position = 0.311
        colorramp_node.color_ramp.elements[1].position = 0.762

        #---------------------------------------------
        # 6. Set the hue correct node's attributes.
        #---------------------------------------------
        hue_correct_nodename = "Compositor_HueCorrect"        
        hue_correct_node = self.compositor_nodes[hue_correct_nodename]

        # Access the individual curves:
        # Index 0: Hue-to-Hue curve
        # Index 1: Hue-to-Saturation curve
        # Index 2: Hue-to-Value curve
        hue_curve = hue_correct_node.mapping.curves[0]  # Hue-to-Hue curve
        saturation_curve = hue_correct_node.mapping.curves[1]  # Hue-to-Saturation curve
        value_curve = hue_correct_node.mapping.curves[2]  # Hue-to-Value curve
        
        # Clear any existing points on the hue curve (except the default start and end points)
        # to avoid a cluttered curve.
        while len(saturation_curve.points) > 2:
            saturation_curve.points.remove(saturation_curve.points[-1])

        new_point = saturation_curve.points.new(0.23, 0.0)
        new_point = saturation_curve.points.new(0.35, 0.0)
        new_point = saturation_curve.points.new(0.50, 0.35)
        
        # Update the curve mapping to apply changes
        hue_correct_node.mapping.update()


    def load_image_sequence(
            self,
            image_sequence_dir=""
        ):
        # 1. Double check if the input parameters are valid.
        if not os.path.isdir(image_sequence_dir):
            warn_msg = f"load_image_sequence(), image_sequence_dir='{image_sequence_dir}' is not a valid directory."
            self.logger.warn(warn_msg)
            return
        image_sequence_dir = image_sequence_dir.rstrip('/')

        # 2. Load the image sequence
        self.image_sequence_strip.load_image_sequence(
            image_sequence_dir=image_sequence_dir
        ) 
        self.scene_settings = self.image_sequence_strip.scene_settings
        first_path = self.image_sequence_strip.frame_image_filenames[0]

        scene_setting_str = json.dumps(
            self.scene_settings,
            indent=2,
            ensure_ascii=False
        )
        warn_msg = f"load_image_sequence(), scene_setting:\n{scene_setting_str}\n"
        self.logger.warn(warn_msg)
        self.logger.warn(f"len(self.frame_image_filenames)={len(self.image_sequence_strip.frame_image_filenames)}")
        self.logger.warn(f"self.frame_image_filename[0]: '{first_path}'")

        # 3. Load the first image to 'bpy.data.images'
        if first_path not in bpy.data.images:
            sequence_image = bpy.data.images.load(first_path)
        else:
            sequence_image = bpy.data.images[first_path]

        # Critical: Set image source to sequence
        sequence_image.source = 'SEQUENCE'

        sequence_image.filepath = first_path  # Path to first frame
        sequence_image.filepath_raw = first_path  # Raw path (no frame number substitution)

        # 4. Set the image sequence to the input of the image node
        image_nodename = "Compositor_Image"
        image_node = self.compositor_nodes[image_nodename]

        image_node.image = sequence_image

        image_node.frame_start = 1  # Start frame in timeline
        image_node.frame_duration = len(self.image_sequence_strip.frame_image_filenames)  # Total frames in sequence
        image_node.frame_offset = 0  # No frame offset
        image_node.use_cyclic = False  # Disable looping
        image_node.use_auto_refresh = True  # Auto-refresh when file changes

        # 5. Print out the info log
        info_msg = f"load_image_sequence(), load the image sequence from directory '{image_sequence_dir}', "
        info_msg += f"to '{image_nodename}' compositor node."
        self.logger.info(info_msg)


    @staticmethod
    def run_demo():
        green_screen_compositor = GreenScreenCompositor()
        green_screen_compositor.create_greenscreen_node()
        green_screen_compositor.set_greenscreen_settings()

        bicycle_green_screen_dir = "/home/robot/movie_blender_studio/output/bicycling_greenscreen_imgseq"
        kdeng_green_screen_dir = "/home/robot/movie_blender_studio/input/kan_walking_frames"
        green_screen_compositor.load_image_sequence(
            image_sequence_dir=kdeng_green_screen_dir
        )

