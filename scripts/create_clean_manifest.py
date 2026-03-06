import os
import json
import hashlib
import soundfile as sf
from pathlib import Path
import tempfile
import shutil
import argparse

""" 
This .py file mainly defines things through functions, 
because later it's expect to be applied to other languages 
and functions help organize thing in modules to adapt to flexible application 
"""


def compute_md5(path: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def process_item(tmp_file, wav_path, utt_stem, ref_text, LANG):
    if not wav_path.exists():
        raise FileNotFoundError(f"WAV not found: {wav_path}")

    signal, sr = sf.read(wav_path) 

    if sr != 16000:  # Important! verify the sample rate if matches the model requirement (wav2vec2 will be applied to do analyze, it expects 16 kHz)
        raise ValueError(f"Unexpected sample rate: {sr}")

    if signal.ndim != 1: # Again to match to model's requirement, check if audio is mono (since the model expects single channel)
        raise ValueError("Audio is not mono") # reject multi-channel audio to avoid shape mismatch

    duration_s = len(signal) / sr  # it is not required, but the duration of sample may be needed in further analysis 
    audio_md5 = compute_md5(wav_path)

    utt_id = f"{LANG}_{utt_stem}"

    manifest_entry = {
        "utt_id": utt_id,
        "lang": LANG,
        "wav_path": str(wav_path).replace("\\", "/"), # DVC need to be reproducible, and github does not allow absolute path, so I have this line here to ensure cross-platform operation
        "ref_text": ref_text,
        "ref_phon": None,  # create_clean_manifest.py does not generate phonemes, it is in the next stage that espeak will generate phonemes.
        "audio_md5": audio_md5,
        "sr": sr,
        "duration_s": round(duration_s, 4),
        "snr_db": None,
    }

    tmp_file.write(json.dumps(manifest_entry) + "\n") # each utterance is an independent JSON object
                                                        # each object takes one line


def main():
    # define all the constants and language variable
    #      use capitalized forms for constants so that easy to recognize in the code 
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    parser.add_argument("--subset", default="dev-clean")
    args = parser.parse_args()

    LANG = args.lang
    SUBSET =args.subset

    FLAC_ROOT = Path(f"data/raw/{LANG}/flac")
    WAV_ROOT = Path(f"data/raw/{LANG}/wav")
    MANIFEST_DIR = Path(f"data/manifests/{LANG}")
    MANIFEST_PATH = MANIFEST_DIR / "clean.jsonl"

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    # Atomic writing: write to temp file first
    # As the lab requires, manifest must be created atomically.
    # So, if fails in the half way, the whole task fails rather than generating half manifest.
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        dir=MANIFEST_DIR,
        suffix=".tmp",
        encoding="utf-8",
    ) as tmp_file:
        
        temp_path = Path(tmp_file.name)

        # Walk through FLAC structure to find the transcripts, since transcripts only exists in FLAC
        for root, _, files in os.walk(FLAC_ROOT):  
            for file in files:
                
                # ---------- LibriSpeech ----------
                if file.endswith(".trans.txt"): # all the transcripts file endwith .trans.txt
                    trans_path = Path(root) / file

                    with open(trans_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue

                            utt_stem, ref_text = line.split(" ", 1)

                            wav_path = (
                                WAV_ROOT
                                / Path(root).relative_to(FLAC_ROOT)
                                / f"{utt_stem}.wav"
                            )
                            process_item(tmp_file, wav_path, utt_stem, ref_text, LANG)

                            
                # ---------- MLS ----------
                if file == "transcripts.txt":
                    trans_path = Path(root) / file

                    with open(trans_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue

                            utt_id, ref_text = line.split("\t", 1)
                            speaker, book, utt = utt_id.split("_")
                            utt_stem = f"{speaker}-{book}-{utt}"

                            wav_path = (
                                WAV_ROOT
                                / "mls"
                                / "dev"
                                / speaker
                                / book
                                / f"{utt_stem}.wav"
                            )
                            process_item(tmp_file, wav_path, utt_stem, ref_text, LANG)

        
    # Atomic rename
    shutil.move(str(temp_path), MANIFEST_PATH)

    print("Clean manifest created successfully.")
    print(f"Manifest path: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()





