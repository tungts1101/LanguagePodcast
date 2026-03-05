# Chinese Shadowing Practice Platform

## Running Locally

**Backend** (from `backend/`):
```bash
cd backend
python -m uvicorn app.main:app --reload
# runs at http://localhost:8000
```

**Frontend** (from `frontend/`):
```bash
cd frontend
npm install   # first time only
npm run dev
# runs at http://localhost:3000
```

---

## Project Overview

This project is a web application that helps users practice **Chinese listening and speaking using the shadowing method**.

Shadowing is a language learning technique where learners **listen to audio and immediately repeat what they hear**, mimicking natural conversation.

The platform provides **themed audio lessons with synchronized scripts**, allowing learners to follow the audio visually and practice pronunciation.

The system also allows **users to upload their own lessons**, which will eventually be automatically synchronized using AI alignment.

The project is designed so that both **learning content and user-generated content** can coexist.

---

# MVP Goal

The first version of the product focuses only on **listening practice with synchronized scripts**.

The MVP features are:

1. Play lesson audio
2. Display synchronized script
3. Highlight characters while the audio is playing
4. Toggle the visibility of:
   - Pinyin
   - English translation

Features such as **speech evaluation** and **automatic audio alignment** are planned but may not exist in the initial version.

---

# Core Features

## 1. Audio + Script Shadowing

Each lesson contains:

- an audio file
- Chinese script
- pinyin
- English translation
- timestamps

Example script entry:

你好  
nǐ hǎo  
hello  

Displayed layout:

pinyin (top)  
hanzi (middle)  
translation (bottom)

Example visual representation:

nǐ hǎo  
你好  
hello  

This layout helps learners simultaneously connect:

- pronunciation
- written characters
- meaning

---

## 2. Character-Level Highlighting

While the audio plays, the script will highlight **character by character**.

Example:

nǐ hǎo  
[你] 好  
hello  

Then:

nǐ hǎo  
你 [好]  
hello  

This requires timestamps associated with each character.

---

## 3. Toggle Learning Layers

Users can toggle different learning layers.

Available layers:

- Hanzi
- Pinyin
- English translation

Possible display modes:

1. Hanzi only
2. Hanzi + Pinyin
3. Hanzi + Translation
4. Hanzi + Pinyin + Translation

This allows learners to gradually increase difficulty.

---

## 4. User Lesson Upload

Users can upload their own lessons.

Uploads include:

- audio file
- script

Script format example:

你好 | nǐ hǎo | hello  
你好吗 | nǐ hǎo ma | how are you  

Uploaded lessons may be:

- private
- public (shared with other users)

---

## 5. Automatic Audio-Script Synchronization (Planned)

When users upload a lesson, the system will eventually perform **automatic audio-script synchronization**.

Planned alignment pipeline:

audio upload  
↓  
speech recognition  
↓  
match transcript  
↓  
generate timestamps  

Possible technologies:

- Whisper
- forced alignment tools

This feature may not be available in the initial MVP but the system should be designed to support it.

---

## 6. Speaking Practice (Planned)

Future versions will allow users to **practice speaking by repeating the audio**.

The system will:

1. record user speech
2. analyze pronunciation
3. detect mispronounced words
4. provide pronunciation feedback

This will likely use:

- specialized speech evaluation APIs
- or dedicated pronunciation models.

---

# Target Platform

Current platform:

Web application.

Future platform:

Mobile application.

The architecture should remain flexible so mobile clients can be added later.

---

# Tech Stack

Frontend:

- Next.js
- React
- TypeScript

Backend:

- FastAPI (Python)

Database:

- SQLite (initial development)
- PostgreSQL (planned for production)

Speech / AI processing:

- Whisper (planned)
- Speech evaluation APIs

---

# System Architecture

Browser  
↓  
Next.js Frontend  
↓  
FastAPI Backend  
↓  
Database  

AI processing components will be integrated into the backend services.

---

# Project Structure

## Frontend (Next.js)

frontend

app  
components  
hooks  
lib  
types  
styles  

Example components:

AudioPlayer  
ScriptViewer  
CharacterHighlight  
PinyinRow  
TranslationRow  

---

## Backend (FastAPI)

backend

app  
main.py  

api  
routes for lessons and scripts  

services  
alignment_service.py  
pronunciation_service.py  

models  
database models  

database  
database connection and migrations

---

# Script Data Model

Internal representation of script entries.

Each entry represents **one character**.

Example:

[
  {
    "hanzi": "你",
    "pinyin": "nǐ",
    "translation": "you",
    "start": 0.52,
    "end": 0.80
  },
  {
    "hanzi": "好",
    "pinyin": "hǎo",
    "translation": "good",
    "start": 0.80,
    "end": 1.10
  }
]

---

# Database Schema (Initial)

Users

id  
email  
created_at  

Lessons

id  
title  
audio_url  
owner_id  
is_public  
created_at  

Scripts

id  
lesson_id  
hanzi  
pinyin  
translation  
start_time  
end_time  
position  

---

# Development Principles

## 1. Clear Frontend / Backend Responsibilities

Frontend handles:

- UI
- audio playback
- script highlighting
- user interaction

Backend handles:

- lesson management
- data storage
- alignment processing
- speech evaluation

---

## 2. Keep Components Small

Avoid very large components.

Prefer splitting functionality into reusable components.

Example components:

ScriptViewer  
CharacterHighlight  
PinyinRow  
TranslationRow  

---

## 3. Avoid Hardcoding Data

Script and lesson data must always come from the backend API.

---

## 4. Prepare for Future AI Features

Even if alignment and pronunciation are not implemented yet, the architecture should allow easy integration.

---

# Development Priorities

Current priority (MVP):

1. Audio playback
2. Script display
3. Character highlighting
4. Toggle pinyin and translation

Later priorities:

5. Lesson upload
6. Automatic audio alignment
7. Speaking evaluation

---

# What Claude Should Help With

Claude can assist with:

- building UI components
- audio synchronization logic
- API design
- database schema
- backend services
- AI integration
- refactoring and optimization

Claude should **follow the architecture and features defined in this README** and should not assume additional functionality unless specified.

---

# Future Expansion

Potential future features:

- AI-generated lessons
- conversational practice scenarios
- community lesson marketplace
- mobile applications
- advanced pronunciation scoring