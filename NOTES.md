# LanguagePodcast — Notes

## Features
- [x] Audio playback with seek bar
- [x] Character-level script display synchronized with audio
- [x] Pinyin display (toggleable)
- [x] English translation display per segment (toggleable)
- [x] Google Drive sync (upload/download via `scripts/gdrive.py`)
- [x] Whisper-based audio-script alignment (`scripts/align.py`)
- [x] Server-side pinyin and translation generation (`scripts/enrich.py`)

## Bugs
- [ ] Whisper model generates incorrect timestamps — causes highlight to be off or missing during playback

## Planned
- [ ] Support multiple translation languages on the UI (currently hardcoded to `en`)
- [ ] Speech evaluation / pronunciation feedback
- [ ] Automatic audio-script alignment improvements (e.g. WhisperX forced alignment)
- [ ] User accounts and lesson management
- [ ] Mobile support
