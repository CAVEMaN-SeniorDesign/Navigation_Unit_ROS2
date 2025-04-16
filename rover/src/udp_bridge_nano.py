#!/usr/bin/env python3
import socket
import json
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class UdpGatewayNano(Node):
    def __init__(self):
        super().__init__('udp_gateway_nano')
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Setup sockets
        self.recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_sock.bind(('0.0.0.0', 5005))

        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.agx_address = ('10.10.10.163', 6006)  # IP of Jetson AGX, as of 4/16/24 is 10.10.10.163

        # Start threads
        threading.Thread(target=self.recv_loop, daemon=True).start()
        threading.Thread(target=self.send_loop, daemon=True).start()

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

    def send_loop(self):
        import time
        while True:
            telemetry = {
                "type": "status",
                "battery": 12.5,
                "dust": 22
            }
            packet = json.dumps(telemetry).encode()
            self.send_sock.sendto(packet, self.agx_address)
            time.sleep(0.5)  

def main():
    rclpy.init()
    node = UdpGatewayNano()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
