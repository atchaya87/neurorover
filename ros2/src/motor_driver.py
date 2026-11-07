import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from basicmicro import Basicmicro


PORT = "/dev/ttyACM0"  # Replace with your device path.
ADDRESS = 0x80         # Must match the controller configuration.
TEST_DUTY = 4000       # About 12% of the positive 32767 range.

DEBUG = False # For testing, running without ROboclaw attached


class MotorDriver(Node):
    def __init__(self):
        super().__init__("motor_driver")

        self.enabled = False
        self.last_command = float("-inf")

        if not DEBUG:
	        # USB CDC does not use a physical UART baud rate, but the
	        # library constructor still takes a baud-rate argument.
	        self.controller = Basicmicro(PORT, 38400)
	        self.controller.Open()
	
	        # Explicitly start both channels at zero.
	        self.controller.DutyM1M2(ADDRESS, 0, 0)

        self.subscription = self.create_subscription(
            Bool, "/motor_enable", self.receive_command, 1
        )
        self.timer = self.create_timer(0.05, self.update_motor)

        self.get_logger().info("Motor driver ready; motor starts OFF.")

    def receive_command(self, message):
        self.enabled = message.data
        self.last_command = time.monotonic()
        print(f"Received command: {message.data}", flush=True)

    def update_motor(self):
        if DEBUG:
            return
        fresh = time.monotonic() - self.last_command < 0.5
        duty = TEST_DUTY if self.enabled and fresh else 0

        try:
            result = self.controller.DutyM1(ADDRESS, duty)
            if not result:
                raise RuntimeError("RoboClaw did not acknowledge command")
        except Exception as error:
            self.enabled = False
            self.get_logger().error(f"Motor communication failed: {error}")
            raise

    def stop_and_close(self):
        if DEBUG:
            return
        try:
            self.controller.DutyM1M2(ADDRESS, 0, 0)
        finally:
            self.controller.close()


def main():
    rclpy.init()
    node = None
    try:
        node = MotorDriver()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            try:
                node.stop_and_close()
            finally:
                node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
