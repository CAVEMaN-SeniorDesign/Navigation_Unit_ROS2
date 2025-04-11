# Requirements:
#   A realsense D435i
#   Install realsense2 ros2 package (ros-$ROS_DISTRO-realsense2-camera)
# Example:
#   $ ros2 launch realsense2_camera rs_launch.py enable_sync:=true
#
#   $ ros2 launch rtabmap_examples realsense_d435_color.launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    realsense_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('realsense2_camera'),
                "launch",
                "rs_launch.py"
            )
        ),
        launch_arguments={
            'color_width': '1280',
            'color_height': '720',
            'color_fps': '30.0',
            'depth_width': '640',
            'depth_height': '480',
            'depth_fps': '30.0',
            'enable_sync': 'true',
            'align_depth': 'true',
        }.items()
    )
    
    parameters=[{
          'frame_id':'camera_link',
          'subscribe_depth':True,
          'subscribe_odom_info':True,
          'approx_sync':False,
          'wait_imu_to_init':False}]

    remappings=[
          ('rgb/image', '/camera/camera/color/image_raw'),
          ('rgb/camera_info', '/camera/camera/color/camera_info'),
          ('depth/image', '/camera/camera/realigned_depth_to_color/image_raw')]

    return LaunchDescription([
        realsense_launch,
        
        Node(
            package='rtabmap_odom', executable='rgbd_odometry', output='screen',
            parameters=parameters,
            remappings=remappings),

        Node(
            package='rtabmap_slam', executable='rtabmap', output='screen',
            parameters=parameters,
            remappings=remappings,
            arguments=['-d']),

        Node(
            package='rtabmap_viz', executable='rtabmap_viz', output='screen',
            parameters=parameters,
            remappings=remappings),
        
        # Because of this issue: https://github.com/IntelRealSense/realsense-ros/issues/2564
        # Generate point cloud from not aligned depth
        Node(
            package='rtabmap_util', executable='point_cloud_xyz', output='screen',
            parameters=[{'approx_sync':False}],
            remappings=[('depth/image',       '/camera/camera/depth/image_rect_raw'),
                        ('depth/camera_info', '/camera/camera/depth/camera_info'),
                        ('cloud',             '/camera/camera/cloud_from_depth')]),
        
        # Generate aligned depth to color camera from the point cloud above       
        Node(
            package='rtabmap_util', executable='pointcloud_to_depthimage', output='screen',
            parameters=[{ 'decimation':2,
                          'fixed_frame_id':'camera_link',
                          'fill_holes_size':1}],
            remappings=[('camera_info', '/camera/camera/color/camera_info'),
                        ('cloud',       '/camera/camera/cloud_from_depth'),
                        ('image_raw',   '/camera/camera/realigned_depth_to_color/image_raw')]),
        
    ])
    
'''
Working realsense launch commands: 
ros2 launch realsense2_camera rs_launch.py 
    depth_width:=640 \ 
    depth_height:=480 \ 
    depth_fps:=30.0 \ 
    infra_width:=640 \ 
    infra_height:=480 \
    infra_fps:=30.0 \ 
    infra_rgb:=true \ 
    enable_sync:=true \
    align_depth:=true 
    
# current best working
ros2 launch realsense2_camera rs_launch.py \
  color_width:=1280 color_height:=720 color_fps:=30.0 \
  depth_width:=640 depth_height:=480 depth_fps:=30.0 \
  enable_sync:=true align_depth:=true

# current best working
ros2 launch realsense2_camera rs_launch.py \
  color_width:=1280 color_height:=720 color_fps:=30.0 \
  depth_width:=1280 depth_height:=720 depth_fps:=30.0 \
  enable_sync:=true align_depth:=true

Not working ones:
ros2 launch realsense2_camera rs_launch.py rgb_camera.color_profile:=1280x720x30 depth_module.depth_profile:=640x480x30
ros2 launch realsense2_camera rs_launch.py rgb_camera.color_profile:=1280x720x30 depth_module.depth_profile:=640x480x30 pointcloud.enable:=true enable_sync:=true align_depth:=true 
'''