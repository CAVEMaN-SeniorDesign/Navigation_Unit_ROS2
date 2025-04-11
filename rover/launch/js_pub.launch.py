import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node

# this is the function launch  system will look for
def generate_launch_description():
    package_description = "rover_description"

    print("Fetching URDF ==>")
    #robot_desc_path = os.path.join(get_package_share_directory(package_description), "rover_desc", urdf_file)
    urdf_file = os.path.join(get_package_share_directory(package_description), 'rover_desc', 'rover.xacro')    #xacro_file = "urdfbot.xacro"
    

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        emulate_tty=True,
        parameters=[{'use_sim_time': False, 'robot_description': Command(['xacro ', urdf_file])}],
        output="screen"
    )
    
    #joint state publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{'use_sim_time': False}],
        output="screen"
    )


    # create and return launch description object
    return LaunchDescription(
        [            
            robot_state_publisher_node,
            joint_state_publisher_node
        ]
    )
