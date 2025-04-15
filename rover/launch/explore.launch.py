from launch_ros.actions import Node
from launch import LaunchDescription

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='explore_lite',
            executable='explore',
            name='explore_node',
            output='screen',
            parameters=[{
                'planner_frequency': 1.0,
                'min_frontier_size': 0.1,
                'visualize': True,
                'return_to_init': False,
            }],
        ),
    ])
