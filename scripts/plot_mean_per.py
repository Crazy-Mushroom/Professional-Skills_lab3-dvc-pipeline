""" 
Different from plot_per_vs_snr, plot_mean_per is for multiple languages.
It plot performance vs noise for each language and the cross language mean.
For exanpme, if we have en and fr, there will be three lines on the .png:
so, one for en, one for fr, and one for cross-mean of these two languages
"""

import json
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


def load_curve(path):
    with open(path) as f:
        data = json.load(f)

    snr = sorted([int(k) for k in data.keys()])
    per = [data[str(s)] for s in snr]

    return snr, per


def main():
    # the user can decide to plot across which specific languages
    parser = argparse.ArgumentParser()
    parser.add_argument("--langs", nargs="+", required=True)

    args = parser.parse_args()

    plt.figure()

    # plot each language
    for lang in args.langs:
        path = Path(f"results/{lang}/per_by_snr.json") 
        snr, per = load_curve(path)
        plt.plot(snr, per, marker="o", label=lang)

    # plot mean curve
    mean_path = Path("results/mean_per_by_snr.json")
    if mean_path.exists():
        snr, per = load_curve(mean_path)
        plt.plot(snr, per, marker="o", linestyle="--", label="mean")

    plt.xlabel("SNR (dB)")
    plt.ylabel("PER")
    plt.title("PER vs SNR (cross-language)")
    plt.grid(True)
    plt.legend()

    output = Path("results/per_vs_snr_all_langs.png")
    output.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output)
    print("Saved plot:", output)


if __name__ == "__main__":
    main()