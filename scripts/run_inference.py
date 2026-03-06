# run_inference.py is for model prediction: audio->predict phoneme
# WARN: On wondows, before run run_inference.py, first run: export PHONEMIZER_ESPEAK_PATH="/c/Program Files/eSpeak NG/libespeak-ng.dll", because windowns search espeak not espeak-ng
# However, sometimes this does not word as well. 
# So I give an example on my Windows system, that is os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = r"C:\Program Files\eSpeak NG\libespeak-ng.dll", just for Windows.
# If run run_inference.py not on Windows, then ignore this line.
import json
import os
if "PHONEMIZER_ESPEAK_LIBRARY" not in os.environ:
    raise RuntimeError("Please set PHONEMIZER_ESPEAK_LIBRARY to your espeak-ng library path")
# os.environ["PHONEMIZER_ESPEAK_LIBRARY"] = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"

from pathlib import Path
import tempfile
import torch
import soundfile as sf
import argparse
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
"""
In huggingface, each model requires:
(1) processor/tokenizer to process input and output,
    so, Wav2Vec2Processor= feature extraction(raw waveform to nomalized tensor) + decode(model output ids to phoneme sequence)
(2) model class for nn. = moel itself
    CTC = Connectionist Temporal Classification, the output layer of speech recognition
    model = Wav2Vec2ForCTC.from_pretrained(...)

The steps are:
audio waveform -> wav2vec2 encoder -> CTC layer -> phoneme tokens
"""
 

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    LANG = args.lang

    INPUT_MANIFEST = Path(f"data/manifests/{LANG}/noisy.jsonl")
    OUTPUT_MANIFEST = Path(f"data/manifests/{LANG}/predictions.jsonl")

    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    # load the pretrained model
    processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-lv-60-espeak-cv-ft")
    model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-lv-60-espeak-cv-ft")

    model.eval()

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

                speech, sr = sf.read(wav_path)

                # Safety check (model requires 16kHz mono)
                if sr != 16000:
                    raise ValueError(f"Unexpected sample rate: {sr}")
                if speech.ndim != 1:
                    raise ValueError("Audio is not mono")

                inputs = processor(
                    speech, 
                    sampling_rate=sr, 
                    return_tensors="pt", 
                    padding=True,
                )

                with torch.no_grad(): # here, I do not compute gradients
                    logits = model(inputs.input_values).logits
                
                pred_ids = torch.argmax(logits, dim=-1)

                pred_phon = processor.batch_decode(pred_ids)[0].strip() # in case there are extra space to remove
                pred_phon = pred_phon.replace(" ", "")
                pred_phon = " ".join(list(pred_phon))

                new_item = item.copy()
                new_item["pred_phon"] = pred_phon

                tmp_file.write(json.dumps(new_item) + "\n")

    
    temp_path.replace(OUTPUT_MANIFEST)

    print("Inference completed.")
    print(f"Predictions manifest: {OUTPUT_MANIFEST}")

if __name__ == "__main__":
    main()

            



