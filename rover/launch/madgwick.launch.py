from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    madgwick_params = os.path.join(get_package_share_directory("rover"), 'config', 'madgwick.yaml')

    return LaunchDescription([
        Node(
            package='imu_filter_madgwick',
            executable='imu_filter_madgwick_node',
            name='imu_filter_madgwick_node',
            parameters=[madgwick_params],
            remappings=[
                ('/imu/data_raw', '/imu_raw'),
                ('/imu/data', '/imu/filtered')
            ]
        )
    ])
