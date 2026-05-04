from pathlib import Path
import argparse
import csv
import statistics


class ThresholdCalculator:
    def __init__(self, rest_state_id=0, active_state_ids=None, multiplier=3.0):
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

    def compute_rest_statistics(self, rest_values):

        if len(rest_values) < 2:
            raise ValueError("Not enough rest values")
        
        mean = statistics.mean(rest_values)
        std = statistics.stdev(rest_values)

        return mean, std

    def compute_threshold(self, rest_mean, rest_std):
        threshold = rest_mean + self.multiplier * rest_std
        return threshold

    def sanity_check(self, threshold, active_values):
        if len(active_values) == 0:
            return
        
        active_mean = statistics.mean(active_values)
        if threshold > active_mean:
            print("Warning: Threshold is larger that active mean")

    def calculate(self, csv_path):
        values_by_state = self.load_values_by_state(csv_path)

        rest_values = self.extract_rest_values(values_by_state)
        rest_mean,rest_std = self.compute_rest_statistics(rest_values)
        threshold = self.compute_threshold(rest_mean=rest_mean, rest_std=rest_std)

        active_values = self.extract_active_values(values_by_state)
        self.sanity_check(threshold=threshold,active_values=active_values)
        
        return int(threshold)
        



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--rest-state-id", type=int, default=0)
    parser.add_argument("--active-state-ids", type=int, nargs="*", default=None)
    parser.add_argument("--multiplier", type=float, default=3.0)
    return parser.parse_args()


def main():
    args = parse_args()

    calculator = ThresholdCalculator(
        rest_state_id=args.rest_state_id,
        active_state_ids=args.active_state_ids,
        multiplier=args.multiplier,
    )

    threshold = calculator.calculate(args.input)

    print(f"Threshold: {threshold}")


if __name__ == "__main__":
    main()