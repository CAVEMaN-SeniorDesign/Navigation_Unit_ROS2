from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

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

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),
        joy_node,
        # twist_stamper       
    ])
