# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Chinese shadowing practice platform — a web app for listening practice with synchronized character-level scripts. Users listen to audio and follow along with highlighted Hanzi, Pinyin, and English translation.

## Tech Stack

- **Frontend:** Next.js + React + TypeScript (`frontend/`)
- **Backend:** FastAPI (Python) (`backend/`)
- **Database:** SQLite (dev) → PostgreSQL (prod)
- **AI (planned):** Whisper for alignment, speech evaluation APIs for pronunciation

## Commands

### Frontend

```bash
cd frontend
npm install
npm run dev       # Start dev server
npm run build     # Production build
npm run lint      # Lint
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload   # Start dev server
```

## Architecture

```
Browser → Next.js Frontend → FastAPI Backend → SQLite/PostgreSQL
                                    ↓
                            AI Services (alignment, pronunciation)
```

**Frontend responsibilities:** UI rendering, audio playback, character highlighting, user interaction.
**Backend responsibilities:** Lesson management, data storage, alignment processing, speech evaluation.

## Core Data Model

Script entries are **character-level** (one object per Hanzi character):

```json
{
  "hanzi": "你",
  "pinyin": "nǐ",
  "translation": "you",
  "start": 0.52,
  "end": 0.80
}
```

Database tables: `Users`, `Lessons` (title, audio_url, owner_id, is_public), `Scripts` (lesson_id, hanzi, pinyin, translation, start_time, end_time, position).

## Display Layout

```
nǐ hǎo        ← Pinyin (top)
你 [好]        ← Hanzi (middle), character highlighted during playback
hello          ← Translation (bottom)
```

Users toggle pinyin/translation visibility independently to adjust difficulty.

## MVP Scope

1. Audio playback
2. Synchronized script display with character-level highlighting
3. Toggle pinyin and translation visibility

**Not in MVP:** Speech evaluation, automatic audio-script alignment (Whisper/forced alignment). Design backend services (`alignment_service.py`, `pronunciation_service.py`) to allow future integration without requiring implementation now.

## Key Frontend Components

- `AudioPlayer` — controls playback
- `ScriptViewer` — renders the full script
- `CharacterHighlight` — highlights the active character based on audio timestamp
- `PinyinRow`, `TranslationRow` — toggleable display layers

## Principles

- All lesson/script data comes from the backend API — never hardcode content.
- Keep components small and focused; split reusable pieces out of larger components.
- Architecture must remain flexible for future mobile clients (avoid web-only assumptions in the API layer).
