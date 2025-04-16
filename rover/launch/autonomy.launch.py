from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    
    package_description = "rover_description"
    print("Fetching URDF ==>")
    urdf_file = os.path.join(get_package_share_directory(package_description), 'rover_desc', 'rover.xacro')    #xacro_file = "urdfbot.xacro"

    use_sim_time = LaunchConfiguration('use_sim_time')

    joy_params = os.path.join(get_package_share_directory('rover'),'config','xbox.yaml')
    MAIN_EKF_PARAMS = os.path.join(get_package_share_directory("rover"), 'config', 'only_imu_ekf.yaml')

    VO_only_params = os.path.join(get_package_share_directory("rover"), 'config', 'only_VO.yaml')
    VIO_params = os.path.join(get_package_share_directory("rover"), 'config', 'only_VIO.yaml')

    MAIN_EKF_PARAMS = VO_only_params

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
    
    rs_and_rtabmap = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("rover"), 
                'launch', 
                'rtabmap.launch.py'
            )
        ]),
        launch_arguments={
        }.items()
    )

    EKF_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[MAIN_EKF_PARAMS],
    )
    
    Nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory("rover"), 
                'launch', 
                'nav2.launch.py'
            )
        ]),
        launch_arguments={
        }.items()
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),
        robot_state_publisher_node,
        joint_state_publisher_node,
        rs_and_rtabmap,
        EKF_node,
        Nav2
    ])
