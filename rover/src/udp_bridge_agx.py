#!/usr/bin/env python3
import socket
import json
import threading
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy  # or any control msg

class UdpGatewayAGX(Node):
    def __init__(self):
        super().__init__('udp_gateway_agx')

        self.nano_ip = '10.10.10.1'  # IP of Jetson Nano
        self.send_port = 5005
        self.recv_port = 6006

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(('0.0.0.0', self.recv_port))

        self.create_subscription(Joy, '/joy', self.joy_callback, 10)
        threading.Thread(target=self.recv_loop, daemon=True).start()

    def joy_callback(self, msg):
        packet = {
            "type": "drive_cmd",
            "linear": msg.axes[1],
            "angular": msg.axes[3]
        }
        data = json.dumps(packet).encode()
        self.send_sock.sendto(data, (self.nano_ip, self.send_port))

    def recv_loop(self):
        while True:
            data, _ = self.recv_sock.recvfrom(1024)
            try:
                msg = json.loads(data.decode())
                self.get_logger().info(f"Telemetry: {msg}")
            except Exception as e:
                self.get_logger().warn(f"Error parsing telemetry: {e}")

def main():
    rclpy.init()
    node = UdpGatewayAGX()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
