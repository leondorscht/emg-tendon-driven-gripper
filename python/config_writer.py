from pathlib import Path
import argparse
import textwrap


class ConfigWriter:
    def __init__(self, config_path):
        self.config_path = Path(config_path)

    def format_servo_pins(self, servo_pins):
        if len(servo_pins) == 0:
            raise ValueError("Servo pin list cannot be empty")
        else:
            pin_string = "{"
            for pin in servo_pins:
                pin_string += str(pin)
                pin_string += ","
            pin_string = pin_string[:-1]
            pin_string += "}"

        return pin_string

    def build_config_content(
        self,
        mode_calibration,
        serial_baudrate,
        emg_pin,
        emg_threshold,
        servo_pins,
        servo_open_angle,
        servo_close_angle,
        smoothing_window,
    ):
        
        mode_calibration = 1 if mode_calibration else 0

        pin_string = self.format_servo_pins(servo_pins)

        config_content = textwrap.dedent("""\
                #pragma once

                // Operation Mode
                // set the mode to either calibration (1) or control (0)
                #define MODE_CALIBRATION {mode_calibration}

                // Serial
                #define SERIAL_BAUDRATE {serial_baudrate}

                // Servos
                #define NUM_SERVOS {num_servos}
                const int SERVO_PINS[NUM_SERVOS] = {pin_string};

                #define SERVO_OPEN_ANGLE {servo_open_angle}
                #define SERVO_CLOSE_ANGLE {servo_close_angle}

                // EMG
                #define EMG_PIN {emg_pin}
                #define EMG_THRESHOLD {emg_threshold}
                #define EMG_SMOOTHING_WINDOW {smoothing_window}
                """).format(mode_calibration=mode_calibration,
                            serial_baudrate=serial_baudrate,
                            num_servos=len(servo_pins),
                            pin_string=pin_string,
                            servo_open_angle=servo_open_angle,
                            servo_close_angle=servo_close_angle,
                            emg_pin=emg_pin,
                            emg_threshold=emg_threshold,
                            smoothing_window=smoothing_window,)
        
        return config_content

    def write_config(
        self,
        mode_calibration = True,
        serial_baudrate = 9600,
        emg_pin = "A0",
        emg_threshold = 1023,
        servo_pins = None,
        servo_open_angle = 0,
        servo_close_angle = 90,
        smoothing_window = 10,
    ):
        
        if servo_pins is None:
            servo_pins = [9, 10, 11]
        
        config_string = self.build_config_content(mode_calibration,
            serial_baudrate,
            emg_pin,
            emg_threshold,
            servo_pins,
            servo_open_angle,
            servo_close_angle,
            smoothing_window,
            )
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(config_string, encoding="utf-8")
        



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--mode-calibration", type=int, required=True)
    parser.add_argument("--serial-baudrate", type=int, default=9600)
    parser.add_argument("--emg-pin", default="A0")
    parser.add_argument("--emg-threshold", type=int, default=400)
    parser.add_argument("--servo-pins", type=int, nargs="+", required=True)
    parser.add_argument("--servo-open-angle", type=int, default=0)
    parser.add_argument("--servo-close-angle", type=int, default=90)
    parser.add_argument("--smoothing-window", type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()

    writer = ConfigWriter(config_path=args.config_path)

    writer.write_config(
        mode_calibration=bool(args.mode_calibration),
        serial_baudrate=args.serial_baudrate,
        emg_pin=args.emg_pin,
        emg_threshold=args.emg_threshold,
        servo_pins=args.servo_pins,
        servo_open_angle=args.servo_open_angle,
        servo_close_angle=args.servo_close_angle,
        smoothing_window=args.smoothing_window,
    )


if __name__ == "__main__":
    main()