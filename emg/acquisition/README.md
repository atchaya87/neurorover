# EMG acquisition MVP

`acquisition.py` is a ROS 2 Python node that reads one JSON object per line from
standard input, validates each batch, and publishes it as `std_msgs/String` JSON
on `/emg/raw`. This input format is a temporary boundary while the EMG device is
undecided. A device reader can later produce the same batches.

Each input object needs:

- `channels`: unique channel names, such as `["forearm"]`.
- `sample_rate_hz`: positive sampling rate.
- `samples`: a list of frames, each with one finite number per channel.
- `unit`: the unit of the values, such as `V` or `count`.
- `signal_kind`: what the values represent, such as `raw` or `envelope`.

Optional fields are `source_id` and `first_sample_time_ns`. The latter must be
the Unix capture time of the **first** sample in nanoseconds if the source knows it;
otherwise it is `null`. The node adds `sequence` and `received_at_ns` to every
published batch. Rejected lines leave gaps in the sequence. Arrival time is not
a substitute for an accurate sample time.

Example input:

```json
{"source_id":"demo","channels":["forearm"],"sample_rate_hz":1000,"samples":[[0.1],[0.2]],"unit":"V","signal_kind":"raw"}
```

After sourcing a ROS 2 environment, pipe newline-delimited input to
`python3 emg/acquisition/acquisition.py`. Use `ros2 topic echo /emg/raw` in
another terminal to inspect published batches. The repository does not yet
contain a ROS 2 package manifest or a device-specific reader.

Invalid batches are discarded with a warning. Input failure or end of stream
stops the node; downstream control must treat stale EMG data as no command.
