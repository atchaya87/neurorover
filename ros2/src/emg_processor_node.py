"""EMG processor node: filter -> features -> classify.

Listens:    /emg/raw   (std_msgs/Float32MultiArray, from emg_reader_node)
Publishes:  /gesture   (std_msgs/String)

Keeps a sliding window of recent samples per channel, computes RMS for each
channel, and turns that into a gesture label.

PLACEHOLDER: until emg/processing/ and a trained model from ml_pipeline/
exist, filtering is skipped and the "classifier" is a simple rule:
quiet on every channel -> "rest", otherwise the loudest channel picks a gesture.
"""

import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String


SAMPLE_RATE_HZ = 250
WINDOW_MS = 200
WINDOW_SAMPLES = SAMPLE_RATE_HZ * WINDOW_MS // 1000  # 50 samples

# Placeholder mapping: channel index -> gesture label.
GESTURES = ["fist", "open", "wrist_left", "wrist_right"]
REST_THRESHOLD = 0.2  # RMS below this on every channel counts as "rest"


def filter_window(window):
    """TODO: replace with emg.processing (bandpass 20-450 Hz, 60 Hz notch)."""
    return window


def extract_features(window):
    """Return RMS per channel. TODO: move to emg.processing and add more features."""
    return [
        math.sqrt(sum(s * s for s in channel) / len(channel)) if channel else 0.0
        for channel in window
    ]


class PlaceholderClassifier:
    """TODO: replace with the trained model from ml_pipeline/, e.g.
        model = joblib.load("ml_pipeline/models/gesture_model.pkl")
        label = model.predict([features])[0]
    """

    def predict(self, features):
        if max(features) < REST_THRESHOLD:
            return "rest"
        loudest = features.index(max(features))
        return GESTURES[loudest] if loudest < len(GESTURES) else "rest"


class EmgProcessorNode(Node):
    def __init__(self):
        super().__init__("emg_processor")
        self.classifier = PlaceholderClassifier()
        self.window = None  # list of per-channel sample lists
        self.last_gesture = None

        self.subscription = self.create_subscription(
            Float32MultiArray, "/emg/raw", self.receive_chunk, 10
        )
        self.publisher = self.create_publisher(String, "/gesture", 10)
        self.get_logger().info("EMG processor ready (PLACEHOLDER classifier)")

    def receive_chunk(self, msg):
        if len(msg.layout.dim) < 2:
            self.get_logger().warn("Chunk missing layout; skipping")
            return
        channels = msg.layout.dim[0].size
        samples = msg.layout.dim[1].size
        if len(msg.data) != channels * samples:
            self.get_logger().warn("Chunk size does not match layout; skipping")
            return

        if self.window is None or len(self.window) != channels:
            self.window = [[] for _ in range(channels)]

        # Append new samples and keep only the most recent window.
        for ch in range(channels):
            start = ch * samples
            self.window[ch].extend(msg.data[start:start + samples])
            del self.window[ch][:-WINDOW_SAMPLES]

        if len(self.window[0]) < WINDOW_SAMPLES:
            return  # not enough data yet

        features = extract_features(filter_window(self.window))
        gesture = self.classifier.predict(features)

        self.publisher.publish(String(data=gesture))
        if gesture != self.last_gesture:
            self.get_logger().info(f"Gesture: {gesture}")
            self.last_gesture = gesture


def main():
    rclpy.init()
    node = EmgProcessorNode()
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
