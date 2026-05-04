from pathlib import Path
import time
import csv
import serial  # pyserial
import random
import argparse


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
        # should generate random states with the rest

        for _ in range(num_repetitions):
            for state_id, state_name in self.state_dict.items():

                if state_id == self.rest_state_id:
                    continue

                sequence.append({
                    "state_id": state_id,
                    "duration": self._get_state_length(self.state_length),
                    "state_name": state_name
                })

                sequence.append({
                    "state_id": self.rest_state_id,
                    "duration": self._get_state_length(self.rest_length),
                    "state_name": self.state_dict[self.rest_state_id]
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
            timeout=self.timeout
        )

        time.sleep(2)  # Arduino braucht oft kurz nach dem Öffnen
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
            value = int(line.decode("utf-8").strip())
            return value

        except ValueError:
            return None
        
        except UnicodeDecodeError:
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
    def __init__(self, output_path):
        self.output_path = Path(output_path)
        self.file = None
        self.writer = None

    def open(self):
        """
        CSV-Datei öffnen und Header schreiben.
        """
        self.file = open(self.output_path, "w", newline="")
        self.writer = csv.DictWriter(
            self.file,
            fieldnames=["timestamp", "state_id", "state_name", "duration", "value"]
            )
        self.writer.writeheader()

    def write_sample(self, sample):
        """
        Einen Messpunkt in die CSV schreiben.
        """
        if self.writer:
            self.writer.writerow(sample)
            self.file.flush()

    def close(self):
        """
        Datei sauber schließen.
        """
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
        """
        Führt das komplette Experiment aus.
        """
        self.reader.open()
        self.recorder.open()

        try:
            overall_start_time = time.monotonic()
            for state_info in self.protocol:
                self._record_state(state_info, overall_start_time)

        finally:
            self.reader.close()
            self.recorder.close()

    def _record_state(self, state_info, overall_start_time):
        """
        Nimmt Daten für genau einen State auf.
        """
        start_time = time.monotonic()

        print(state_info["state_name"])

        while time.monotonic() - start_time < state_info["duration"]:
            sample = self.reader.read_sample()

            if sample is None:
                continue

            sample_row = {
                "timestamp": time.monotonic()-overall_start_time,
                "state_id": state_info["state_id"], 
                "state_name": state_info["state_name"], 
                "duration": state_info["duration"], 
                "value": sample
                }
            self.recorder.write_sample(sample_row)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--output", default="recording.csv")
    return parser.parse_args()


if __name__ == "__main__":

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

    controller.run()