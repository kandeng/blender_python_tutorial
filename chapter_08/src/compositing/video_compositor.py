import bpy
import os
import json


class VideoCompositor():
    def __init__(self):
        self.node_tree = None 
        self.compositor_node_list = []

        self.renderer = None
        self.editor_node = None
        self.cinematic_compositor = None
        self.movie_clip_node = None
        
        #
        # Video Size: clip.size returns a tuple (width, height) in pixels.
        # Frame Count: clip.frame_duration gives the total number of frames in the video (accounts for speed changes if any).
        # FPS: clip.fps provides the video's original frame rate (this is separate from the scene's frame rate).
        #    - bpy.context.scene.render.fps: Base frame rate
        #    - bpy.context.scene.render.fps_base: Frame rate divisor (usually 1.0 for standard FPS values)
        # 
        self.movie_clip_size = None
        self.movie_clip_frame_duration = 0
        self.movie_clip_fps = 0

        try:
            scene = bpy.context.scene
            if not scene.use_nodes:
                scene.use_nodes = True
            self.node_tree = scene.node_tree

            from logger.logger import LlamediaLogger
            self.logger = LlamediaLogger("VideoCompositor").getLogger()

            from camera.camera import Camera
            self.renderer = Camera().renderer

            from editor.editor_node import EditorNode
            self.editor_node = EditorNode(editor_name="Compositor", editor_type="COMPOSITING")

            from compositing.cinematic_compositor import CinematicCompositor
            self.cinematic_compositor = CinematicCompositor()

            # Create all compositor nodes, including a cinematic node, and a view node.
            self.create_compositor_nodes()

        except ImportError as e:
            if self.logger:
                self.logger.error(f"Could not initialize VideoCompositor class, error message: '{str(e)}'")
            else:
                print(f"[ERROR] Could not initialize VideoCompositor class, error message: '{str(e)}'")
        

    def create_compositor_nodes(self):
        # 1. Create all compositor nodes, not including a cinematic node.
        self.create_base_nodes()

        # 2. Create a Cinematic node
        self.cinematic_compositor.create_cinematic_node()
        if self.cinematic_compositor.cinematic_node:
            cinematic_nodename = "CinematicCompositor" 
            if cinematic_nodename not in self.compositor_node_list:
                self.compositor_node_list.append(cinematic_nodename)

        # 3. For unknown reason, after creating 'CinematicCompositor',
        #    The 'Viewer' disappear, hence, to create again.
        viewer_nodename = "Compositor_Viewer"
        viewer_node = self.editor_node.get_node(viewer_nodename)
        if not viewer_node:
            viewer_node = self.node_tree.nodes.new(type='CompositorNodeViewer')

        viewer_node.name = viewer_nodename
        viewer_node.location = (300, -300)
        if viewer_nodename not in self.compositor_node_list:
            self.compositor_node_list.append(viewer_nodename)        


    def create_base_nodes(self):
        # 1. Clear existing nodes (optional)
        for node in self.node_tree.nodes:
            self.node_tree.nodes.remove(node)

        # 2. Create a Movie Clip node
        movie_clip_nodename = "Compositor_VideoInput"
        self.movie_clip_node = self.editor_node.get_node(movie_clip_nodename)
        if not self.movie_clip_node:
            self.movie_clip_node = self.node_tree.nodes.new(type='CompositorNodeMovieClip')

        self.movie_clip_node.name = movie_clip_nodename
        self.movie_clip_node.location = (-300, 300)  # Position node in the compositor
        if movie_clip_nodename not in self.compositor_node_list:
            self.compositor_node_list.append(movie_clip_nodename)

        # 3. Image input node (Not always useful, but prepare for potential use.)
        image_nodename = "Compositor_Image"
        image_node = self.editor_node.get_node(image_nodename)
        if not image_node:
            image_node = self.node_tree.nodes.new(type='CompositorNodeImage')

        image_node.name = image_nodename
        image_node.location = (-300, 0)
        if image_nodename not in self.compositor_node_list:
            self.compositor_node_list.append(image_nodename)

        # 4. Render Layers node (Not always useful, but prepare for potential use.)
        render_layers_nodename = "Compositor_RenderLayers"
        render_layers = self.editor_node.get_node(render_layers_nodename)
        if not render_layers:
            render_layers = self.node_tree.nodes.new(type='CompositorNodeRLayers')

        render_layers.name = render_layers_nodename
        render_layers.location = (-300, -300)
        if render_layers_nodename not in self.compositor_node_list:
            self.compositor_node_list.append(render_layers_nodename)

        # 5. Denoise node (Not always useful, but prepare for potential use.)
        denoise_nodename = "Compositor_Denoise"
        denoise_node = self.editor_node.get_node(denoise_nodename)
        if not denoise_node:
            denoise_node = self.node_tree.nodes.new(type='CompositorNodeDenoise')

        denoise_node.name = denoise_nodename
        denoise_node.location = (0, 0)
        if denoise_nodename not in self.compositor_node_list:
            self.compositor_node_list.append(denoise_nodename)

        # 6. Composite node (final output)
        composite_nodename = "Compositor_Composite"
        composite_node = self.editor_node.get_node(composite_nodename)
        if not composite_node:
            composite_node = self.node_tree.nodes.new(type='CompositorNodeComposite')

        composite_node.name = composite_nodename
        composite_node.location = (300, 300)
        if composite_nodename not in self.compositor_node_list:
            self.compositor_node_list.append(composite_nodename)
        
        # 7. Viewer node (preview)
        viewer_nodename = "Compositor_Viewer"
        viewer_node = self.editor_node.get_node(viewer_nodename)
        if not viewer_node:
            viewer_node = self.node_tree.nodes.new(type='CompositorNodeViewer')

        viewer_node.name = viewer_nodename
        viewer_node.location = (300, -300)
        if viewer_nodename not in self.compositor_node_list:
            self.compositor_node_list.append(viewer_nodename)


    def video_processing_decorator(func):
        """
        A decorator function for all image processing functions.
        """
        def wrapper(self, *args, **kwargs):
            # 1. Load the input image to the InputImage node.
            input_video_filename = kwargs.get("input_video_filename", "")
            self.load_video(video_filename=input_video_filename)

            # 2. Call the func with its parameters.
            in_out = func(self, *args, **kwargs)
            in_node = in_out["in_node"]
            in_socket = in_out["in_socket"]
            out_node = in_out["out_node"]
            out_socket = in_out["out_socket"]

            # 3. Get the base nodes.
            composite_node = self.editor_node.get_node("Compositor_Composite")
            viewer_node = self.editor_node.get_node("Compositor_Viewer")

            # 4. Link nodes together
            links = self.node_tree.links
            links.new(self.movie_clip_node.outputs[0], in_node.inputs[in_socket[0]])    # 'Image'
            links.new(self.movie_clip_node.outputs[1], in_node.inputs[in_socket[1]])    # 'Alpha'
            links.new(out_node.outputs[out_socket[0]], composite_node.inputs[0])        # 'Image'
            links.new(out_node.outputs[out_socket[1]], composite_node.inputs[1])        # 'Alpha'
            links.new(out_node.outputs[out_socket[0]], viewer_node.inputs[0])           # 'Image'
            links.new(out_node.outputs[out_socket[1]], viewer_node.inputs[1])           # 'Alpha'

            # 5. Print out the info log.
            info_msg = f"image_processing_decorator(), input_image='{input_video_filename}'."
            self.logger.info(info_msg)

        # Return the wrapper function
        return wrapper


    def render_video(
            self, 
            output_video_filename=""
        ):        
        # 1. Render the scene into an image.
        self.renderer.set_scene_settings(
            engine='CYCLES', 
            resolution_x=self.movie_clip_size[0], 
            resolution_y=self.movie_clip_size[1], 
            samples=32, 
            frame_start=1, 
            frame_end=self.movie_clip_frame_duration+1
        )
        self.renderer.set_output_settings(
            file_name="",
            file_format="FFMPEG", 
            video_codec="H264", 
            container="MPEG4",
            fps=round(self.movie_clip_fps)
        )
        # Bug fixing, override the output_path
        bpy.context.scene.render.filepath = output_video_filename

        # 2. Start the rendering, it will take quite long time. 
        self.renderer.start_rendering()

        # 3. Print out the info log.
        info_msg = f"image_processing_decorator(), output_image='{output_video_filename}''."
        self.logger.info(info_msg)


    def load_video(
            self, 
            video_filename=""
        ):
        if not os.path.exists(video_filename):
            warn_msg = f"load_video(), Input video file not found: {video_filename}."
            self.logger.warn(warn_msg)
            return

        # Load the video file into a new movie clip data block
        try:
            # Create a new movie clip
            clip = bpy.data.movieclips.load(video_filename)
            self.movie_clip_node.clip = clip

            self.movie_clip_size = clip.size
            self.movie_clip_frame_duration = clip.frame_duration
            self.movie_clip_fps = clip.fps

            info_msg = f"load_video(), successfully loaded video: '{video_filename}', \n\t"
            info_msg += f"Video properties - Size(x*y): ({clip.size[0]}*{clip.size[1]}), Frames: {clip.frame_duration}, FPS: {clip.fps}."
            self.logger.info(info_msg)

        except Exception as e:
            warn_msg = f"load_video(), failed to load video '{video_filename}', "
            warn_msg += f"the error message is: '{str(e)}'"
            self.logger.warn(warn_msg)



    @video_processing_decorator
    def cinematic_mystery(
            self,
            input_video_filename=""
        ):
        in_out = self.cinematic_compositor.cinematic_mystery()
        return in_out   
    


    @staticmethod
    def run_demo():
        video_compositor = VideoCompositor()
        compositor_node_list = video_compositor.compositor_node_list 
        compositor_node_str = json.dumps(compositor_node_list, indent=2, ensure_ascii=False)
        video_compositor.logger.debug(f"Video compositor nodes: \n\t{compositor_node_str}")

        input_videos = [
            "/home/robot/movie_blender_studio/input/nyu_corridor.MOV",
            "/home/robot/movie_blender_studio/input/TrueStory.mp4"
        ]
        output_videos = [
            "/home/robot/movie_blender_studio/output/nyu_corridor_cinematic_20250916.mp4"
        ]

        video_compositor.cinematic_mystery(
            input_video_filename=input_videos[0]       
        )
        video_compositor.render_video(
            output_video_filename=output_videos[0]
        )
