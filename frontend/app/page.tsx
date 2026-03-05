"use client";

import { useEffect, useState, useCallback } from "react";
import AudioPlayer from "./components/AudioPlayer";
import ScriptViewer, { ScriptEntry } from "./components/ScriptViewer";

const LESSON_ID = "lesson1";
const TRANSLATION_LANG = "en";

export default function Home() {
  const [script, setScript] = useState<ScriptEntry[]>([]);
  const [pinyin, setPinyin] = useState<string[]>([]);
  const [translations, setTranslations] = useState<string[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [showPinyin, setShowPinyin] = useState(true);
  const [showTranslation, setShowTranslation] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [scriptRes, pinyinRes, translationsRes] = await Promise.all([
          fetch(`/api/lessons/${LESSON_ID}/script`),
          fetch(`/api/lessons/${LESSON_ID}/pinyin`),
          fetch(`/api/lessons/${LESSON_ID}/translations/${TRANSLATION_LANG}`),
        ]);
        if (!scriptRes.ok) throw new Error(`Script: HTTP ${scriptRes.status}`);
        setScript(await scriptRes.json());
        if (pinyinRes.ok) setPinyin(await pinyinRes.json());
        if (translationsRes.ok) setTranslations(await translationsRes.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load lesson");
      }
    };
    load();
  }, []);

  const handleTimeUpdate = useCallback((t: number) => setCurrentTime(t), []);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  if (!script.length) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-zinc-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <header className="sticky top-0 z-10 bg-zinc-50/80 dark:bg-zinc-950/80 backdrop-blur border-b border-zinc-200 dark:border-zinc-800 px-6 py-3">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            每天中文 — Lesson 1
          </h1>
          <div className="flex gap-2">
            <button
              onClick={() => setShowPinyin((v) => !v)}
              className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
                showPinyin
                  ? "bg-zinc-900 text-white border-zinc-900 dark:bg-white dark:text-zinc-900 dark:border-white"
                  : "text-zinc-500 border-zinc-300 dark:border-zinc-700 hover:border-zinc-500"
              }`}
            >
              Pinyin
            </button>
            <button
              onClick={() => setShowTranslation((v) => !v)}
              className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
                showTranslation
                  ? "bg-zinc-900 text-white border-zinc-900 dark:bg-white dark:text-zinc-900 dark:border-white"
                  : "text-zinc-500 border-zinc-300 dark:border-zinc-700 hover:border-zinc-500"
              }`}
            >
              Translation
            </button>
          </div>
        </div>
      </header>

      <ScriptViewer
        script={script}
        pinyin={pinyin}
        translations={translations}
        currentTime={currentTime}
        showPinyin={showPinyin}
        showTranslation={showTranslation}
      />

      <AudioPlayer
        src={`/api/audio/${LESSON_ID}.mp3`}
        onTimeUpdate={handleTimeUpdate}
      />
    </div>
  );
}
