import os
import random
import json
import bpy


class Compositor:
    def __init__(self):
        self.logger = None
        self.camera = None

        self.node_tree = None
        self.base_node_names = ["CinematicCompositor"]   # Reserve CinematicCompositor as a base node.

        self.color_compositor = None
        self.cinematic_compositor = None

        try:
            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("Compositor").getLogger()

            from editor.editor_node import EditorNode
            self.editor_node = EditorNode(editor_name="Compositor", editor_type="COMPOSITING")
            self.node_tree = self.editor_node.node_tree

            from camera.camera import Camera
            self.camera = Camera("CompositorCamera")

            self.create_base_nodes()
            self.remove_nonbase_nodes()

            from compositing.cinematic_compositor import CinematicCompositor
            self.cinematic_compositor = CinematicCompositor()

            from compositing.color_compositor import ColorCompositor
            self.color_compositor = ColorCompositor()

            self.logger.info(f"Compositor class initialized.")
        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize Compositor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize Compositor class, error message: '{str(e)}'")


    def create_base_nodes(self):   
        # 1. Image node (input image)
        image_node = self.editor_node.get_node("Compositor_InputImage")
        if not image_node:
            image_node = self.node_tree.nodes.new(type='CompositorNodeImage')
        image_node.location = (-1000, -300)
        image_node.name = "Compositor_InputImage"
        self.base_node_names.append(image_node.name)

        # 2. Render Layers node (as requested, even if we use an image)
        render_layers = self.editor_node.get_node("Compositor_RenderLayers")
        if not render_layers:
            render_layers = self.node_tree.nodes.new(type='CompositorNodeRLayers')
        render_layers.location = (-1000, 0)
        render_layers.name = "Compositor_RenderLayers"
        self.base_node_names.append(render_layers.name)
   
        # 3. Mix node (blend image with noise)
        mix_node = self.editor_node.get_node("Compositor_MixRGB")
        if not mix_node:
            mix_node = self.node_tree.nodes.new(type='CompositorNodeMixRGB')
        mix_node.location = (0, -300)
        mix_node.name = "Compositor_MixRGB"
        self.base_node_names.append(mix_node.name)

        mix_node.blend_type = 'MULTIPLY'  # Darkens image where noise is present
        mix_node.inputs['Fac'].default_value = 0.3  # Noise strength (30%)
        
        # 4. Composite node (final output)
        composite_node = self.editor_node.get_node("Compositor_Composite")
        if not composite_node:
            composite_node = self.node_tree.nodes.new(type='CompositorNodeComposite')
        composite_node.location = (300, 300)
        composite_node.name = "Compositor_Composite"
        self.base_node_names.append(composite_node.name)
        
        # 5. Viewer node (preview)
        viewer_node = self.editor_node.get_node("Compositor_Viewer")
        if not viewer_node:
            viewer_node = self.node_tree.nodes.new(type='CompositorNodeViewer')
        viewer_node.location = (300, -300)
        viewer_node.name = "Compositor_Viewer"
        self.base_node_names.append(viewer_node.name)


    def remove_nonbase_nodes(self):
        removed_nodes = []
        remained_nodes = []

        try:
            # Clear default nodes
            for node in self.node_tree.nodes:
                if node.name not in self.base_node_names:
                    removed_nodes.append(node.name)
                    self.node_tree.nodes.remove(node)
                else:
                    remained_nodes.append(node.name)
            
            info_msg = f"remove_nonbase_nodes(), Remove all the compositing nodes except the base nodes."
            self.logger.info(info_msg)

            removed_nodes_str = json.dumps(removed_nodes, indent=2, ensure_ascii=False)
            self.logger.debug(f"The non-base nodes that have been removed:\n{removed_nodes_str}\n")

            remained_nodes_str = json.dumps(remained_nodes, indent=2, ensure_ascii=False)
            self.logger.debug(f"The nodes that have been remained:\n{remained_nodes_str}\n")


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
        return image_node
  

    def get_image_format_from_filename(
            self, 
            filename=""
        ) -> str:
        """
        Get the image file format based on the given filename's suffix.
        """
        # A dictionary mapping file extensions to Blender's internal file format identifiers.
        # Note: These names are case-sensitive.
        file_formats = {
            '.png': 'PNG',
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.bmp': 'BMP',
            '.tga': 'TGA',
            '.tif': 'TIFF',
            '.tiff': 'TIFF',
            '.exr': 'OPEN_EXR',
            # Add more mappings as needed
        }

        # Extract the file extension from the filename.
        file_extension = os.path.splitext(filename)[1].lower()

        # Get the corresponding Blender file format identifier.
        file_format = file_formats.get(file_extension)

        if file_format:
            return file_format
        else:
            return ""


    def image_processing_decorator(func):
        """
        A decorator function for all image processing functions.
        """
        def wrapper(self, *args, **kwargs):
            # 1. Clean the compositing nodes.
            self.remove_nonbase_nodes()

            # 2. Load the input image to the InputImage node.
            input_image = kwargs.get("input_image_filename", "")
            image_node = self.load_image(single_image_filename=input_image)

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
            image_format = self.get_image_format_from_filename(output_image)
            if len(image_format) == 0: image_format = "PNG"
            self.camera.renderer.set_image_settings(      
                engine='CYCLES', 
                file_format=image_format,
                resolution_x=image_node.image.size[0], 
                resolution_y=image_node.image.size[1], 
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
        in_out = self.color_compositor.denoise()
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
        in_out = self.color_compositor.blur(blur_factor)
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
        in_out = self.color_compositor.adjust_color(
            bright_contrast=(0.1, 0.2), 
            hue_saturation_value=(0.1, 1.2, 1.0),
            color_balance=[(1, 1, 1), (1.02, 1.02, 1.02), (0.8, 0.8, 0.8)],
            rgb_to_bw=False
        )
        return in_out        

    
    @image_processing_decorator
    def cinematic_mystery(
            self,
            input_image_filename="",
            output_image_filename=""
        ):
        in_out = self.cinematic_compositor.cinematic_mystery()

        # Fix a bug, the view node disappears for unknown reason.
        self.create_base_nodes()
        return in_out   



    @staticmethod
    def run_demo():
        image_compositor = Compositor()
        base_node_names = image_compositor.base_node_names 
        base_node_names_str = json.dumps(base_node_names, indent=2, ensure_ascii=False)
        image_compositor.logger.debug(f"Base nodes: \n\t{base_node_names_str}")

        input_images = [
            "/home/robot/movie_blender_studio/input/balloons_noisy.png",
            "/home/robot/movie_blender_studio/input/battle_field.png",
            "/home/robot/movie_blender_studio/input/opera_house_inside.jpeg",
            "/home/robot/movie_blender_studio/input/opera_house_outside.jpeg"
        ]
        output_images = [
            "/home/robot/movie_blender_studio/output/balloons_noisy_denoise.jpg",
            "/home/robot/movie_blender_studio/output/balloons_noisy_blur.jpg",
            "/home/robot/movie_blender_studio/output/battle_field_color_adjusted.jpg",
            "/home/robot/movie_blender_studio/output/opera_house_inside_cinematic.jpg",
            "/home/robot/movie_blender_studio/output/opera_house_outside_cinematic.jpg"
        ]

        image_compositor.denoise(
            input_image_filename=input_images[0],
            output_image_filename=output_images[0]
        )        
        
        image_compositor.blur(
            input_image_filename=input_images[0],
            output_image_filename=output_images[1],
            blur_factor=(1, 2) 
        )
        
        image_compositor.adjust_color(
            input_image_filename=input_images[1],
            output_image_filename=output_images[2], 
            bright_contrast=(0.1, 0.2), 
            hue_saturation_value=(0.1, 1.2, 1.0),
            color_balance=[(0.9, 1, 1.1), (0.99, 1.0, 1.01), (0.79, 0.8, 0.81)]
        )        

        image_compositor.cinematic_mystery(
            input_image_filename=input_images[2],
            output_image_filename=output_images[3], 
        )
        image_compositor.cinematic_mystery(
            input_image_filename=input_images[3],
            output_image_filename=output_images[4], 
        )

        



if __name__ == "__main__":
    Compositor.run_demo()