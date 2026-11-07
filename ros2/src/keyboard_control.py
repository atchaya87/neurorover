import select
import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


def main():
    if not sys.stdin.isatty():
        raise RuntimeError("Run this program in an interactive terminal.")

    rclpy.init()
    node = Node("keyboard_control")
    publisher = node.create_publisher(Bool, "/motor_enable", 1)

    enabled = False
    old_settings = termios.tcgetattr(sys.stdin)

    print("I = ON, O = OFF, Q = quit. Terminal must have focus.")

    try:
        tty.setcbreak(sys.stdin.fileno())

        while rclpy.ok():
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)

            if ready:
                key = sys.stdin.read(1).lower()
                if key == "i":
                    enabled = True
                    print("I pressed, enabled")
                elif key == "o":
                    enabled = False
                    print("O pressed, disabled")
                elif key == "q":
                    print("Quitting...")
                    break

            publisher.publish(Bool(data=enabled))
            rclpy.spin_once(node, timeout_sec=0)

    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(
            sys.stdin, termios.TCSADRAIN, old_settings
        )
        publisher.publish(Bool(data=False))
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
