from pathlib import Path
import argparse
import csv
import statistics


class ThresholdCalculator:
    def __init__(self, rest_state_id=0, active_state_ids=None, multiplier=2.0):
        self.rest_state_id = rest_state_id
        self.active_state_ids = active_state_ids
        self.multiplier = multiplier

    def load_values_by_state(self, csv_path):
        with open(csv_path, newline="") as file:
            reader = csv.DictReader(file)

            values_by_state = {}

            for row in reader:
                try:
                    state_id = int(row["state_id"])
                    value = int(row["value"])
                except ValueError:
                    continue

                if state_id not in values_by_state:
                    values_by_state[state_id] = []

                values_by_state[state_id].append(value)

        return values_by_state

    def extract_rest_values(self, values_by_state):
        return values_by_state.get(self.rest_state_id, [])

    def extract_active_values(self, values_by_state):
        if self.active_state_ids is None:
            return []

        active_values = []

        for state_id in self.active_state_ids:
            active_values.extend(values_by_state.get(state_id, []))

        return active_values

    def compute_statistics(self, values):
        if len(values) < 2:
            raise ValueError("Not enough values")

        mean = statistics.mean(values)
        std = statistics.stdev(values)

        return mean, std

    def compute_rms_values(self, values, baseline, rms_window):
        rms_values = []

        for i in range(len(values)):
            start = max(0, i - rms_window + 1)
            window_values = values[start:i + 1]

            sum_sq = 0

            for value in window_values:
                diff = value - baseline
                sum_sq += diff * diff

            rms = (sum_sq / len(window_values)) ** 0.5
            rms_values.append(rms)

        return rms_values

    def compute_threshold(self, rest_rms_values):
        rest_mean, rest_std = self.compute_statistics(rest_rms_values)
        threshold = rest_mean + self.multiplier * rest_std
        return threshold

    def sanity_check(self, threshold, active_rms_values):
        if len(active_rms_values) == 0:
            return

        active_mean = statistics.mean(active_rms_values)

        if threshold > active_mean:
            print("Warning: Threshold is larger than active RMS mean")

    def calculate(self, csv_path, rms_window=32):
        values_by_state = self.load_values_by_state(csv_path)

        rest_values = self.extract_rest_values(values_by_state)
        active_values = self.extract_active_values(values_by_state)

        if len(rest_values) < 2:
            raise ValueError("Not enough rest values")

        baseline = int(statistics.median(rest_values))

        rest_rms_values = self.compute_rms_values(
            values=rest_values,
            baseline=baseline,
            rms_window=rms_window,
        )

        threshold = self.compute_threshold(rest_rms_values)

        active_rms_values = self.compute_rms_values(
            values=active_values,
            baseline=baseline,
            rms_window=rms_window,
        )

        self.sanity_check(
            threshold=threshold,
            active_rms_values=active_rms_values,
        )

        print(f"Baseline: {baseline}")
        print(f"Rest RMS mean: {statistics.mean(rest_rms_values)}")
        print(f"Rest RMS std: {statistics.stdev(rest_rms_values)}")

        if len(active_rms_values) > 0:
            print(f"Active RMS mean: {statistics.mean(active_rms_values)}")

        print(f"Threshold: {threshold}")

        return int(threshold), int(baseline)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--rest-state-id", type=int, default=0)
    parser.add_argument("--active-state-ids", type=int, nargs="*", default=None)
    parser.add_argument("--multiplier", type=float, default=2.0)
    parser.add_argument("--rms-window", type=int, default=32)
    return parser.parse_args()


def main():
    args = parse_args()

    calculator = ThresholdCalculator(
        rest_state_id=args.rest_state_id,
        active_state_ids=args.active_state_ids,
        multiplier=args.multiplier,
    )

    threshold, baseline = calculator.calculate(
        csv_path=args.input,
        rms_window=args.rms_window,
    )

    print(f"Threshold: {threshold}")
    print(f"Baseline: {baseline}")


if __name__ == "__main__":
    main()