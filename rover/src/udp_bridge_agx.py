#!/usr/bin/env python3
import socket
import json
import threading
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from std_msgs.msg import Header
from rover_interfaces.msg import Encoders, Airquality

class UdpGatewayAGX(Node):
    def __init__(self):
        super().__init__('udp_gateway_agx')

        self.nano_ip = '10.10.10.1'  # IP of Jetson Nano, as of 4/16/24, is 10.10.10.1
        self.send_port = 5005
        self.recv_port = 6006

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(('0.0.0.0', self.recv_port))

        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        threading.Thread(target=self.recv_loop, daemon=True).start()
        
        self.imu_pub = self.create_publisher(Imu, '/imu/data', 10)
        self.encoder_pub = self.create_publisher(Encoders, '/encoders', 10)
        self.airquality_pub = self.create_publisher(Airquality, '/airquality', 10)

    def cmd_vel_callback(self, msg):
        packet = {
            "type": "drive_cmd",
            "linear": msg.linear.x,
            "angular": msg.angular.z
        }
        data = json.dumps(packet).encode()
        self.send_sock.sendto(data, (self.nano_ip, self.send_port))

    def recv_loop(self):
        while True:
            data, _ = self.recv_sock.recvfrom(1024)
            try:
                msg = json.loads(data.decode())
                msg_type = msg.get("type")
                if msg_type == "imu":
                    self.get_logger().info(f"IMU data: {msg['orientation']}")
                    self.publish_imu(msg)

                elif msg_type == "encoder":
                    self.get_logger().info(f"Encoder pulses: {msg['wheel_0']['pulses']}")
                    self.publish_encoders(msg)

                elif msg_type == "airquality":
                    self.get_logger().info(f"Dust: {msg['dust']} ug/m3, Gas: {msg['gas']} ppm, Temp: {msg['temp']} °C")
                    self.publish_airquality(msg)
                else:
                    self.get_logger().warn(f"Unknown message type: {msg_type}")
            except Exception as e:
                self.get_logger().warn(f"Error parsing messages from Jetson Nano: {e}")

def main():
    rclpy.init()
    node = UdpGatewayAGX()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
