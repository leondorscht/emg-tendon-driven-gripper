from pathlib import Path
import argparse

from calibration_recorder import (
    ProtocolGenerator,
    EMGSerialReader,
    CSVRecorder,
    RecordingController,
)
from threshold_calculator import ThresholdCalculator
from config_writer import ConfigWriter
from arduino_flasher import ArduinoFlasher


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--port", required=True)
    parser.add_argument("--fqbn", required=True)

    parser.add_argument("--sketch-path", default="arduino/emg_control")
    parser.add_argument("--config-path", default="arduino/emg_control/config.h")
    parser.add_argument("--output", default="data/calibration.csv")

    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--emg-pin", default="A0")
    parser.add_argument("--servo-pins", type=int, nargs="+", default=[9, 10, 11])
    parser.add_argument("--servo-open-angle", type=int, default=0)
    parser.add_argument("--servo-close-angle", type=int, default=90)
    parser.add_argument("--smoothing-window", type=int, default=10)

    parser.add_argument("--state-length", type=float, default=5)
    parser.add_argument("--rest-length", type=float, default=3)
    parser.add_argument("--num-repetitions", type=int, default=10)

    parser.add_argument("--rest-state-id", type=int, default=0)
    parser.add_argument("--active-state-ids", type=int, nargs="+", default=[1])
    parser.add_argument("--threshold-multiplier", type=float, default=3.0)

    parser.add_argument("--cli-path", default="arduino-cli")

    return parser.parse_args()


def build_protocol(args):
    state_dict = {
        0: "rest",
        1: "hand_close",
    }

    return ProtocolGenerator(
        state_dict=state_dict,
        state_length=args.state_length,
        rest_length=args.rest_length,
        rest_state_id=args.rest_state_id,
    ).generate(num_repetitions=args.num_repetitions)


def write_calibration_config(args):
    writer = ConfigWriter(config_path=args.config_path)

    writer.write_config(
        mode_calibration=True,
        serial_baudrate=args.baudrate,
        emg_pin=args.emg_pin,
        emg_threshold=1023,
        servo_pins=args.servo_pins,
        servo_open_angle=args.servo_open_angle,
        servo_close_angle=args.servo_close_angle,
        smoothing_window=args.smoothing_window,
    )


def write_control_config(args, threshold):
    writer = ConfigWriter(config_path=args.config_path)

    writer.write_config(
        mode_calibration=False,
        serial_baudrate=args.baudrate,
        emg_pin=args.emg_pin,
        emg_threshold=int(threshold),
        servo_pins=args.servo_pins,
        servo_open_angle=args.servo_open_angle,
        servo_close_angle=args.servo_close_angle,
        smoothing_window=args.smoothing_window,
    )


def flash_arduino(args):
    flasher = ArduinoFlasher(
        sketch_path=args.sketch_path,
        port=args.port,
        fqbn=args.fqbn,
        cli_path=args.cli_path,
    )

    flasher.flash()


def record_calibration(args, protocol):
    reader = EMGSerialReader(
        port=args.port,
        baudrate=args.baudrate,
        timeout=1,
    )

    recorder = CSVRecorder(
        output_path=args.output,
    )

    controller = RecordingController(
        protocol=protocol,
        reader=reader,
        recorder=recorder,
    )

    return controller.run()


def calculate_threshold(args, csv_path):
    calculator = ThresholdCalculator(
        rest_state_id=args.rest_state_id,
        active_state_ids=args.active_state_ids,
        multiplier=args.threshold_multiplier,
    )

    return calculator.calculate(csv_path)


def main():
    args = parse_args()

    print("Writing calibration config...")
    write_calibration_config(args)

    print("Flashing calibration firmware...")
    flash_arduino(args)

    print("Building calibration protocol...")
    protocol = build_protocol(args)

    print("Recording calibration data...")
    csv_path = record_calibration(args, protocol)

    print("Calculating threshold...")
    threshold = calculate_threshold(args, csv_path)
    print(f"Threshold: {threshold}")

    print("Writing control config...")
    write_control_config(args, threshold)

    print("Flashing control firmware...")
    flash_arduino(args)

    print("Pipeline complete.")


if __name__ == "__main__":
    main()