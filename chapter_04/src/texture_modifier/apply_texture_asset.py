import bpy
import os
import sys
import pprint

# Add the parent directory to sys.path to import create_texture
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from texture_modifier.texture_generator import TextureGenerator
from texture_modifier.modifier_generator import ModifierGenerator

class ApplyTexture:
    """
    A class to apply a full set of PBR textures to a specified mesh object.
    """
    def __init__(self):
        """
        Initializes the texture application process.
        """
        try:
            print(f"[INFO] In RockGenerator, sys.path: '{sys.path}'")
            from texture_modifier.texture_generator import TextureGenerator
            from texture_modifier.modifier_generator import ModifierGenerator
        except ImportError:
            print("[ERROR] Could not import ApplyTexture class. Make sure 'apply_texture_to_mesh.py' is in the correct directory.")
            ApplyTexture = None

        self.mesh = None
        self.texture_dir = None

        self.material = None
        self.texture_generator = None
        self.principled_bsdf = None
        self.mapping_node = None
        self.output_node = None
        self.use_modifier = True


    def set_object(self, mesh_object=None):
        # Double-check if the mesh object is ready.
        if not mesh_object or not hasattr(mesh_object, 'type') or mesh_object.type != 'MESH':
            raise ValueError("A valid mesh object must be provided.")
        
        self.mesh = mesh_object
        print(f"[INFO] ApplyTexture initialized for mesh '{self.mesh.name}'.")

    def set_texture_directory(self, texture_dir="/"):
        if not os.path.isdir(texture_dir):
            raise FileNotFoundError(f"Texture directory not found: {texture_dir}")
        
        self.texture_dir = texture_dir
        self.texture_paths = self._scan_texture_directory()    
        print(f"[INFO] Found {len(self.texture_paths)} texture maps.")
    

    def _scan_texture_directory(self):
        """ Scans the directory for common PBR texture maps. """
        texture_files = {}
        for file in os.listdir(self.texture_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', 'exr')):
                file_path = os.path.join(self.texture_dir, file)
                if 'color' in file.lower() or 'albedo' in file.lower() or 'diff' in file.lower():
                    texture_files['color'] = file_path
                elif 'displacement' in file.lower() or 'height' in file.lower() or 'disp' in file.lower():
                    texture_files['displacement'] = file_path
                elif 'rough' in file.lower():
                    texture_files['roughness'] = file_path
                elif 'normal' in file.lower() or 'nor' in file.lower():
                    texture_files['normal'] = file_path
                elif 'metal' in file.lower():
                    texture_files['metalness'] = file_path
        
        print(f"\n[INFO] texture_files in file directory '{self.texture_dir}':")
        pprint.pprint(texture_files)
        print(f"\n")
        return texture_files

    def create_base_nodes(self):
        """
        2. Creates the commonly used, non-image-specific shader nodes using TextureGenerator.
        """
        print("[INFO] Creating base shader nodes...")
        
        # Create material using TextureGenerator
        material_name = f"{self.mesh.name}_Material"
        self.texture_generator = TextureGenerator()
        self.texture_generator.set_object(self.mesh)
        self.material = self.texture_generator.create_material(material_name)
        
        # Create essential nodes using TextureGenerator
        self.output_node = self.texture_generator.create_node(
            'ShaderNodeOutputMaterial', 
            "Output_Node", 
            location=(1000, 0)
        )
        
        self.principled_bsdf = self.texture_generator.create_node(
            'ShaderNodeBsdfPrincipled', 
            "Principled_BSDF", 
            location=(700, 0)
        )
        
        # Link BSDF to output
        self.texture_generator.create_link(
            self.principled_bsdf, 'BSDF', 
            self.output_node, 'Surface'
        )
        
        tex_coord_node = self.texture_generator.create_node(
            'ShaderNodeTexCoord', 
            "Texture_Coordinate", 
            location=(0, 300)
        )
        
        self.mapping_node = self.texture_generator.create_node(
            'ShaderNodeMapping', 
            "Mapping", 
            location=(200, 300)
        )
        
        # Link texture coordinate to mapping
        self.texture_generator.create_link(
            tex_coord_node, 'UV', 
            self.mapping_node, 'Vector'
        )
        
        print("[INFO] Base shader nodes created using TextureGenerator.")

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
                self.create_displacement_modifier()
            else:
                self.create_displacement_node((400, -500))

    def _create_texture_node(self, map_type, location, bsdf_input, color_space='sRGB'):
        """ Helper to create and connect a single image texture node using TextureGenerator. """
        path = self.texture_paths[map_type]
        
        # Create texture node
        tex_node = self.texture_generator.create_node(
            'ShaderNodeTexImage', 
            f"{map_type.capitalize()}_Texture", 
            location=location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(path)
        tex_node.image.colorspace_settings.name = color_space
        
        # Link mapping to texture
        self.texture_generator.create_link(
            self.mapping_node, 'Vector', 
            tex_node, 'Vector'
        )
        
        # Link texture to BSDF input
        self.texture_generator.create_link(
            tex_node, 'Color', 
            self.principled_bsdf, bsdf_input
        )
        
        print(f"[INFO] Created {map_type} node using TextureGenerator.")

    def _create_normal_node(self, location):
        """ Helper to create and connect a normal map node setup using TextureGenerator. """
        path = self.texture_paths['normal']
        
        # Create texture node
        tex_node = self.texture_generator.create_node(
            'ShaderNodeTexImage', 
            "Normal_Texture", 
            location=location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(path)
        tex_node.image.colorspace_settings.name = 'Non-Color'
        
        # Link mapping to texture
        self.texture_generator.create_link(
            self.mapping_node, 'Vector', 
            tex_node, 'Vector'
        )

        # Create normal map node
        normal_map_node = self.texture_generator.create_node(
            'ShaderNodeNormalMap', 
            "Normal_Map", 
            location=(location[0] + 250, location[1])
        )
        
        # Link texture to normal map
        self.texture_generator.create_link(
            tex_node, 'Color', 
            normal_map_node, 'Color'
        )
        
        # Link normal map to BSDF
        self.texture_generator.create_link(
            normal_map_node, 'Normal', 
            self.principled_bsdf, 'Normal'
        )
        
        print(f"[INFO] Created normal map node using TextureGenerator.")

    def create_displacement_node(self, location):
        """ Helper to create and connect a displacement node setup using TextureGenerator. """
        path = self.texture_paths['displacement']
        
        # Create texture node
        tex_node = self.texture_generator.create_node(
            'ShaderNodeTexImage', 
            "Displacement_Texture", 
            location=location
        )
        
        # Load image and set color space
        tex_node.image = bpy.data.images.load(path)
        tex_node.image.colorspace_settings.name = 'Non-Color'
        
        # Link mapping to texture
        self.texture_generator.create_link(
            self.mapping_node, 'Vector', 
            tex_node, 'Vector'
        )

        # Create displacement node
        disp_node = self.texture_generator.create_node(
            'ShaderNodeDisplacement', 
            "Displacement", 
            location=(location[0] + 250, location[1])
        )
        
        # Set displacement scale
        disp_node.inputs['Scale'].default_value = 0.1
        
        # Link texture to displacement
        self.texture_generator.create_link(
            tex_node, 'Color', 
            disp_node, 'Height'
        )
        
        # Link displacement to output
        self.texture_generator.create_link(
            disp_node, 'Displacement', 
            self.output_node, 'Displacement'
        )
        
        # Enable displacement in material settings for Cycles
        self.material.displacement_method = 'BOTH'

        self.use_modifier = False
        print(f"[INFO] Created displacement shader node using TextureGenerator.")

    def create_displacement_modifier(self, disp_strength:float=0.1, midlevel:float=0.0):
        """
        Create a displacement modifier using the ModifierGenerator class.
        There are 2 ways to use displacement,
        1. Use shader node, to change the way of rendering only,
        2. Use modifier tool, to change the locations of the vertices physically.
        Usually, only one way is selected to use. 
        However, it is okay to use both. The rendering effect will look like doubly displaced. 
        """
        # Prepare the mesh for UV mapping
        bpy.context.view_layer.objects.active = self.mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project()
        bpy.ops.object.mode_set(mode='OBJECT')

        try:
            # Load the displacement texture
            path = self.texture_paths['displacement']
            disp_image = bpy.data.images.load(path, check_existing=True)
            disp_image.colorspace_settings.name = 'Non-Color'
        except Exception as e:
            print(f"[ERROR] Could not load displacement texture: {e}")
            return

        # Create a texture for the displacement modifier
        disp_texture = bpy.data.textures.new(name="RockDisplacementTexture", type='IMAGE')
        disp_texture.image = disp_image

        # Initialize the ModifierGenerator
        modifier_generator = ModifierGenerator()
        modifier_generator.set_object(self.mesh)

        # Create displacement modifier with initial attributes
        modifier_attributes = {
            "strength": disp_strength,
            "mid_level": midlevel,
            "texture_coords": 'UV',
            "uv_layer": "UVMap",
            "texture": disp_texture
        }

        # Create the displacement modifier using ModifierGenerator
        disp_mod = modifier_generator.create_modifier(
            modifier_type="displace",
            modifier_name="Final_Displacement",
            modifier_attributes=modifier_attributes
        )

        self.use_modifier = True
        print(f"[INFO] Created displacement modifier using ModifierGenerator.")

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
    @staticmethod
    def run_demo():
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
            texture_applier = ApplyTexture()
            texture_applier.set_object(sample_mesh)
            texture_applier.set_texture_directory(texture_directory)

            # 2. Run the texturing process
            texture_applier.run()
            texture_applier.create_displacement_modifier()

            # 3. Set up the render engine
            ApplyTexture.setup_render_engine(engine='EEVEE')

            print("\n[SUCCESS] Script finished.")

        except (ValueError, FileNotFoundError) as e:
            print(f"\n[ERROR] An error occurred: {e}")



if __name__ == "__main__":
    ApplyTexture.run_demo()