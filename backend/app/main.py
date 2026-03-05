import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="LanguagePodcast API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent.parent / "data" / "samples"


@app.get("/api/hello")
def hello():
    return {"message": "Hello from LanguagePodcast backend!"}


@app.get("/api/lessons")
def list_lessons():
    return [
        {"id": f.stem, "title": f.stem}
        for f in sorted(DATA_DIR.glob("*.json"))
    ]


@app.get("/api/lessons/{lesson_id}/script")
def get_script(lesson_id: str):
    path = DATA_DIR / f"{lesson_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Lesson not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/lessons/{lesson_id}/translations")
def get_translations(lesson_id: str):
    path = DATA_DIR / f"{lesson_id}_translations.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Translations not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/lessons/{lesson_id}/pinyin")
def get_pinyin(lesson_id: str):
    path = DATA_DIR / f"{lesson_id}_pinyin.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Pinyin not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/lessons/{lesson_id}/translations/{lang}")
def get_translations(lesson_id: str, lang: str):
    path = DATA_DIR / f"{lesson_id}_{lang}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Translation '{lang}' not found")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    path = DATA_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(str(path), media_type="audio/mpeg")
