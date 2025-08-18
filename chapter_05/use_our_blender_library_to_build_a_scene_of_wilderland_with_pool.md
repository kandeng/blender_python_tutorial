# A Demo Video made by our Blender python library

## 1. Objectives

There are two objectives for chapter 05. 

1. Continue to develop our Blender python library for video-making.

2. Build a video-making scene set, in this case it is a wilderland with a pool, to verifying our library's functionality and easy-to-use.


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

├── camera_light

├── scene
│   ├── __init__.py
│   └── rocky_river_terrain.py

├── hdri
│   ├── __init__.py
│   └── dome_with_hdri_and_sun_generator.py

├── model
│   ├── __init__.py
│   ├── riverbed_generator.py
│   ├── rock_generator.py
│   └── water_generator.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── curve_generator.py

├── shader_modifier
│   ├── __init__.py
│   ├── apply_texture_asset.py
│   ├── modifier_generator.py
│   └── shader_generator.py

└── sys_config
    ├── import_in_blender.py
    └── __init__.py
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

[![Blender HDRI python package](https://img.youtube.com/vi/MhH08Um4Nd4/hqdefault.jpg)](https://www.youtube.com/watch?v=MhH08Um4Nd4)

