outline - MVP

EMG input device undecided for now, so acquisition.py serves as a general-purpose pipeline:
    reads JSON object (format: 'channels', 'sample_rate_hz', 'samples', 'unit', 'signal_type')
    validates each line -> publishes to /emg/raw as `std_msgs/String` JSON

the above JSON format is just a general/default EMG data format I've seen

Example input:
```json
{"source_id":"sample","channels":["forearm"],"sample_rate_hz":1000,"samples":[[0.1],[0.2]],"unit":"V","signal_kind":"raw"}
```

Invalid batches are discarded with a warning, and the Node is terminated upon input failure or reaching the end of the stream

