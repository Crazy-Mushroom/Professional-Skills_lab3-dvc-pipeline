import json
import argparse
from pathlib import Path


def load_json(path):
    with open(path) as f:
        return json.load(f)


def compute_mean(files):
    data = [load_json(f) for f in files]
    snrs = data[0].keys()
    mean = {}

    for snr in snrs:
        values = [d[snr] for d in data]
        mean[snr] = sum(values) / len(values)

    return mean


def main():
    # decide to compute mean across which specific languages
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--langs",
        nargs="+",
        required=True,
        help="Languages to average (e.g. en fr)"
    )
    args = parser.parse_args()

    # automatically build input paths
    input_paths = [
        Path(f"results/{lang}/per_by_snr.json")
        for lang in args.langs
    ]

    mean = compute_mean(input_paths)

    output_path = Path("results/mean_per_by_snr.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(mean, f, indent=2)
    print("Saved mean PER →", output_path)


if __name__ == "__main__":
    main()