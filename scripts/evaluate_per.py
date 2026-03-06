""" 
This file is for PER Evaluation:
edit_distance = Substitution(S) + Insertion(I) + Deletion(D)
len(reference phoneme sequence) = N, so that N is thenumber of phonemes in reference
PER = (S + D + I) / N = edit_distance / len(ref)
So, PER = edit_distance(ref, pred) / len(ref)
"""
import json
from pathlib import Path 
from collections import defaultdict
import argparse


def edit_distance(ref, pred):
    """
    to calculate PER, first is to 
    get edit_distance between reference and predicted phonemes
    """
    # split the reference phoneme(predicted phoneme) string into list of phonemes
    r = ref.split()
    h = pred.split()

    dp = [[0]*(len(h)+1) for _ in range(len(r)+1)] # DP matrix: row=ref, colum=pred

    for i in range(len(r)+1): # fill first column, that the deletions needed to mathch empty prediction
        dp[i][0] = i
    for j in range(len(h)+1): # fill first row, that the insertions needed to match empty reference
        dp[0][j] = j

    for i in range(1, len(r)+1):
        for j in range(1, len(h)+1):
            if r[i-1] == h[j-1]: # iterate over each reference phoneme and predicted phoneme, 
                cost = 0         # if phonemes match, then no substitution cost
            else:
                cost = 1         # otherwise, the cost is 1.
            dp[i][j] = min(
                dp[i-1][j] + 1,     # D, deletion
                dp[i][j-1] + 1,     # I, insertion
                dp[i-1][j-1] + cost # S, substitution
            )

    return dp[len(r)][len(h)], len(r)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    LANG = args.lang
    
    INPUT_MANIFEST = Path(f"data/manifests/{LANG}/predictions.jsonl")
    RESULTS_DIR = Path(f"results/{LANG}")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    OUTPUT_JSON = RESULTS_DIR / "per_by_snr.json"
    OUTPUT_TABLE = RESULTS_DIR / "per_table.txt"

    RESULTS_DIR.parent.mkdir(parents=True, exist_ok=True) # automatically create results/

    errors = defaultdict(int) # errors by snr
    totals = defaultdict(int) # reference length by snr

    with open(INPUT_MANIFEST, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)

            snr = item["snr_db"]
            ref = item["ref_phon"]
            pred = item["pred_phon"] # this new item was added in run_inference.py!
            
            # in case "accidents" happen, the following two lines ensure the whole process won't crash
            if ref is None or pred is None:
                continue

            dist, length = edit_distance(ref, pred)  # dist=edit_distance, length=reference_length

            errors[snr] += dist
            totals[snr] += length

    per_by_snr = {}

    for snr in sorted(errors.keys(), reverse=True): # use reverse, so that the plot will be easier to read as X axis is from -5 to 40
        if totals[snr] > 0:
            per = errors[snr] / totals[snr]  
        else: # but rarely, total[snr] = 0, I set the condition just in case it happens
            per=0
        per_by_snr[str(snr)] = per

    # save json matrics
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(per_by_snr, f, indent=2)
    # save the table
    with open(OUTPUT_TABLE, "w", encoding="utf-8") as f:
        f.write("SNR(dB)\tPER\n")
        for snr, per in per_by_snr.items():
            f.write(f"{snr}:\t{per:.3f}\n")
        
    print("Evaluation completed.")
    print("Metrics:", OUTPUT_JSON)
    print("Table:", OUTPUT_TABLE)


if __name__ == "__main__":
    main()