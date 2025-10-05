# Green Screen, OpenCV and MoviePy

## 1. Objectives

In chapter 08, we start to combine 
[OpenCV-python](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html) and 
[Moviepy](https://zulko.github.io/moviepy/) with Blender python. 

Later, we will combine the state-of-art AI models with Blender python. 

Specifically, in this chapter, 

1. We will use Blender python to implement green screen,
   to extract the human subject and their motion from the green screen background video footage.

2. Given another video footage, like the scene of Seine river in Paris,
   we use OpenCV-python to inverse calculate the motion of camera, especially its pan and tilt.

3. Given the time series of camera motion, we use OpenCV-python to process the human subject motion video footage,
   to make the human motion aligned with the scene video footage's pan and tilt. 

4. Use Moviepy, instead of Blender's video editor functionality, to merge the human motion video footage
   with the scene background video. 


&nbsp;
## 2. Blender, OpenCV and MoviePy

