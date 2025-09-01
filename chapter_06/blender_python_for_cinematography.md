# AI Coder Oriented Blender Python Package for Cinematography

## 1. Objectives

In chapter 06, we did four jobs. 

1. Implement logger class, not only for logging convenience, but also for AI code to fix bugs easily.

2. Implement camera and renderer classes, to control the movement of camera in addition to lens and other functionalities,
   to control the rendering process in which we always rendering animation frames into images,
   and then assemble those images into a MP4 video.

3. Implement animation, keyframe, and constraint classes.

4. Modify rocky_river_terrain class to make a case for the complex movement of camera in a complex scene. 


&nbsp;
## 2. System Architecture

Following is the library framework, under rapid development. 

In each file directory, we will add many more python scripts. 

~~~
$ cd /home/robot
$ tree movie_blender_studio/
movie_blender_studio/
├── dot.env -> .env

├── __init__.py
├── main.py

├── logger
│   ├── __init__.py
│   └── logger.py

├── camera
│   ├── __init__.py
│   ├── camera.py
│   └── renderer.py

├── animation
│   ├── __init__.py
│   ├── animation.py
│   ├── keyframe.py
│   └── constraint.py

├── hdri
│   ├── __init__.py
│   ├── hdri_background.py
│   └── dome_with_hdri_and_sun_generator.py

├── scene
│   ├── __init__.py
│   └── rocky_river_terrain.py

├── model
│   ├── __init__.py
│   ├── riverbed_generator.py
│   ├── rock_generator.py
│   └── water_generator.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── curve_generator.py

├── shader_modifier
│   ├── __init__.py
│   ├── apply_texture_asset.py
│   ├── modifier_generator.py
│   └── shader_generator.py

├── sys_config
│   ├── __init__.py 
│   └── import_in_blender.py
~~~


&nbsp;
## 3. Run demos

To run the demo, do the following

~~~
$ cd /home/robot/movie_blender_studio/

# To verify there is no error.
$ python3 main.py

# To see the demo in the Blender 3D software
$ blender --python main.py
~~~

&nbsp;
## 4. Demo Video

Click the image to jump to youtube to see our demo.

[![Blender Python Package for AI Cinematography](https://img.youtube.com/vi/egharDlQHZA/hqdefault.jpg)](https://www.youtube.com/watch?v=egharDlQHZA)
