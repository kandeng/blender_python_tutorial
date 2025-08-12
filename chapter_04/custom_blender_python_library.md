# Custom Blender Python Library

&nbsp;
## 1. Objective

This article describes how to create a custom Blender python library 
that aims at constructing virtual movie studio. 

&nbsp;
## 2. System architecture

~~~
$ cd /home/robot/movie_blender_studio/
$ tree .
.env
├── main.py
├── sys_config
│   ├── __init__.py 
│   └── import_in_blender.py
├── shader_modifier
│   ├── __init__.py
│   ├── apply_texture_asset.py
│   ├── modifier_generator.py
│   └── shader_generator.py
├── hdri
│   ├── __init__.py
│   └── dome_with_hdri_and_sun_generator.py
├── model
│   ├── __init__.py
│   ├── rock_generator.py
│   ├── water_generator.py
│   └── river_terrain_generator.py
├── scene
│   ├── __init__.py
│   └── landscape_with_river.py
├── animation
│   ├── __init__.py
├── camera_light
│   ├── __init__.py
├── video
│   ├── __init__.py
│   └── the_early_morning_landscape_with_river.py
~~~

&nbsp;
## 3. Run demos

~~~
$ cd /home/robot/movie_blender_studio/

$ python3 main.py
$ blender --background --python main.py
~~~

Or, load and run the "main.py" script in the Blender 3D software.

   <p align="center" vertical-align="top">
     <img alt="The sun's 3D coordinate from the point of view inside the dome" src="./asset/sun_3d_coorindate_inside_dome.png" width="48%">
     &nbsp; 
     <img alt="The sun's 3D coordinate from the point of view outside the dome" src="./asset/sun_3d_coordinate_outside_dome.png" width="48%">
   </p>  

&nbsp;
## 4. Demo video

[![Blender HDRI python package](https://img.youtube.com/vi/fFoZTq80alY/hqdefault.jpg)](https://www.youtube.com/watch?v=fFoZTq80alY)
