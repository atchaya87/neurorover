"""Command mapper node: gesture -> drive command.

Listens:    /gesture  (std_msgs/String, from emg_processor_node)
Publishes:  /cmd_vel  (geometry_msgs/Twist)

Publishes at a steady rate. If no gesture arrives for STALE_AFTER_S seconds,
it sends a stop command, so the rover halts when the EMG side goes quiet.
"""

import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String


PUBLISH_PERIOD_S = 0.05  # 20 Hz
STALE_AFTER_S = 0.5

LINEAR_SPEED = 0.3   # m/s  (placeholder, tune on the real rover)
ANGULAR_SPEED = 1.0  # rad/s

# gesture -> (linear x, angular z). Anything not listed means stop.
GESTURE_TO_VELOCITY = {
    "fist": (LINEAR_SPEED, 0.0),          # forward
    "open": (0.0, 0.0),                   # stop
    "wrist_left": (0.0, ANGULAR_SPEED),   # turn left in place
    "wrist_right": (0.0, -ANGULAR_SPEED), # turn right in place
    "rest": (0.0, 0.0),
}


class CommandMapperNode(Node):
    def __init__(self):
        super().__init__("command_mapper")
        self.gesture = "rest"
        self.last_received = float("-inf")

        self.subscription = self.create_subscription(
            String, "/gesture", self.receive_gesture, 10
        )
        self.publisher = self.create_publisher(Twist, "/cmd_vel", 10)
        self.timer = self.create_timer(PUBLISH_PERIOD_S, self.publish_command)
        self.get_logger().info("Command mapper ready")

    def receive_gesture(self, msg):
        if msg.data not in GESTURE_TO_VELOCITY:
            self.get_logger().warn(f"Unknown gesture '{msg.data}', treating as stop")
        self.gesture = msg.data
        self.last_received = time.monotonic()

    def publish_command(self):
        fresh = time.monotonic() - self.last_received < STALE_AFTER_S
        linear, angular = (
            GESTURE_TO_VELOCITY.get(self.gesture, (0.0, 0.0)) if fresh else (0.0, 0.0)
        )

        cmd = Twist()
        cmd.linear.x = linear
        cmd.angular.z = angular
        self.publisher.publish(cmd)


def main():
    rclpy.init()
    node = CommandMapperNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Best-effort stop before exiting.
        node.publisher.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
