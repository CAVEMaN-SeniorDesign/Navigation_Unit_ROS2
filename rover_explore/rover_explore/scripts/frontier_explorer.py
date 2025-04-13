#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, ReliabilityPolicy
from nav_msgs.msg import OccupancyGrid
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Point
from visualization_msgs.msg import Marker, MarkerArray
import numpy as np
import math
import random
from tf2_ros import TransformListener, Buffer
from scipy.ndimage import binary_dilation
import tf2_geometry_msgs
import time

class FrontierExplorer(Node):
    def __init__(self):
        super().__init__('frontier_explorer')
        
        # Parameters
        self.declare_parameter('min_frontier_size', 10)
        self.declare_parameter('robot_radius', 0.3)
        self.declare_parameter('inflation_radius', 0.5)
        self.declare_parameter('goal_tolerance', 0.5)
        self.declare_parameter('goal_selection_method', 'closest')  # Options: closest, largest, random
        
        self.min_frontier_size = self.get_parameter('min_frontier_size').value
        self.robot_radius = self.get_parameter('robot_radius').value
        self.inflation_radius = self.get_parameter('inflation_radius').value
        self.goal_tolerance = self.get_parameter('goal_tolerance').value
        self.goal_selection_method = self.get_parameter('goal_selection_method').value
        
        # Current map data
        self.map_data = None
        self.map_width = 0
        self.map_height = 0
        self.map_resolution = 0.0
        self.map_origin_x = 0.0
        self.map_origin_y = 0.0
        
        # TF listener for robot position
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Navigation client
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Subscribe to map updates
        qos = QoSProfile(depth=1)
        qos.reliability = ReliabilityPolicy.RELIABLE
        self.map_sub = self.create_subscription(
            OccupancyGrid, 
            'map',
            self.map_callback,
            qos)
            
        # Publishers for visualization
        self.frontier_pub = self.create_publisher(
            MarkerArray,
            'frontier_markers',
            10)
            
        self.goal_pub = self.create_publisher(
            Marker,
            'exploration_goal',
            10)
        
        # Timer for exploration loop
        self.timer = self.create_timer(5.0, self.exploration_loop)
        self.get_logger().info('Frontier explorer initialized')
        
        # State tracking
        self.exploring = False
        self.last_goal = None
        self.frontiers = []
        
    def map_callback(self, msg):
        """Process incoming map messages."""
        self.map_data = np.array(msg.data).reshape((msg.info.height, msg.info.width))
        self.map_width = msg.info.width
        self.map_height = msg.info.height
        self.map_resolution = msg.info.resolution
        self.map_origin_x = msg.info.origin.position.x
        self.map_origin_y = msg.info.origin.position.y
        self.map_frame = msg.header.frame_id
        
        self.get_logger().debug(f'Received map: {self.map_width}x{self.map_height} at {self.map_resolution}m/cell')

    def get_robot_position(self):
        """Get the current robot position in the map frame."""
        try:
            transform = self.tf_buffer.lookup_transform(
                self.map_frame,
                'base_link',
                rclpy.time.Time())
                
            robot_x = transform.transform.translation.x
            robot_y = transform.transform.translation.y
            
            # Convert to grid coordinates
            grid_x = int((robot_x - self.map_origin_x) / self.map_resolution)
            grid_y = int((robot_y - self.map_origin_y) / self.map_resolution)
            
            return grid_x, grid_y, robot_x, robot_y
        except Exception as e:
            self.get_logger().error(f'Failed to get robot position: {e}')
            return None, None, None, None

    def is_navigating(self):
        """Check if we're currently navigating to a goal."""
        return self.exploring and not self._nav_client.wait_for_server(timeout_sec=0.1)

    def find_frontiers(self):
        """Find frontiers in the current map."""
        if self.map_data is None:
            self.get_logger().warn('No map data available')
            return []
            
        # Create binary map: 0 = free, 1 = occupied/unknown
        free_space = (self.map_data == 0).astype(np.uint8)
        
        # Create binary map of unknown space
        unknown_space = (self.map_data == -1).astype(np.uint8)
        
        # Dilate obstacles for safety
        occupied_space = (self.map_data > 50).astype(np.uint8)
        inflation_cells = int(self.inflation_radius / self.map_resolution)
        inflated_obstacles = binary_dilation(occupied_space, iterations=inflation_cells)
        
        # Frontiers are at the boundary of free and unknown space
        frontiers = np.zeros_like(free_space)
        
        # For each free cell, check if it borders an unknown cell
        for i in range(1, self.map_height - 1):
            for j in range(1, self.map_width - 1):
                if free_space[i, j] and not inflated_obstacles[i, j]:
                    # Check 8-connected neighbors
                    if (unknown_space[i-1:i+2, j-1:j+2]).any():
                        frontiers[i, j] = 1
        
        # Extract frontier clusters
        frontier_clusters = []
        visited = np.zeros_like(frontiers)
        
        for i in range(self.map_height):
            for j in range(self.map_width):
                if frontiers[i, j] and not visited[i, j]:
                    # Found a new frontier point, start a new cluster
                    cluster = []
                    queue = [(i, j)]
                    visited[i, j] = 1
                    
                    while queue:
                        y, x = queue.pop(0)
                        cluster.append((y, x))
                        
                        # Check 8-connected neighbors
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                ny, nx = y + dy, x + dx
                                if (0 <= ny < self.map_height and 
                                    0 <= nx < self.map_width and 
                                    frontiers[ny, nx] and 
                                    not visited[ny, nx]):
                                    queue.append((ny, nx))
                                    visited[ny, nx] = 1
                    
                    if len(cluster) >= self.min_frontier_size:
                        frontier_clusters.append(cluster)
        
        self.get_logger().info(f'Found {len(frontier_clusters)} frontiers')
        self.frontiers = frontier_clusters
        self.visualize_frontiers(frontier_clusters)
        return frontier_clusters

    def visualize_frontiers(self, frontier_clusters):
        """Visualize frontiers for debugging."""
        marker_array = MarkerArray()
        
        for i, cluster in enumerate(frontier_clusters):
            marker = Marker()
            marker.header.frame_id = self.map_frame
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "frontiers"
            marker.id = i
            marker.type = Marker.POINTS
            marker.action = Marker.ADD
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.1
            marker.scale.y = 0.1
            marker.color.r = 1.0
            marker.color.g = 0.5
            marker.color.b = 0.0
            marker.color.a = 1.0
            
            for cell in cluster:
                p = Point()
                # Convert grid coordinates to world coordinates
                p.x = self.map_origin_x + cell[1] * self.map_resolution
                p.y = self.map_origin_y + cell[0] * self.map_resolution
                p.z = 0.0
                marker.points.append(p)
                
            marker_array.markers.append(marker)
            
        self.frontier_pub.publish(marker_array)

    def select_frontier_goal(self, frontiers):
        """Select a frontier to explore next."""
        if not frontiers:
            return None
            
        grid_x, grid_y, robot_x, robot_y = self.get_robot_position()
        if grid_x is None:
            return None
            
        method = self.goal_selection_method
        
        if method == 'random':
            # Choose a random frontier
            frontier = random.choice(frontiers)
            
        elif method == 'largest':
            # Choose the largest frontier
            frontier = max(frontiers, key=len)
            
        else:  # Default to 'closest'
            # Choose the closest frontier
            closest_frontier = None
            min_distance = float('inf')
            
            for frontier in frontiers:
                # Calculate center of frontier
                center_y = sum(p[0] for p in frontier) / len(frontier)
                center_x = sum(p[1] for p in frontier) / len(frontier)
                
                # Calculate distance to robot
                distance = math.sqrt((center_y - grid_y)**2 + (center_x - grid_x)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    closest_frontier = frontier
                    
            frontier = closest_frontier
        
        # Calculate center of the selected frontier
        center_y = sum(p[0] for p in frontier) / len(frontier)
        center_x = sum(p[1] for p in frontier) / len(frontier)
        
        # Convert to world coordinates
        world_x = self.map_origin_x + center_x * self.map_resolution
        world_y = self.map_origin_y + center_y * self.map_resolution
        
        # Visualize the goal
        self.visualize_goal(world_x, world_y)
        
        return (world_x, world_y)

    def visualize_goal(self, x, y):
        """Visualize the current exploration goal."""
        marker = Marker()
        marker.header.frame_id = self.map_frame
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "goal"
        marker.id = 0
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x = x
        marker.pose.position.y = y
        marker.pose.position.z = 0.1
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.3
        marker.scale.y = 0.3
        marker.scale.z = 0.3
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0
        marker.color.a = 1.0
        
        self.goal_pub.publish(marker)

    def send_goal(self, x, y):
        """Send a navigation goal to Nav2."""
        self.get_logger().info(f'Sending goal: ({x:.2f}, {y:.2f})')
        
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = self.map_frame
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.w = 1.0
        
        self._nav_client.wait_for_server()
        send_goal_future = self._nav_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)
        
        self.exploring = True
        self.last_goal = (x, y)

    def goal_response_callback(self, future):
        """Handle the goal response."""
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            self.exploring = False
            return
            
        self.get_logger().info('Goal accepted')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        """Handle the navigation result."""
        result = future.result().result
        status = future.result().status
        
        if status == 4:  # Succeeded
            self.get_logger().info('Goal succeeded!')
        else:
            self.get_logger().info(f'Goal failed with status: {status}')
            
        self.exploring = False

    def exploration_loop(self):
        """Main exploration loop."""
        # Skip if no map yet
        if self.map_data is None:
            self.get_logger().warn('Waiting for map data...')
            return
            
        # Skip if currently navigating
        if self.is_navigating():
            self.get_logger().debug('Still navigating to previous goal...')
            return
            
        # Find frontiers
        frontiers = self.find_frontiers()
        
        if not frontiers:
            self.get_logger().info('No frontiers found, exploration complete!')
            return
            
        # Select and navigate to a frontier
        goal = self.select_frontier_goal(frontiers)
        
        if goal:
            # Don't resend the same goal
            if self.last_goal and math.sqrt((goal[0] - self.last_goal[0])**2 + 
                                           (goal[1] - self.last_goal[1])**2) < self.goal_tolerance:
                self.get_logger().info('Skipping similar goal')
                return
                
            self.send_goal(goal[0], goal[1])

def main(args=None):
    rclpy.init(args=args)
    explorer = FrontierExplorer()
    
    try:
        rclpy.spin(explorer)
    except KeyboardInterrupt:
        pass
    finally:
        explorer.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()