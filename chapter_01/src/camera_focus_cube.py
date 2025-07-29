import bpy
import math
import os

def setup_render_settings(output_path):
    """设置渲染参数以输出MP4视频"""
    scene = bpy.context.scene
    
    # 设置渲染引擎
    # scene.render.engine = 'BLENDER_EEVEE_NEXT'  # When running in Blender/scripts, needs this. 
    scene.render.engine = 'BLENDER_EEVEE'   # When running in terminal, use this. 
    scene.eevee.taa_render_samples = 64  # 抗锯齿采样
    
    # 设置帧率和帧范围
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 100
    
    # 设置输出路径和格式
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'  # 高质量
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'  # 编码预设
    
    # 设置分辨率
    scene.render.resolution_x = 640  # 1280
    scene.render.resolution_y = 480  # 720
    scene.render.resolution_percentage = 100
    
    # 设置其他渲染选项
    scene.render.use_motion_blur = False  # 可选：关闭运动模糊以提高渲染速度

def update_camera_position_and_render():
    """控制相机移动并渲染视频"""
    # 确保有一个立方体在原点
    if "Cube" not in bpy.data.objects:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
    cube = bpy.data.objects["Cube"]

    # 确保有一个相机
    camera_start_position = (-10, -5, 3)
    if "Camera" not in bpy.data.objects:
        bpy.ops.object.camera_add(location=camera_start_position)
    camera = bpy.data.objects["Camera"]
    
    # 设置相机位置
    camera.location = camera_start_position

    # 设置相机为活动相机
    bpy.context.scene.camera = camera

    # 设置关键帧动画
    total_frames = 100
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = total_frames

    # 清除相机上的所有关键帧
    camera.animation_data_clear()

    # 相机起始和结束位置
    start_pos = (-10, -5, 3)
    end_pos = (10, 5, 3)

    # 创建一个空对象作为跟踪目标
    if "Target" not in bpy.data.objects:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        # 获取新创建的空对象并命名
        target = bpy.context.active_object
        target.name = "Target"
    else:
        target = bpy.data.objects["Target"]

    # 为相机添加跟踪约束
    if not camera.constraints.get("Track To"):
        track_to = camera.constraints.new(type='TRACK_TO')
        track_to.target = target
        track_to.track_axis = 'TRACK_NEGATIVE_Z'
        track_to.up_axis = 'UP_Y'

    # 设置当前帧为1
    bpy.context.scene.frame_set(1)
    
    # 设置相机位置的关键帧
    for frame in range(1, total_frames + 1):
        # 计算当前帧的位置（线性插值）
        t = frame / total_frames
        x = start_pos[0] + t * (end_pos[0] - start_pos[0])
        # y = start_pos[1] + t * (end_pos[1] - start_pos[1])
        y = start_pos[1]  # Y 坐标保持不变
        z = start_pos[2]  # Z 坐标保持不变
        print(f"设置第 {frame} 帧的相机位置: ({x:.2f}, {y:.2f}, {z:.2f})")
        
        # 设置相机位置
        camera.location = (x, y, z)
        
        # 设置关键帧
        camera.keyframe_insert(data_path="location", frame=frame)
        
        # 更新当前帧和视口显示
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()

    # 设置输出目录和文件名
    output_dir = os.path.expanduser("./blender_animations")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "camera_movement.mp4")
    
    # 设置渲染参数
    setup_render_settings(output_file)
    
    # 执行渲染
    print("开始渲染动画视频...")
    bpy.ops.render.render("INVOKE_DEFAULT", animation=True)
    print(f"渲染完成！视频已保存到: {output_file}")

# Execute the function
if __name__ == "__main__":
    update_camera_position_and_render()