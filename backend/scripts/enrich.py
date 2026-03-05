#!/usr/bin/env python3
"""
Enrich an aligned script JSON with pinyin and/or translations.
All output files are stored alongside the input file.

Output files:
  {stem}_pinyin.json         — array of pinyin strings, index-matched to script array
  {stem}_{lang}.json         — array of translation strings, one per speaker segment

Usage:
  # Generate pinyin
  python scripts/enrich.py data/samples/lesson1.json --pinyin

  # Generate English translation
  python scripts/enrich.py data/samples/lesson1.json --translate en

  # Generate Vietnamese translation
  python scripts/enrich.py data/samples/lesson1.json --translate vi

  # Both at once
  python scripts/enrich.py data/samples/lesson1.json --pinyin --translate en
"""

import sys
import json
import time
import argparse
from pathlib import Path

# Lang codes supported by deep-translator GoogleTranslator
LANG_MAP = {
    "en": "english",
    "vi": "vietnamese",
    "ja": "japanese",
    "ko": "korean",
    "fr": "french",
}


def group_segments(entries: list[dict]) -> list[dict]:
    """Group consecutive same-speaker entries into segments."""
    segments = []
    current = None
    for entry in entries:
        if current is None or entry["speaker"] != current["speaker"]:
            current = {"speaker": entry["speaker"], "text": ""}
            segments.append(current)
        current["text"] += entry["hanzi"]
    return segments


def generate_pinyin(entries: list[dict], output_path: Path) -> None:
    from pypinyin import pinyin, Style
    result = [
        pinyin(e["hanzi"], style=Style.TONE)[0][0]
        for e in entries
    ]
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Pinyin → {output_path}  ({len(result)} entries)")


def generate_translations(entries: list[dict], lang: str, output_path: Path) -> None:
    from deep_translator import GoogleTranslator

    dest = LANG_MAP.get(lang, lang)
    translator = GoogleTranslator(source="zh-CN", target=dest)
    segments = group_segments(entries)
    translations = []

    print(f"Translating {len(segments)} segments → {lang} ...")
    for i, seg in enumerate(segments):
        try:
            translation = translator.translate(seg["text"])
        except Exception as e:
            print(f"  Warning: segment {i} failed: {e}")
            translation = ""
        translations.append(translation)
        print(f"  [{i+1}/{len(segments)}] {seg['text'][:20]}… → {translation[:50]}")
        time.sleep(0.5)

    output_path.write_text(
        json.dumps(translations, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Translations ({lang}) → {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Path to aligned script JSON (e.g. data/samples/lesson1.json)")
    parser.add_argument("--pinyin", action="store_true", help="Generate pinyin file")
    parser.add_argument("--translate", metavar="LANG", choices=list(LANG_MAP.keys()),
                        help="Generate translation file for language code (e.g. en, vi)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    if not args.pinyin and not args.translate:
        parser.print_help()
        sys.exit(1)

    entries = json.loads(input_path.read_text(encoding="utf-8"))

    if args.pinyin:
        output_path = input_path.with_name(f"{input_path.stem}_pinyin.json")
        generate_pinyin(entries, output_path)

    if args.translate:
        lang = args.translate.lower()
        output_path = input_path.with_name(f"{input_path.stem}_{lang}.json")
        generate_translations(entries, lang, output_path)

    print("Done.")


if __name__ == "__main__":
    main()
