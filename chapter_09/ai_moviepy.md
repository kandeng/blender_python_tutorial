# Integrate AI models and Moviepy to Blender

## 1. Objectives

In chapter 09, we integrate AI models and Moviepy with Blender. 
Specifically, 

1. Replace Blender's video sequencer editor (VSE) with Moviepy.

   Because Moviepy is more pythonic and easier to use.  

2. Use AI models for compositing jobs.

   For the time being, we use the AI image/video models on the Alibaba Cloud Bailian platform.


&nbsp;
## 2. Moviepy

To make it easy to use Moviepy, we implement `movie/movie_editor.py` to provide following functions, 

1. video file to image sequence, and vice versa.

2. subclip to take a segment from a full-length video file.

3. concatenate a sequence of video files into one MP4 video file.

4. convert a colorful video file to be a black-and-white MP4 video file.

5. overlay subtitle text and image onto a video file.

   To write text to video, you need to download fonts.

   We download the English/Chinese font ttf files from https://fonts.google.com/noto/fonts


&nbsp;
## 3. Qwen AI model

### 3.1 Installation 

~~~
$ /home/robot/blender-4.4.3-linux-x64/4.4/python/bin/python3.11 -m pip install dashscope

$ /home/robot/blender-4.4.3-linux-x64/4.4/python/bin/python3.11 -m pip show dashscope
Name: dashscope
Version: 1.24.6
Summary: dashscope client sdk library
Home-page: https://dashscope.aliyun.com/
Author: Alibaba Cloud
Author-email: dashscope@alibabacloud.com
License: Apache 2.0
Location: /home/robot/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/site-packages
Requires: aiohttp, certifi, cryptography, requests, websocket-client
Required-by:

$ /home/robot/blender-4.4.3-linux-x64/4.4/python/bin/python3.11 -m pip install asyncio

$ /home/robot/blender-4.4.3-linux-x64/4.4/python/bin/python3.11 -m pip show asyncio
Name: asyncio
Version: 4.0.0
Summary: Deprecated backport of asyncio; use the stdlib package instead
Home-page: 
Author: 
Author-email: 
License: 
Location: /home/robot/blender-4.4.3-linux-x64/4.4/python/lib/python3.11/site-packages
Requires: 
Required-by: 
~~~
