import bpy
import os

class ApplyTexture:
    """
    A class to apply a full set of PBR textures to a specified mesh object.
    """
    def __init__(self, mesh_object, texture_dir, use_modifier=False):
        """
        Initializes the texture application process.

        Args:
            mesh_object (bpy.types.Object): The mesh object to texture.
            texture_dir (str): The directory containing the texture files.
        """
        # 1. Double-check if the mesh and texture files are ready.
        if not mesh_object or not hasattr(mesh_object, 'type') or mesh_object.type != 'MESH':
            raise ValueError("A valid mesh object must be provided.")
        self.mesh = mesh_object

        if not os.path.isdir(texture_dir):
            raise FileNotFoundError(f"Texture directory not found: {texture_dir}")
        self.texture_dir = texture_dir

        self.texture_paths = self._scan_texture_directory()
        self.material = None
        self.nodes = None
        self.links = None
        self.principled_bsdf = None
        self.mapping_node = None
        self.output_node = None

        self.use_modifier=False

        print(f"[INFO] ApplyTexture initialized for mesh '{self.mesh.name}'.")
        print(f"[INFO] Found {len(self.texture_paths)} texture maps.")

    def _scan_texture_directory(self):
        """ Scans the directory for common PBR texture maps. """
        texture_files = {}
        for file in os.listdir(self.texture_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tif')):
                file_path = os.path.join(self.texture_dir, file)
                if 'color' in file.lower() or 'albedo' in file.lower():
                    texture_files['color'] = file_path
                elif 'displacement' in file.lower() or 'height' in file.lower():
                    texture_files['displacement'] = file_path
                elif 'roughness' in file.lower():
                    texture_files['roughness'] = file_path
                elif 'normal' in file.lower():
                    texture_files['normal'] = file_path
                elif 'metal' in file.lower():
                    texture_files['metalness'] = file_path
        return texture_files

    def create_base_nodes(self):
        """
        2. Creates the commonly used, non-image-specific shader nodes.
        """
        print("[INFO] Creating base shader nodes...")
        self.material = bpy.data.materials.new(name=f"{self.mesh.name}_Material")
        self.material.use_nodes = True
        self.mesh.data.materials.append(self.material)
        self.nodes = self.material.node_tree.nodes
        self.links = self.material.node_tree.links
        self.nodes.clear()

        # Create essential nodes
        self.output_node = self.nodes.new(type='ShaderNodeOutputMaterial')
        self.output_node.location = (1000, 0)

        self.principled_bsdf = self.nodes.new(type='ShaderNodeBsdfPrincipled')
        self.principled_bsdf.location = (700, 0)
        self.links.new(self.principled_bsdf.outputs['BSDF'], self.output_node.inputs['Surface'])

        tex_coord_node = self.nodes.new(type='ShaderNodeTexCoord')
        tex_coord_node.location = (0, 300)

        self.mapping_node = self.nodes.new(type='ShaderNodeMapping')
        self.mapping_node.location = (200, 300)
        self.links.new(tex_coord_node.outputs['UV'], self.mapping_node.inputs['Vector'])

    def create_texture_nodes(self):
        """
        3. Creates image texture nodes for all available texture maps.
        """
        if not self.principled_bsdf:
            print("[ERROR] Base nodes not created. Run create_base_nodes() first.")
            return

        print("[INFO] Creating image texture nodes...")
        # Create and connect nodes for each texture type found
        if 'color' in self.texture_paths:
            self._create_texture_node('color', (400, 500), 'Base Color')
        if 'roughness' in self.texture_paths:
            self._create_texture_node('roughness', (400, 250), 'Roughness', 'Non-Color')
        if 'metalness' in self.texture_paths:
            self._create_texture_node('metalness', (400, 0), 'Metallic', 'Non-Color')
        if 'normal' in self.texture_paths:
            self._create_normal_node((400, -250))
        if 'displacement' in self.texture_paths:
            if self.use_modifier:
                self.create_displacement_modifier((400, -500))
            else:
                self.create_displacement_node((400, -500))

    def _create_texture_node(self, map_type, location, bsdf_input, color_space='sRGB'):
        """ Helper to create and connect a single image texture node. """
        path = self.texture_paths[map_type]
        tex_node = self.nodes.new(type='ShaderNodeTexImage')
        tex_node.location = location
        tex_node.image = bpy.data.images.load(path)
        tex_node.image.colorspace_settings.name = color_space
        self.links.new(self.mapping_node.outputs['Vector'], tex_node.inputs['Vector'])
        self.links.new(tex_node.outputs['Color'], self.principled_bsdf.inputs[bsdf_input])
        print(f"[INFO] Created {map_type} node.")

    def _create_normal_node(self, location):
        """ Helper to create and connect a normal map node setup. """
        path = self.texture_paths['normal']
        tex_node = self.nodes.new(type='ShaderNodeTexImage')
        tex_node.location = location
        tex_node.image = bpy.data.images.load(path)
        tex_node.image.colorspace_settings.name = 'Non-Color'
        self.links.new(self.mapping_node.outputs['Vector'], tex_node.inputs['Vector'])

        normal_map_node = self.nodes.new(type='ShaderNodeNormalMap')
        normal_map_node.location = (location[0] + 250, location[1])
        self.links.new(tex_node.outputs['Color'], normal_map_node.inputs['Color'])
        self.links.new(normal_map_node.outputs['Normal'], self.principled_bsdf.inputs['Normal'])
        print(f"[INFO] Created normal map node.")

    def create_displacement_node(self, location):
        """ Helper to create and connect a displacement node setup. """
        path = self.texture_paths['displacement']
        tex_node = self.nodes.new(type='ShaderNodeTexImage')
        tex_node.location = location
        tex_node.image = bpy.data.images.load(path)
        tex_node.image.colorspace_settings.name = 'Non-Color'
        self.links.new(self.mapping_node.outputs['Vector'], tex_node.inputs['Vector'])

        disp_node = self.nodes.new(type='ShaderNodeDisplacement')
        disp_node.location = (location[0] + 250, location[1])
        disp_node.inputs['Scale'].default_value = 0.1
        self.links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
        self.links.new(disp_node.outputs['Displacement'], self.output_node.inputs['Displacement'])
        # Enable displacement in material settings for Cycles
        self.material.displacement_method = 'BOTH'

        self.use_modifier=False
        print(f"[INFO] Created displacement shader node.")

    def create_displacement_modifier(self, strength=0.5, midlevel=0.5):
        # There are 2 ways to use displacement,
        # 1. Use shader node, to change the way of rendering only,
        # 2. User modifier tool, to change the locations of the vertices physically.
        # Usually, only one way is selected to use. 
        # However, it is okay to use both. The rendering effect will look like doubly displaced. 

        bpy.context.view_layer.objects.active = self.mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        try:
            path = self.texture_paths['displacement']
            disp_image = bpy.data.images.load(path, check_existing=True)
            disp_image.colorspace_settings.name = 'Non-Color'
        except Exception as e:
            print(f"[ERROR] Could not load displacement texture: {e}")
            return

        disp_texture = bpy.data.textures.new(name="RockDisplacementTexture", type='IMAGE')
        disp_texture.image = disp_image

        disp_mod = self.mesh.modifiers.new(name="Final_Displacement", type='DISPLACE')
        disp_mod.texture = disp_texture
        disp_mod.texture_coords = 'UV'
        disp_mod.uv_layer = "UVMap"
        disp_mod.strength = strength
        disp_mod.mid_level = midlevel

        self.use_modifier=True
        print(f"[INFO] Created displacement modifier.")


    def run(self):
        """ Creates and connects all shader nodes. """
        self.create_base_nodes()
        self.create_texture_nodes()
        print(f"[INFO] Texture shader graph created successfully.")

    @staticmethod
    def setup_render_engine(engine='CYCLES', resolution=(1920, 1080)):
        """
        4. Sets up the render engine and output settings.

        Args:
            engine (str): The render engine to use ('CYCLES' or 'EEVEE').
            resolution (tuple): The output resolution (width, height).
        """
        print(f"[INFO] Setting up {engine} render engine...")
        scene = bpy.context.scene
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]

        if engine.upper() == 'CYCLES':
            scene.render.engine = 'CYCLES'
            scene.cycles.device = 'GPU'
            scene.cycles.samples = 128
        elif 'EEVEE' in engine.upper():
            try:
                scene.render.engine = 'BLENDER_EEVEE'
            except TypeError:
                print(f"[WARNING] BLENDER_EEVEE not available, falling back to BLENDER_EEVEE_NEXT.")
                scene.render.engine = 'BLENDER_EEVEE_NEXT'
            scene.eevee.taa_render_samples = 64
        else:
            print(f"[WARNING] Unknown render engine '{engine}'. Defaulting to Cycles.")
            scene.render.engine = 'CYCLES'

# --- Main execution example ---
if __name__ == "__main__":
    # Clear the scene and create a sample mesh to texture
    bpy.ops.object.select_all(action='SELECT')
    if bpy.context.active_object: bpy.ops.object.delete()

    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    sample_mesh = bpy.context.active_object
    sample_mesh.name = "DemoFloor"
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=50)
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Define the texture directory
    # IMPORTANT: Update this path to your texture folder
    texture_directory = "/home/robot/movie_blender_studio/asset/texture/WoodFloor043_4K"

    try:
        # 1. Instantiate the class with the mesh and texture directory
        texture_applier = ApplyTexture(mesh_object=sample_mesh, texture_dir=texture_directory)

        # 2. Run the texturing process
        texture_applier.run()
        texture_applier.create_displacement_modifier()

        # 3. Set up the render engine
        ApplyTexture.setup_render_engine(engine='EEVEES')

        print("\n[SUCCESS] Script finished.")

    except (ValueError, FileNotFoundError) as e:
        print(f"\n[ERROR] An error occurred: {e}")

