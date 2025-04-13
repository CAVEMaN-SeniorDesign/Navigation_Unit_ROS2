from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    explore_lite_dir = get_package_share_directory('explore_lite')
    explore_launch_path = os.path.join(explore_lite_dir, 'launch', 'explore.launch.py')

    # Launch the explore_lite node
    explore_lite_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(explore_launch_path)
    )

    # Run the empty_map_service node
    empty_map_service_node = Node(
        package='rover_explore',
        executable='empty_map_service',
        name='empty_map_service',
        output='screen'
    )

    # Call the /publish_empty_map service once after 5 seconds
    call_publish_service = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=['ros2', 'service', 'call', '/publish_empty_map', 'std_srvs/srv/Trigger'],
                shell=True
            )
        ]
    )

    return LaunchDescription([
        explore_lite_launch,
        empty_map_service_node,
        call_publish_service
    ])
