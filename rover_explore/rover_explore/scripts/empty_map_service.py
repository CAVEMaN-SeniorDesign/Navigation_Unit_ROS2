import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from std_msgs.msg import Header
from geometry_msgs.msg import Pose
from std_srvs.srv import Trigger

class EmptyMapPublisherService(Node):
    def __init__(self):
        super().__init__('empty_map_service_node')

        self.map_pub = self.create_publisher(OccupancyGrid, '/map', 10)
        self.srv = self.create_service(Trigger, 'publish_empty_map', self.handle_publish)

        self.get_logger().info("Ready to publish empty map on request.")

    def handle_publish(self, request, response):
        msg = OccupancyGrid()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'

        msg.info.resolution = 0.05  # 5 cm
        msg.info.width = 100
        msg.info.height = 100
        msg.info.origin = Pose()

        msg.data = [-1] * (msg.info.width * msg.info.height)
        self.map_pub.publish(msg)

        self.get_logger().info('Published empty map on service request.')
        response.success = True
        response.message = "Empty map published to /map."
        return response

def main(args=None):
    rclpy.init(args=args)
    node = EmptyMapPublisherService()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    rclpy.shutdown()

if __name__ == '__main__':
    main()
