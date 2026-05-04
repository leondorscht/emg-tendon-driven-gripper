from pathlib import Path
import argparse
import subprocess
import time


class ArduinoFlasher:
    def __init__(self, sketch_path, port, fqbn, cli_path="arduino-cli"):
        self.sketch_path = Path(sketch_path)
        self.port = port
        self.fqbn = fqbn
        self.cli_path = cli_path

    def validate_paths(self):
        if not self.sketch_path.exists() or not self.sketch_path.is_dir():
            raise ValueError(f"Invalid sketch path: {self.sketch_path}")
        
        

    def build_compile_command(self):

        return [
            self.cli_path,
            "compile",
            "--fqbn",
            self.fqbn,
            str(self.sketch_path),
        ]

    def build_upload_command(self):

        return [
            self.cli_path,
            "upload",
            "-p",
            self.port,
            "--fqbn",
            self.fqbn,
            str(self.sketch_path),
    ]

    def run_command(self, command):

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            print("Command failed:")
            print(" ".join(command))
            print("STDOUT:")
            print(result.stdout)
            print("STDERR:")
            print(result.stderr)
            raise RuntimeError("Arduino CLI command failed")
        
        return result

    def compile(self):
        print("Compiling Arduino sketch...")
        command = self.build_compile_command()
        return self.run_command(command)

    def upload(self):

        print("Uploading Arduino sketch...")
        command = self.build_upload_command()
        result = self.run_command(command)

        time.sleep(2)

        return result

    def flash(self):
        self.validate_paths()
        self.compile()
        self.upload()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sketch-path", required=True)
    parser.add_argument("--port", required=True)
    parser.add_argument("--fqbn", required=True)
    parser.add_argument("--cli-path", default="arduino-cli")
    return parser.parse_args()


def main():
    args = parse_args()

    flasher = ArduinoFlasher(
        sketch_path=args.sketch_path,
        port=args.port,
        fqbn=args.fqbn,
        cli_path=args.cli_path,
    )

    flasher.flash()


if __name__ == "__main__":
    main()