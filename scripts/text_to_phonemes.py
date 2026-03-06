import json
import subprocess
from pathlib import Path
import tempfile
import shutil
import argparse

# def text_to_phonemes(text: str, lang:str) -> str:
#     result = subprocess.run(
#         ["espeak-ng", "-q", "--ipa", "-v", lang, text],  # quiet mode, IPA output, input text
#         capture_output=True,
#     )
#     phon = result.stdout.decode("utf-8").strip() # ensure utf-8 encoding! or the results will be wired!
#     phon = " ".join(phon.split())
#     return phon

# The following version removes stress also, but it may not be necessary, so is provided here as an option.
def text_to_phonemes(text: str, lang:str) -> str:
    result = subprocess.run(
        ["espeak-ng", "-q", "--ipa", "-v", lang, text],  # quiet mode, IPA output, input text
        capture_output=True,
    )
    phon = result.stdout.decode("utf-8").strip() # ensure utf-8 encoding! or the results will be wierd!
    # phon = " ".join(phon.split()) # normalize whitespace
    phon = phon.replace("ˈ", "").replace("ˌ", "") # remove stress markers, not split by words but by phoneme tokens
    phon = phon.replace("ː", "")
    phon = phon.replace(" ", "")
    phon = " ".join(list(phon)) 
    return phon

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()

    LANG = args.lang

    input_manifest = Path(f"data/manifests/{LANG}/clean.jsonl")
    output_manifest = Path(f"data/manifests/{LANG}/phoneme.jsonl")

    output_manifest.parent.mkdir(parents=True, exist_ok=True)

    # manifests must be created atomically!
    with tempfile.NamedTemporaryFile(
        mode="w",
        delete=False,
        dir=output_manifest.parent,
        suffix=".tmp",
        encoding="utf-8",
    ) as tmp_file:
    
        tmp_path = Path(tmp_file.name)

        with open(input_manifest, "r", encoding="utf-8") as fin:
            
            for line in fin:   # interate through each line (utterance) in the input manifest file
                item = json.loads(line)  # parse! parse json line into dictionary for field access

                text = item["ref_text"]
                phon = text_to_phonemes(text, LANG)  # convert text to IPA phonemes using espeak-ng

                item["ref_phon"] = phon # add phoneme field to the dictionary

                tmp_file.write(json.dumps(item, ensure_ascii=False) + "\n")  # update JSON object in output manifest, one per line
    tmp_path.replace(output_manifest)

    print("successfully done text to phonemes.")
    print("Output:", output_manifest)

if __name__ =="__main__":
    main()
