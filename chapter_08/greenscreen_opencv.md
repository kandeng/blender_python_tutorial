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

We plan to combine Blender python with OpenCV and MoviePy. 

1. OpenCV 

   We will use OpenCV python to load the video and do image enhancement,
   including cropping, stabilization, denoising and color adjustment.
   
   In addition, we will use OpenCV to do feature tracking, or more advanced PnP/Homography solving
   to calculate a relative camera transformation matrix per frame.

   Also we will use OpenCV to do object detection or background subtraction
   to generate per-frame masks (e.g., identifying a green screen, or isolating a tracked object)
   to assist in rendering or compositing later.

2. MoviePy
   
   MoviePy and Blender's Video Sequence Editor (VSE) share a lot of features,
   but MoviePy is more convenient to work with.
   Therefore, we intend to use MoviePy to replace the VSE in our pipeline.

   Especially, we will use MoviePy to load various media files,
   including the video footage of various formats, and image sequence,
   in addition to audio and textual caption for the video. 

   Also, we will use Moviedy To clip a segment from a video, audio. 

   And finally, we will use MoviePy to assemble multiple layers of media together
   to deliver the final video file. 

3. Blender

   Blender is good at modeling that create a virtual object and scene of the real world, including landscape, city and indoor environment.
   Furthermore, there are a lot of tools or even completed 3D assets available on market, that will save a lot of development human cost.

   Blender is also good at 3D animation adhering to the physics laws.

   Blender excels at implementing visual effects (VFX), including fire, massive waves, explosions, avalanches, and building collapse.

   In addition, there are many Blender material assets available on the market, including wood, metal, and plastic etc.

   For image and video enhancement, Blender features numerous compositing add-ons
   that can significantly enhance the quality of videos and images, giving them a cinematic look.
