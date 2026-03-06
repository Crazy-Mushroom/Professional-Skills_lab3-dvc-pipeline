"""
The file add_noise.py will do, mainly, three things:
(1) read input manifest, 
(2) use the functions defined in  add_noise_utils.py (provided in the instruction pdf),
(3) ouput noisy dataset, named as noisy.jsonl.
"""

import json
import hashlib
from pathlib import Path
import tempfile
import argparse

# use the function provided in the lab instruction pdf, which defines the function to add noise
from add_noise_utils import add_noise_to_file 


# As the instruction prefers 10 intervals, here we have 10 values
SNR_LEVELS = [40, 35, 30, 25, 20, 15, 10, 5, 0, -5]

# define a functin to calculate MD5checksum of a file.
# use MD5 to generae the unique fingerprint of the audio file to:
# (1) detect if the file has been modified or corrputed
# (2) ensure pipeline reproducibility
def compute_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:  # open file in binary mode, ensures consistent hash across platforms
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()  # return hexadecimal digest string to detect file changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    LANG = args.lang
    
    # Since in this stage I need to use the path constants multiple times,
    # to avoid mismatch, I use capitalized names again.
    INPUT_MANIFEST = Path(f"data/manifests/{LANG}/phoneme.jsonl")
    OUTPUT_MANIFEST = Path(f"data/manifests/{LANG}/noisy.jsonl")

    NOISY_DIR = Path(f"data/noisy/{LANG}")

    NOISY_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", 
        delete=False, 
        dir=OUTPUT_MANIFEST.parent,
        suffix=".tmp",
        encoding="utf-8",
    ) as tmp_file:
        temp_path = Path(tmp_file.name)

        with open(INPUT_MANIFEST, "r", encoding="utf-8") as f:

            for line in f:
                item = json.loads(line)

                wav_path = Path(item["wav_path"])

                for snr in SNR_LEVELS: # SNR = Signal-to-Noise Ratio

                    out_dir = NOISY_DIR / f"snr{snr}"
                    out_dir.mkdir(parents=True, exist_ok=True)

                    out_wav = out_dir / wav_path.name

                    add_noise_to_file(   # use the function defined in add_noise_utils.py ！
                        str(wav_path),
                        str(out_wav),
                        snr_db=snr,
                        seed=42,   # ensure reproducibility! set the random_seed to ensure obtaining same noises evey time
                    )

                    new_item = item.copy()
                    
                    # now, update the noisy file's path, SNR level and MD5checksum in the manifest
                    new_item["wav_path"] = str(out_wav).replace("\\", "/")
                    new_item["snr_db"] = snr
                    new_item["audio_md5"] = compute_md5(out_wav)

                    tmp_file.write(json.dumps(new_item) + "\n")

    temp_path.replace(OUTPUT_MANIFEST)

    print("Noise generation completed.")
    print(f"Output manifests:{OUTPUT_MANIFEST}")


if __name__ == "__main__":
    main()