"use client";

import { useEffect, useRef } from "react";

export interface ScriptEntry {
  speaker: string;
  hanzi: string;
  start: number;
  end: number;
}

interface Segment {
  speaker: string;
  chars: ScriptEntry[];
  startIdx: number;
}

interface Props {
  script: ScriptEntry[];
  pinyin: string[];          // index-matched to script
  translations: string[];    // one per segment, in order
  currentTime: number;
  showPinyin: boolean;
  showTranslation: boolean;
}

function groupBySpeaker(script: ScriptEntry[]): Segment[] {
  const segments: Segment[] = [];
  let current: Segment | null = null;
  script.forEach((entry, i) => {
    if (!current || current.speaker !== entry.speaker) {
      current = { speaker: entry.speaker, chars: [], startIdx: i };
      segments.push(current);
    }
    current.chars.push(entry);
  });
  return segments;
}

function findActiveIndex(script: ScriptEntry[], time: number): number {
  let lo = 0;
  let hi = script.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (script[mid].end <= time) lo = mid + 1;
    else if (script[mid].start > time) hi = mid - 1;
    else return mid;
  }
  return -1;
}

export default function ScriptViewer({
  script,
  pinyin,
  translations,
  currentTime,
  showPinyin,
  showTranslation,
}: Props) {
  const activeRef = useRef<HTMLSpanElement>(null);
  const activeIdx = findActiveIndex(script, currentTime);
  const segments = groupBySpeaker(script);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, [activeIdx]);

  return (
    <div className="max-w-3xl mx-auto px-6 py-8 pb-28 space-y-6">
      {segments.map((seg, si) => {
        const globalStart = seg.startIdx;
        const translation = translations[si] ?? "";

        return (
          <div key={si} className="flex gap-4">
            {/* Speaker label */}
            <span className="text-sm font-medium text-zinc-400 dark:text-zinc-500 w-12 shrink-0 text-right pt-1">
              {seg.speaker}
            </span>

            <div className="flex flex-col gap-1">
              {/* Characters */}
              <div className="flex flex-wrap">
                {seg.chars.map((char, ci) => {
                  const globalIdx = globalStart + ci;
                  const isActive = globalIdx === activeIdx;
                  const py = pinyin[globalIdx] ?? "";

                  return (
                    <span key={ci} ref={isActive ? activeRef : undefined} className="flex flex-col items-center mx-0.5">
                      {/* Pinyin — always takes space to avoid layout shift */}
                      <span
                        className={`text-xs leading-tight text-zinc-400 dark:text-zinc-500 transition-opacity duration-150 ${
                          showPinyin ? "opacity-100" : "opacity-0"
                        }`}
                      >
                        {py}
                      </span>

                      {/* Hanzi — only this is highlighted */}
                      <span
                        className={`text-2xl leading-snug transition-colors ${
                          isActive
                            ? "bg-yellow-300 dark:bg-yellow-500 dark:text-zinc-900 rounded px-0.5"
                            : "text-zinc-800 dark:text-zinc-200"
                        }`}
                      >
                        {char.hanzi}
                      </span>
                    </span>
                  );
                })}
              </div>

              {/* Translation — segment level */}
              <p
                className={`text-sm text-zinc-500 dark:text-zinc-400 transition-opacity duration-150 ${
                  showTranslation && translation ? "opacity-100" : "opacity-0"
                }`}
              >
                {translation || "—"}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
