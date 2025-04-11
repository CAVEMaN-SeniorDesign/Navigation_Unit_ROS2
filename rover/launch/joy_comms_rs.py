from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    joy_params = os.path.join(get_package_share_directory('rover'),'config','xbox.yaml')

    ros_distro = os.environ.get('ROS_DISTRO')
    joy_package = 'joy'
    joy_node = 'joy_node'
    
    if ros_distro and ros_distro == "humble":
        print(f"ROS 2 distribution: {ros_distro}")
        joy_package = "joy_linux"
        joy_node = "joy_linux_node"
    elif ros_distro:
        print("ROS_DISTRO not humble, good to use joy_node")
    else:
        print("ROS_DISTRO environment variable not set.")

    joy_node = Node(
            package=joy_package,
            executable=joy_node,
            parameters=[joy_params, {'use_sim_time': use_sim_time}],
            output="screen",
            arguments=['--ros-args', '--log-level', 'info']
         )
    
    UARTcomms = Node(
            package='rover_comms',
            executable='rover_comms',
            name='comms_node',
            arguments=[],
            output="screen"
    )
    
    RealSense = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("realsense2_camera"), 
                'launch', 
                'rs_launch.py'
            )
        ]),
        launch_arguments={
            'use_sim_time': 'true',
            'rgb_camera.color_profile': '1280x720x30',
            'depth_module.depth_profile': '640x480x30'
        }.items()
    )
    
    PavelRS = Node(
            package='ros2_realsense',
            executable='convert_image_raw',
            name='pavel_node',
                arguments=[
                    '--ros-args',
                    '-p', 'topic_color:=/camera/camera/color/image_raw',
                    '-p', 'topic_depth:=/camera/camera/depth/image_rect_raw'
                ],
            output="screen"
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),
        
        joy_node,
        UARTcomms,
        RealSense,
        PavelRS,
    ])
