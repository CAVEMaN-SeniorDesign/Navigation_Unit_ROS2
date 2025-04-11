from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    nav2_params = os.path.join(get_package_share_directory("rover"), 'config', 'nav2_params.yaml')

    # Nav2 = Node(
    #     package='nav2_bringup',
    #     executable='bringup_launch.py',
    #     output='screen',
    #     parameters=[nav2_params],
    #     arguments=['--ros-args', '--params-file', nav2_params]
    # )
    
    Nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("nav2_bringup"), 
                'launch', 
                'navigation_launch.py'
            )
        ]),
        launch_arguments={
            'params_file': nav2_params,
            'use_sim_time': use_sim_time,
            'autostart': autostart
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock, such as Gazebo, if true'),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='Automatically start navigation'),
        Nav2
    ])

    
