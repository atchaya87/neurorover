import json
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# ensure all necessary fields are present; these fields can be changed
def validate(packet):
    if not isinstance(packet, dict):
        raise ValueError("batch must be a JSON object")
    required = ("channels", "sample_rate_hz", "samples", "unit")
    missing = [name for name in required if name not in packet]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    channels = packet["channels"]
    samples = packet.get("samples")
    if not isinstance(channels, list) or not channels:
        raise ValueError("channel info cannot be empty")
    if not isinstance(samples, list) or not samples:
        raise ValueError("samples cannot be empty")
    if any(not isinstance(frame, list) or len(frame) != len(channels)
           for frame in samples):
        raise ValueError("each sample must have one value per channel")
    return packet

# calls the validation and sends data to /emg/raw as publisher
class AcquisitionNode(Node):
    def __init__(self):
        super().__init__("emg_acquisition")
        self.publisher = self.create_publisher(String, "/emg/raw", 10)

    def handle_line(self, line):
        try:
            batch = validate(json.loads(line))
        except (json.JSONDecodeError, ValueError) as error:
            self.get_logger().warning(f"Discarding invalid EMG batch: {error}")
            return

        batch["received_at_ns"] = time.time_ns()
        self.publisher.publish(String(data=json.dumps(batch, separators=(",", ":"))))


def main():
    rclpy.init()
    node = AcquisitionNode()
    node.get_logger().info("Reading from stdin")
    try:
        while rclpy.ok():
            line = sys.stdin.readline()
            if not line:
                node.get_logger().warning("End of stream")
                break
            if line.strip():
                node.handle_line(line)
    except KeyboardInterrupt:
        pass
    except OSError as error:
        node.get_logger().error(f"Input error: {error}")
        raise
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
