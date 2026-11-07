import math
import random
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, MultiArrayDimension


NUM_CHANNELS = 4
SAMPLE_RATE_HZ = 250
CHUNK_SAMPLES = 25  # 25 samples at 250 Hz = one message every 100 ms


class FakeEmgBoard:
    """Stand-in for the real sensor board.

    TODO: replace with something like
        from emg.acquisition import EmgBoard
    exposing the same read_chunk() method.
    """

    def __init__(self, channels, sample_rate):
        self.channels = channels
        self.sample_rate = sample_rate
        self.start = time.monotonic()

    def read_chunk(self, num_samples):
        """Return a list of `channels` lists, each with `num_samples` floats."""
        elapsed = time.monotonic() - self.start
        # Every 3 s, pick a channel to "flex" for 1.5 s; channel cycles over time.
        cycle = int(elapsed // 3)
        flexing = (elapsed % 3) < 1.5
        active_channel = cycle % self.channels if flexing else None

        chunk = []
        for ch in range(self.channels):
            amplitude = 1.0 if ch == active_channel else 0.05
            chunk.append([
                amplitude * math.sin(random.uniform(0, 2 * math.pi))
                + random.gauss(0, 0.02)
                for _ in range(num_samples)
            ])
        return chunk


class EmgReaderNode(Node):
    def __init__(self):
        super().__init__("emg_reader")
        self.board = FakeEmgBoard(NUM_CHANNELS, SAMPLE_RATE_HZ)
        self.publisher = self.create_publisher(Float32MultiArray, "/emg/raw", 10)
        self.timer = self.create_timer(
            CHUNK_SAMPLES / SAMPLE_RATE_HZ, self.publish_chunk
        )
        self.get_logger().info(
            f"EMG reader ready (FAKE data): {NUM_CHANNELS} ch @ {SAMPLE_RATE_HZ} Hz"
        )

    def publish_chunk(self):
        chunk = self.board.read_chunk(CHUNK_SAMPLES)

        msg = Float32MultiArray()
        msg.layout.dim = [
            MultiArrayDimension(
                label="channels", size=NUM_CHANNELS, stride=NUM_CHANNELS * CHUNK_SAMPLES
            ),
            MultiArrayDimension(label="samples", size=CHUNK_SAMPLES, stride=CHUNK_SAMPLES),
        ]
        msg.data = [sample for channel in chunk for sample in channel]
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = EmgReaderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
