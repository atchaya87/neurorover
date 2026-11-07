import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


UPDATE_PERIOD_S = 0.05  # 20 Hz
STALE_AFTER_S = 0.5

WHEEL_BASE_M = 0.30       # distance between left and right wheels (placeholder)
MAX_WHEEL_SPEED_MS = 0.5  # wheel speed that maps to full power (placeholder)


def twist_to_wheels(linear, angular):
    """Return (left, right) wheel power in the range -1.0 to 1.0."""
    left = linear - angular * WHEEL_BASE_M / 2
    right = linear + angular * WHEEL_BASE_M / 2

    def clamp(value):
        return max(-1.0, min(1.0, value / MAX_WHEEL_SPEED_MS))

    return clamp(left), clamp(right)


class FakeMotors:
    """Stand-in for the real motor controller.

    TODO: replace with something like
        from robot.motor_control import Motors
    exposing the same set_speeds(left, right) and stop() methods.
    The real version would scale -1..1 to RoboClaw duty (-32767..32767).
    """

    def __init__(self, logger):
        self.logger = logger
        self.last = None

    def set_speeds(self, left, right):
        current = (round(left, 2), round(right, 2))
        if current != self.last:
            self.logger.info(f"[FAKE MOTORS] left={current[0]:+.2f} right={current[1]:+.2f}")
            self.last = current

    def stop(self):
        self.set_speeds(0.0, 0.0)

    def close(self):
        pass


class MotorDriverNode(Node):
    def __init__(self):
        super().__init__("motor_driver")
        self.motors = FakeMotors(self.get_logger())
        self.linear = 0.0
        self.angular = 0.0
        self.last_command = float("-inf")

        self.motors.stop()
        self.subscription = self.create_subscription(
            Twist, "/cmd_vel", self.receive_command, 10
        )
        self.timer = self.create_timer(UPDATE_PERIOD_S, self.update_motors)
        self.get_logger().info("Motor driver ready (FAKE motors); starting stopped")

    def receive_command(self, msg):
        self.linear = msg.linear.x
        self.angular = msg.angular.z
        self.last_command = time.monotonic()

    def update_motors(self):
        fresh = time.monotonic() - self.last_command < STALE_AFTER_S
        if not fresh:
            self.motors.stop()
            return
        left, right = twist_to_wheels(self.linear, self.angular)
        self.motors.set_speeds(left, right)

    def stop_and_close(self):
        try:
            self.motors.stop()
        finally:
            self.motors.close()


def main():
    rclpy.init()
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.stop_and_close()
        finally:
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()


if __name__ == "__main__":
    main()
