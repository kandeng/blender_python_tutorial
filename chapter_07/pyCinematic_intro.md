# Introduction to pyCinematic

## 1. Objectives

In chapter 07, we did four jobs. 

1. Implement compositing classes, especially cinematic_compositor.py.
   This is the first try to implement virtual cinematography based on Blender.

2. Implement video sequence editing classes, for video, audio, image, and text sequence editing.
   This is similar to [github.com/Zulko/moviepy](https://github.com/Zulko/moviepy), but based on Blender.
   
   We should learn from `moviepy` for its simple APIs. 

3. Intensively modify renderer.py, especially implement the setting for image, audio, and video.


&nbsp;
## 2. System Architecture

Following is the file structure of the scripts. 

We tried to bridge `video`(the wrapper of the functions of video sequence editor, VSE) and `compositing` (the wrapper of compositing editor), 
back and forth, but failed. 

For the time being, the solution is that,

1. Upload video, and image files from disk to `compositing`,
   do the cinematic processing, using the various compositors.

2. From `compositing`, render the video that has been processed, into a disk video file.

3. Upload the processed video file, in addition to audio file, text file, etc. to the `video` that is the Blender video sequence editor,
   assemble the multiple media files into a Blender scene, consisting of multiple channels with multiple media sequences.

4. From `video`, render the Blender scene into a disk video file.
   
&nbsp;

However, it may not be a bad idea to separate `compositing` and `video`. 

In term of system architecture and workflow, it is more reliable and less error-proning 
to make `compositing` and `video` as independent sub-systems.  

~~~
$ cd /home/robot/movie_blender_studio
$ tree .
├── dot.env -> .env
├── __init__.py
├── main.py
│     
├── animation
│   ├── __init__.py
│   ├── animation.py
│   ├── keyframe.py
│   └── constraint.py
├── camera
│   ├── __init__.py
│   ├── camera.py
│   └── renderer.py
│     
├── editor
│   ├── __init__.py
│   └── editor_node.py
├── compositing
│   ├── __init__.py
│   ├── video_compositor.py
│   ├── cinematic_compositor.py
│   ├── color_compositor.py
│   ├── image_compositor.py
│   └── image_sequence_compositor.py
├── material
│   ├── __init__.py
│   └── texture_shader.py
│     
├── video
│   ├── __init__.py
│   ├── video_editor.py
│   ├── video_channel.py
│   ├── audio_strip.py
│   ├── image_strip.py
│   └── video_strip.py
│
├── model
│   ├── __init__.py
│   ├── rock_generator.py
│   ├── water_generator.py
│   ├── riverbed_generator.py
│   └── utils
│       ├── __init__.py
│       └── curve_generator.py
├── modifier
│   ├── __init__.py
│   └── modifier_generator.py
├── hdri
│   ├── __init__.py
│   ├── hdri_background.py
│   └── dome_with_hdri_and_sun_generator.py
├── scene
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-311.pyc
│   │   └── rocky_river_terrain.cpython-311.pyc
│   └── rocky_river_terrain.py
│  
├── logger
│   ├── __init__.py
│   └── logger.py
└── sys_config
    ├── import_in_blender.py
    ├── __init__.py
    └── sys_config.env
~~~


&nbsp;
## 3. Cinematography

In [Python For Feature Film](https://www.gfx.dev/python-for-feature-film/) by Dhruv Govil, in October 2020, 
he depicted the workflow using 3D tool like Blender, to make a movie. 

   <p align="center" vertical-align="top">
     <img alt="The workflow to make movie using 3D modeling tool like Blender" src="./asset/blender_for_movie_making.png" width="80%">
   </p>  

This article raises several inspiring points.

1. Our pyCinematic's API should be designed with cinematography in mind, instead of Blender python packages.

2. Our pyCinematic should be an AI agent, to leverage the power of AI models, like [nano-banana](https://aistudio.google.com/models/gemini-2-5-flash-image),
   not just a Python package alternative to [github.com/Zulko/moviepy](https://github.com/Zulko/moviepy).

3. Our pyCinematic should also use 3DGS and other tools, to implement virtual cinematography with better effect.
   

&nbsp;
## 3. Run demos

To run the demo, do the following

~~~
$ cd /home/robot/movie_blender_studio/

# To see the demo in the Blender 3D software
$ blender -q --python main.py

# In case don't want to use the UI, run it in the background mode.
$ blender -q -b --gpu-backend --python main.py
~~~

&nbsp;
## 4. Demo Video

Click the image to jump to youtube to see our demo.

[![pyCinematic introduction and a simple demo](https://img.youtube.com/vi/pCvo3Xj4BwU/hqdefault.jpg)](https://www.youtube.com/watch?v=pCvo3Xj4BwU)

