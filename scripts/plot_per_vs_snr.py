import json
import matplotlib.pyplot as plt
from pathlib import Path
import argparse


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    LANG = args.lang
        
    INPUT = Path(f"results/{LANG}/per_by_snr.json")
    OUTPUT = Path(f"results/{LANG}/per_vs_snr.png")

    # load PER results
    with open(INPUT) as f:
        data = json.load(f)

    snr = list(map(int, data.keys()))
    per = list(data.values())

    plt.figure()
    plt.plot(snr, per, marker="o")
    plt.xlabel("SNR (dB)")
    plt.ylabel("PER")
    plt.title(f"{LANG}: PER vs SNR") # high SNR , little noise; low SNR, much noise
    plt.grid(True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT)

    print("Plot saved to:", OUTPUT)


if __name__ == "__main__":
    main()