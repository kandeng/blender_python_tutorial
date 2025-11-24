# A game for scene building and video making 


## 1. Objectives

So far we have made good progress in developing Blender python package. 

Not only does this package make Blender python programming much easier, 
but also it integrates OpenCV and AI models into Blender seamlessly. 

It is time to design the product and discuss the business model.

We propose to use this Blender python package to develop a game, 
a multiplayer cross-platform simulation/strategy game for scene building and video making. 

We use game's UI and business model to make scene-building and video-making easier and more fun. 


&nbsp;
## 2. Product design

### 2.1 Client side

The client-side application is developed in [Unity](https://unity.com/), 
primarily for its small app size and cross-platform compatibility across mobile phones and PCs.

The UI of the client side is similar to those city/empire building strategy games UI, 
e.g. "[Forge of empires](https://en-play.forgeofempires.com)", "[The Sims](https://www.ea.com/zh-cn/games/the-sims)". 

The game UI consists of the following parts，

1. Asset panel 

    The asset panel is for 3D asset objects, it consists of multiple categories, including "landscape", "building", "machine", "human", "animal", "plant" etc.

    Each category is a cascade-down menu, when expanding the menu, it will show the preview thumbnail of each 3D asset.

2. Scene panel

    The scene panel has the largest area. It is a 3D editing canvas.

    The player can drag and drop the 3D assets from the asset panel to the scene panel, i.e. the 3D editing canvas.
   
    The user can rotate the viewport of the 3D canvas, zoom in and out.

3. Control panel

    After the player clicks on one of the 3D object in the scene panel, he can move it, rotate it, scale it.

    Also, the player can set multiplelighting sources, change their orientation and strength, and plan the movement path of the camera. 
  
4. Preview panel

    After completing the scene building and the lighting setting and the camera movement planning, it is time to preview the video in the preview panel. 
  
    The quality of the preview video is of low-fidelity. The player can click the "rendering" button to remotely control the background GPU-empowered Blender cycles rendering engine, to generate high-fidelity .mp4 video.

   <p align="center" vertical-align="top">
     <img alt="The outlook of the client side UI, similar to a city-building game" src="../asset/virtual_studio.png" width="80%">
   </p> 
