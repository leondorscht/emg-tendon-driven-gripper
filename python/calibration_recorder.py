from pathlib import Path
import argparse
import csv
import random
import time

import serial  # pyserial


class ProtocolGenerator:
    def __init__(self, state_dict, state_length, rest_length, rest_state_id=0):
        self.state_dict = state_dict
        self.state_length = state_length
        self.rest_length = rest_length
        self.rest_state_id = rest_state_id

    def _get_state_length(self, length_config):
        if isinstance(length_config, tuple):
            return random.uniform(length_config[0], length_config[1])
        return length_config

    def generate(self, num_repetitions):
        """
        Gibt eine Liste von States/Trials zurück.
        """
        sequence = []

        for _ in range(num_repetitions):
            for state_id, state_name in self.state_dict.items():
                if state_id == self.rest_state_id:
                    continue

                sequence.append({
                    "state_id": state_id,
                    "duration": self._get_state_length(self.state_length),
                    "state_name": state_name,
                })

                sequence.append({
                    "state_id": self.rest_state_id,
                    "duration": self._get_state_length(self.rest_length),
                    "state_name": self.state_dict[self.rest_state_id],
                })

        return sequence


class EMGSerialReader:
    def __init__(self, port, baudrate=9600, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None

    def open(self):
        self.serial_connection = serial.Serial(
            self.port,
            self.baudrate,
            timeout=self.timeout,
        )

        time.sleep(2)
        self.serial_connection.reset_input_buffer()

    def read_sample(self):
        if self.serial_connection is None:
            return None

        if not self.serial_connection.is_open:
            return None

        line = self.serial_connection.readline()

        if not line:
            return None

        try:
            return int(line.decode("utf-8").strip())
        except (ValueError, UnicodeDecodeError):
            return None

    def close(self):
        if self.serial_connection is not None:
            self.serial_connection.close()
            self.serial_connection = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class CSVRecorder:
    def __init__(self, output_path, flush_each_sample=False):
        self.output_path = Path(output_path)
        self.flush_each_sample = flush_each_sample
        self.file = None
        self.writer = None

    def open(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        self.file = open(self.output_path, "w", newline="")
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=["timestamp", "state_id", "state_name", "duration", "value"],
        )
        self.writer.writeheader()

    def write_sample(self, sample):
        if self.writer is None:
            return

        self.writer.writerow(sample)

        if self.flush_each_sample:
            self.file.flush()

    def close(self):
        if self.file:
            self.file.close()

        self.file = None
        self.writer = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class RecordingController:
    def __init__(self, protocol, reader, recorder):
        self.protocol = protocol
        self.reader = reader
        self.recorder = recorder

    def run(self):
        self.reader.open()
        self.recorder.open()

        try:
            overall_start_time = time.monotonic()

            for state_info in self.protocol:
                self._record_state(state_info, overall_start_time)

        finally:
            self.reader.close()
            self.recorder.close()

        return self.recorder.output_path

    def _record_state(self, state_info, overall_start_time):
        start_time = time.monotonic()

        print(state_info["state_name"])

        while time.monotonic() - start_time < state_info["duration"]:
            sample = self.reader.read_sample()

            if sample is None:
                continue

            sample_row = {
                "timestamp": time.monotonic() - overall_start_time,
                "state_id": state_info["state_id"],
                "state_name": state_info["state_name"],
                "duration": state_info["duration"],
                "value": sample,
            }

            self.recorder.write_sample(sample_row)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--output", default="data/calibration.csv")
    return parser.parse_args()


def main():

    # parse arguments from main call
    args = parse_args()

    # a simple state dict
    state_dict = {
        0: "rest",
        1: "hand_open",
        2: "hand_close",
    }

    # create a protocol generator, it is the order of states and their time. 
    # In this case, the time is set to a specific value so it is not random
    protocol = ProtocolGenerator(
        state_dict=state_dict,
        state_length=5,
        rest_length=3,
        rest_state_id=0,
    ).generate(num_repetitions=2)

    # Reader for the EMG data from arduino
    reader = EMGSerialReader(
        port=args.port,
        baudrate=args.baudrate,
        timeout=1,
    )

    # Recorder
    recorder = CSVRecorder(
        output_path=args.output,
    )

    # Controller that puts together the reader and recorder and shows the 
    # protocol in terminal
    controller = RecordingController(
        protocol=protocol,
        reader=reader,
        recorder=recorder,
    )

    output_path = controller.run()
    print(f"Saved calibration recording to {output_path}")


if __name__ == "__main__":
    main()