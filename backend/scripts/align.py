#!/usr/bin/env python3
"""
Generate character-level timestamps from audio + raw script using Whisper.

Usage:
    python scripts/align.py <audio_file> <raw_script_file> [output_json]

Example:
    python scripts/align.py data/samples/lesson1.mp3 data/samples/lesson1_raw.txt data/samples/lesson1.json

Output JSON format (one entry per Chinese character):
    [
      { "speaker": "李明", "hanzi": "朋", "start": 0.52, "end": 0.68 },
      ...
    ]
"""

# PYTHON_ARGCOMPLETE_OK
import re
import json
import sys
import time
import argparse
import difflib
from pathlib import Path


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_raw_script(text: str) -> list[dict]:
    """Return list of {speaker, text} from 'Speaker: text' lines."""
    entries = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^([^:：(（]+)[：:]\s*(.+)$', line)
        if m:
            entries.append({"speaker": m.group(1).strip(), "text": m.group(2).strip()})
    return entries


def is_hanzi(ch: str) -> bool:
    return '\u4e00' <= ch <= '\u9fff'


def extract_chars(entries: list[dict]) -> list[dict]:
    """Flatten script into one dict per Chinese character with speaker tag."""
    result = []
    for entry in entries:
        for ch in entry["text"]:
            if is_hanzi(ch):
                result.append({"speaker": entry["speaker"], "hanzi": ch})
    return result


# ---------------------------------------------------------------------------
# Whisper word → individual character expansion
# ---------------------------------------------------------------------------

def expand_words(words: list[dict]) -> list[dict]:
    """
    Whisper returns word-level timestamps. For Chinese, 'words' can be
    multi-character. Expand each word into per-character entries by splitting
    the word's time span evenly.
    """
    chars = []
    for w in words:
        text = w["word"].strip()
        hanzi_chars = [ch for ch in text if is_hanzi(ch)]
        if not hanzi_chars:
            continue
        duration = (w["end"] - w["start"]) / len(hanzi_chars)
        for i, ch in enumerate(hanzi_chars):
            chars.append({
                "hanzi": ch,
                "start": round(w["start"] + i * duration, 3),
                "end":   round(w["start"] + (i + 1) * duration, 3),
            })
    return chars


# ---------------------------------------------------------------------------
# Sequence alignment (LCS-based)
# ---------------------------------------------------------------------------

def align_sequences(whisper_chars: list[dict], raw_chars: list[dict]) -> list[dict]:
    """
    Use difflib SequenceMatcher to align Whisper output characters to raw
    script characters. This handles insertions/deletions in Whisper's output.

    Returns one entry per raw character with start/end filled in where
    Whisper has a matching character, and interpolated where it doesn't.
    """
    whisper_text = "".join(c["hanzi"] for c in whisper_chars)
    raw_text     = "".join(c["hanzi"] for c in raw_chars)

    matcher = difflib.SequenceMatcher(None, whisper_text, raw_text, autojunk=False)

    # Build a mapping: raw_index → whisper_index (None if no match)
    raw_to_whisper: list[int | None] = [None] * len(raw_chars)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                raw_to_whisper[j1 + offset] = i1 + offset

    # Build result; interpolate timestamps for unmatched raw chars
    result = []
    for j, raw_ch in enumerate(raw_chars):
        wi = raw_to_whisper[j]
        if wi is not None:
            wc = whisper_chars[wi]
            result.append({
                "speaker": raw_ch["speaker"],
                "hanzi":   raw_ch["hanzi"],
                "start":   wc["start"],
                "end":     wc["end"],
            })
        else:
            # Interpolate from nearest matched neighbours
            prev_t = _find_prev_time(result)
            next_t = _find_next_time(raw_to_whisper, whisper_chars, j)
            mid = round((prev_t + next_t) / 2, 3)
            result.append({
                "speaker": raw_ch["speaker"],
                "hanzi":   raw_ch["hanzi"],
                "start":   mid,
                "end":     mid,
            })

    return result


def _find_prev_time(result: list[dict]) -> float:
    for entry in reversed(result):
        if entry["end"] > 0:
            return entry["end"]
    return 0.0


def _find_next_time(
    raw_to_whisper: list[int | None],
    whisper_chars: list[dict],
    from_j: int,
) -> float:
    for j in range(from_j + 1, len(raw_to_whisper)):
        wi = raw_to_whisper[j]
        if wi is not None:
            return whisper_chars[wi]["start"]
    return whisper_chars[-1]["end"] if whisper_chars else 0.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import argcomplete

    parser = argparse.ArgumentParser(
        description="Generate character-level timestamps from audio + raw script using Whisper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("audio_file", help="Path to audio file (e.g. data/samples/lesson1.mp3)")
    parser.add_argument("script_file", help="Path to raw script text file (e.g. data/samples/lesson1_raw.txt)")
    parser.add_argument("output_json", nargs="?", help="Output JSON path (default: same as audio with .json extension)")
    parser.add_argument("--model", default="large-v3", choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper model size (default: large-v3)")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    audio_path  = Path(args.audio_file)
    script_path = Path(args.script_file)
    output_path = Path(args.output_json) if args.output_json else audio_path.with_suffix(".json")

    # --- Transcribe with Whisper ---
    try:
        import whisper
    except ImportError:
        print("Error: openai-whisper not installed. Run: pip install openai-whisper")
        sys.exit(1)

    whisper_model = args.model
    t0 = time.time()

    def elapsed() -> str:
        return f"{time.time() - t0:.1f}s"

    def step(n: int, total: int, label: str) -> None:
        print(f"\n[{n}/{total}] {label}")

    TOTAL_STEPS = 4

    # --- Step 1: Load model ---
    step(1, TOTAL_STEPS, f"Loading Whisper model ({whisper_model}) ...")
    model = whisper.load_model(whisper_model)
    print(f"    Done ({elapsed()})")

    # --- Step 2: Transcribe ---
    # verbose=None shows Whisper's built-in tqdm progress bar (one tick per audio chunk)
    step(2, TOTAL_STEPS, f"Transcribing {audio_path.name} ...")
    audio = whisper.load_audio(str(audio_path))
    duration = len(audio) / whisper.audio.SAMPLE_RATE
    print(f"    Audio duration: {duration/60:.1f} min")
    result = model.transcribe(
        str(audio_path),
        language="zh",
        word_timestamps=True,
        verbose=None,
    )
    all_words: list[dict] = []
    for seg in result["segments"]:
        all_words.extend(seg.get("words", []))
    whisper_chars = expand_words(all_words)
    print(f"    Whisper produced {len(whisper_chars)} Chinese characters ({elapsed()})")

    # --- Step 3: Parse raw script ---
    step(3, TOTAL_STEPS, f"Parsing raw script {script_path.name} ...")
    raw_text    = script_path.read_text(encoding="utf-8")
    raw_entries = parse_raw_script(raw_text)
    raw_chars   = extract_chars(raw_entries)
    print(f"    Raw script has {len(raw_chars)} Chinese characters ({elapsed()})")

    # --- Step 4: Align ---
    step(4, TOTAL_STEPS, "Aligning sequences ...")
    aligned = align_sequences(whisper_chars, raw_chars)
    print(f"    Aligned {len(aligned)} characters ({elapsed()})")

    # --- Write output ---
    output_path.write_text(
        json.dumps(aligned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nDone. Written {len(aligned)} entries → {output_path}  (total: {elapsed()})")


if __name__ == "__main__":
    main()
