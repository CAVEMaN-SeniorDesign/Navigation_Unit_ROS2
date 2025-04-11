#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import numpy as np
from builtin_interfaces.msg import Time
from geometry_msgs.msg import Quaternion

class FakeIMUPublisher(Node):
    def __init__(self):
        super().__init__('fake_imu_publisher')
        self.publisher_ = self.create_publisher(Imu, 'imu_raw', 10)
        self.timer = self.create_timer(0.02, self.publish_imu)  # 50Hz

    def publish_imu(self):
        imu_msg = Imu()

        # Simulated small noise for a stationary IMU
        imu_msg.linear_acceleration.x = np.random.normal(0.0, 0.02)
        imu_msg.linear_acceleration.y = np.random.normal(0.0, 0.02)
        imu_msg.linear_acceleration.z = np.random.normal(0.0, 0.02)

        imu_msg.angular_velocity.x = np.random.normal(0.0, 0.001)
        imu_msg.angular_velocity.y = np.random.normal(0.0, 0.001)
        imu_msg.angular_velocity.z = np.random.normal(0.0, 0.001)

        # Simulate an identity quaternion (no rotation)
        imu_msg.orientation = Quaternion(w=1.0, x=0.0, y=0.0, z=0.0)

        self.publisher_.publish(imu_msg)
        self.get_logger().info('Publishing fake IMU data')

def main(args=None):
    rclpy.init(args=args)
    node = FakeIMUPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
