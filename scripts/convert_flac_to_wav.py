import soundfile as sf
import argparse
from pathlib import Path

""" 
I downloaded dev-clean.tar.gz from LibriSpeechh ASR corpus (en).
Other languages can be obtained from Multilingual LibriSpeech (MLS), so that this code is for LibriSpeech and MLS.
Since files needed are flac, to continue this analysis, 
the first step is to convert flac into wav.
"""


def convert_one(flac_path: Path, wav_path: Path):
    if wav_path.exists():
        return
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    audio, sr = sf.read(flac_path)  # load audio file and return numpy array, and sample rate

    if audio.ndim != 1:
        raise ValueError(f"{flac_path} is not mono") # check if the audio is mono to match the model's requirement: model expects single channel

    if sr != 16000: # important! verify if sample rate matches model requirement (later I will use wav2vec2phonemes which expects 16kHz)
        raise ValueError(f"{flac_path} has sr={sr}, expected 16000")

    sf.write(wav_path, audio, sr)

# ---------- LIBRISPEECH ----------

def convert_librispeech(lang):

    FLAC_ROOT = Path(f"data/raw/{lang}/flac/LibriSpeech/dev-clean")
    WAV_ROOT = Path(f"data/raw/{lang}/wav/LibriSpeech/dev-clean")

    trans_files = list(FLAC_ROOT.rglob("*.trans.txt"))

    count = 0

    for tf in trans_files:

        with open(tf, encoding="utf-8") as f:
            for line in f:

                utt_id, _ = line.strip().split(" ", 1)

                speaker = utt_id.split("-")[0]
                chapter = utt_id.split("-")[1]

                flac_path = FLAC_ROOT / speaker / chapter / f"{utt_id}.flac"
                wav_path = WAV_ROOT / speaker / chapter / f"{utt_id}.wav"

                convert_one(flac_path, wav_path)

                count += 1

    print(f"Converted {count} LibriSpeech files")

# ---------- MLS ----------

def convert_mls(lang):

    FLAC_ROOT = Path(f"data/raw/{lang}/flac/mls/dev/audio")
    WAV_ROOT = Path(f"data/raw/{lang}/wav/mls/dev")

    transcript_file = Path(f"data/raw/{lang}/flac/mls/dev/transcripts.txt")

    count = 0

    with open(transcript_file, encoding="utf-8") as f:

        for line in f:

            utt_id, _ = line.strip().split("\t", 1)

            # MLS id example:
            # 577_394_000000
            speaker, book, utt = utt_id.split("_")

            # convert to LibriSpeech style
            utt_stem = f"{speaker}-{book}-{utt}"

            flac_path = FLAC_ROOT / speaker / book / f"{utt_id}.flac"
            wav_path = WAV_ROOT / speaker / book / f"{utt_stem}.wav"

            convert_one(flac_path, wav_path)

            count += 1

    print(f"Converted {count} MLS files")

# ---------- MAIN ----------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--lang",
        required=True,
        help="Language code (e.g. en, fr)"
    )

    parser.add_argument(
        "--dataset",
        choices=["librispeech", "mls"],
        required=True,
        help="Dataset type"
    )

    args = parser.parse_args()

    if args.dataset == "librispeech":
        convert_librispeech(args.lang)

    elif args.dataset == "mls":
        convert_mls(args.lang)

if __name__ == "__main__":
    main()

