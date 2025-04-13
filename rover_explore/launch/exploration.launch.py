from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        # Parameters
        DeclareLaunchArgument(
            'min_frontier_size',
            default_value='10',
            description='Minimum number of cells to consider a frontier'),
            
        DeclareLaunchArgument(
            'robot_radius',
            default_value='0.3',
            description='Robot radius in meters'),
            
        DeclareLaunchArgument(
            'inflation_radius',
            default_value='0.5',
            description='Safety inflation around obstacles'),
            
        DeclareLaunchArgument(
            'goal_selection_method',
            default_value='closest',
            description='Method to select frontiers (closest, largest, random)'),
            
        # Frontier explorer node
        Node(
            package='rover_explore',  # Replace with your package name
            executable='frontier_explorer',
            name='frontier_explorer',
            output='screen',
            parameters=[{
                'min_frontier_size': LaunchConfiguration('min_frontier_size'),
                'robot_radius': LaunchConfiguration('robot_radius'),
                'inflation_radius': LaunchConfiguration('inflation_radius'),
                'goal_selection_method': LaunchConfiguration('goal_selection_method'),
            }],
        ),
    ])