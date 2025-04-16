#!/usr/bin/env python3
import time
import socket
import json
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from rover_interfaces.msg import Encoders
from rover_interfaces.msg import Airquality


class UdpGatewayNano(Node):
    def __init__(self):
        super().__init__('udp_gateway_nano')
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Setup sockets
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(('0.0.0.0', 5005))

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.agx_address = ('10.10.10.163', 6006)  # IP of Jetson AGX

        # Start receiving drive commands
        threading.Thread(target=self.recv_loop, daemon=True).start()

        # Subscribe to sensors
        self.create_subscription(Imu, '/imu_raw', self.imu_callback, 10)
        self.create_subscription(Encoders, '/encoders', self.encoder_callback, 10)
        self.create_subscription(Airquality, '/air_quality', self.airquality_callback, 10)

    def recv_loop(self):
        while True:
            data, _ = self.recv_sock.recvfrom(1024)
            try:
                msg = json.loads(data.decode())
                if msg.get('type') == 'drive_cmd':
                    print(f"Received drive command: {msg}")
                    twist = Twist()
                    twist.linear.x = msg.get('linear', 0.0)
                    twist.angular.z = msg.get('angular', 0.0)
                    self.cmd_vel_pub.publish(twist)
            except Exception as e:
                self.get_logger().warn(f"Error parsing UDP msg: {e}")

    def imu_callback(self, msg: Imu):
        payload = {
            "type": "imu",
            "orientation": {
                "x": msg.orientation.x,
                "y": msg.orientation.y,
                "z": msg.orientation.z,
                "w": msg.orientation.w
            },
            "angular_velocity": {
                "x": msg.angular_velocity.x,
                "y": msg.angular_velocity.y,
                "z": msg.angular_velocity.z
            },
            "linear_acceleration": {
                "x": msg.linear_acceleration.x,
                "y": msg.linear_acceleration.y,
                "z": msg.linear_acceleration.z
            }
        }
        self.get_logger().info(f"IMU data sent to AGX")
        self.send_sock.sendto(json.dumps(payload).encode(), self.agx_address)

    def encoder_callback(self, msg):
        payload = {
            "type": "encoder",
            "wheel_0": {
                "pulses": msg.total_pulses_encoder_wheel_0,
                "rate": msg.rate_rads_per_sec_encoder_wheel_0
            },
            "wheel_1": {
                "pulses": msg.total_pulses_encoder_wheel_1,
                "rate": msg.rate_rads_per_sec_encoder_wheel_1
            },
            "wheel_2": {
                "pulses": msg.total_pulses_encoder_wheel_2,
                "rate": msg.rate_rads_per_sec_encoder_wheel_2
            },
            "wheel_3": {
                "pulses": msg.total_pulses_encoder_wheel_3,
                "rate": msg.rate_rads_per_sec_encoder_wheel_3
            }
        }
        self.get_logger().info(f"Encoder data sent to AGX")
        self.send_sock.sendto(json.dumps(payload).encode(), self.agx_address)
        
    def airquality_callback(self, msg: Airquality):
        payload = {
            "type": "airquality",
            "dust": msg.dust_ug_per_m3,
            "gas": msg.gas_ppm,
            "temp": msg.temperature_celsius
        }
        self.get_logger().info(f"AQ data sent to AGX")
        self.send_sock.sendto(json.dumps(payload).encode(), self.agx_address)

def main():
    rclpy.init()
    node = UdpGatewayNano()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
