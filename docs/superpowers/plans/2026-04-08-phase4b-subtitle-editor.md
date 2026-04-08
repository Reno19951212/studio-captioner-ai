# Phase 4B: Subtitle Editor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the full-featured subtitle editor page — video player with subtitle overlay, bilingual subtitle list with inline editing and confidence flags, audio waveform timeline with draggable segment boundaries, and a subtitle style customization panel.

**Architecture:** The Editor page (`/editor/:taskId`) is a three-panel layout: video player (left), subtitle list + tabs (right), waveform timeline (bottom). A Zustand `editorStore` holds subtitle segments, playback position, and selection state. Components communicate via the store — clicking a subtitle seeks the video, dragging a waveform boundary updates the segment timing, and the video player highlights the active subtitle. wavesurfer.js renders the waveform with region plugins for segment visualization.

**Tech Stack:** React 18, TypeScript, Zustand, wavesurfer.js (waveform), HTML5 `<video>` element (player), Tailwind CSS

**Working directory:** `/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/frontend`

**Existing API client:** `services/api.ts` already has `subtitles.get()`, `subtitles.save()`, `preview.videoUrl()`, `preview.waveformUrl()`. `SubtitleSegment` type already defined in `types/task.ts`.

---

## File Structure

```
frontend/src/
├── store/
│   └── editorStore.ts           # Subtitle data, selection, playback state
├── pages/
│   └── Editor.tsx               # Editor page (three-panel layout, data loading)
├── components/
│   └── editor/
│       ├── VideoPlayer.tsx      # HTML5 video + subtitle overlay + transport controls
│       ├── SubtitleList.tsx      # Bilingual subtitle list with inline editing + confidence flags
│       ├── Waveform.tsx         # wavesurfer.js waveform with segment regions
│       ├── StylePanel.tsx       # Font, size, color, outline, position controls
│       └── EditorToolbar.tsx    # Save, export, synthesize buttons
├── hooks/
│   └── useEditorKeyboard.ts    # Keyboard shortcuts for proofreading
```

---

### Task 1: Editor Store (Zustand)

**Files:**
- Create: `frontend/src/store/editorStore.ts`

- [ ] **Step 1: Create frontend/src/store/editorStore.ts**

```typescript
import { create } from "zustand";
import { subtitles as subtitlesApi } from "../services/api";
import type { SubtitleSegment } from "../types/task";

interface EditorState {
  taskId: number | null;
  segments: SubtitleSegment[];
  selectedIndex: number | null;
  currentTime: number; // milliseconds
  isPlaying: boolean;
  isDirty: boolean;
  confidenceScores: number[];

  // Actions
  loadSubtitles: (taskId: number) => Promise<void>;
  saveSubtitles: () => Promise<void>;
  updateSegment: (index: number, updates: Partial<SubtitleSegment>) => void;
  selectSegment: (index: number | null) => void;
  setCurrentTime: (ms: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setConfidenceScores: (scores: number[]) => void;
  getActiveSegmentIndex: () => number | null;
  selectNext: () => void;
  selectPrev: () => void;
}

export const useEditorStore = create<EditorState>((set, get) => ({
  taskId: null,
  segments: [],
  selectedIndex: null,
  currentTime: 0,
  isPlaying: false,
  isDirty: false,
  confidenceScores: [],

  loadSubtitles: async (taskId) => {
    const data = await subtitlesApi.get(taskId);
    set({ taskId, segments: data.segments, isDirty: false, selectedIndex: null });
  },

  saveSubtitles: async () => {
    const { taskId, segments } = get();
    if (!taskId) return;
    await subtitlesApi.save(taskId, segments);
    set({ isDirty: false });
  },

  updateSegment: (index, updates) => {
    const segments = [...get().segments];
    segments[index] = { ...segments[index], ...updates };
    set({ segments, isDirty: true });
  },

  selectSegment: (index) => set({ selectedIndex: index }),

  setCurrentTime: (ms) => set({ currentTime: ms }),

  setIsPlaying: (playing) => set({ isPlaying: playing }),

  setConfidenceScores: (scores) => set({ confidenceScores: scores }),

  getActiveSegmentIndex: () => {
    const { segments, currentTime } = get();
    return segments.findIndex(
      (s) => currentTime >= s.start_time && currentTime <= s.end_time
    );
  },

  selectNext: () => {
    const { selectedIndex, segments } = get();
    if (selectedIndex === null) {
      if (segments.length > 0) set({ selectedIndex: 0 });
    } else if (selectedIndex < segments.length - 1) {
      set({ selectedIndex: selectedIndex + 1 });
    }
  },

  selectPrev: () => {
    const { selectedIndex } = get();
    if (selectedIndex !== null && selectedIndex > 0) {
      set({ selectedIndex: selectedIndex - 1 });
    }
  },
}));
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/editorStore.ts
git commit -m "feat: editor Zustand store — subtitle data, selection, playback state"
```

---

### Task 2: Video Player Component

**Files:**
- Create: `frontend/src/components/editor/VideoPlayer.tsx`

- [ ] **Step 1: Create frontend/src/components/editor/VideoPlayer.tsx**

```tsx
import { useRef, useEffect, useCallback } from "react";
import { useEditorStore } from "../../store/editorStore";
import { preview } from "../../services/api";

interface VideoPlayerProps {
  taskId: number;
}

export function VideoPlayer({ taskId }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const {
    segments,
    currentTime,
    isPlaying,
    selectedIndex,
    setCurrentTime,
    setIsPlaying,
    getActiveSegmentIndex,
  } = useEditorStore();

  const activeIndex = getActiveSegmentIndex();
  const activeSegment = activeIndex >= 0 ? segments[activeIndex] : null;

  // Sync playback state
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying && video.paused) video.play();
    if (!isPlaying && !video.paused) video.pause();
  }, [isPlaying]);

  // Seek when selected segment changes
  useEffect(() => {
    const video = videoRef.current;
    if (!video || selectedIndex === null) return;
    const seg = segments[selectedIndex];
    if (seg) {
      video.currentTime = seg.start_time / 1000;
    }
  }, [selectedIndex, segments]);

  // Time update handler
  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (video) {
      setCurrentTime(Math.round(video.currentTime * 1000));
    }
  }, [setCurrentTime]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  };

  const formatTime = (ms: number) => {
    const totalSec = Math.floor(ms / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  };

  return (
    <div className="flex flex-col bg-black rounded-lg overflow-hidden h-full">
      {/* Video */}
      <div className="flex-1 relative flex items-center justify-center min-h-0">
        <video
          ref={videoRef}
          src={preview.videoUrl(taskId)}
          onTimeUpdate={handleTimeUpdate}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          className="max-w-full max-h-full object-contain"
          preload="metadata"
        />
        {/* Subtitle overlay */}
        {activeSegment && (
          <div className="absolute bottom-10 left-1/2 -translate-x-1/2 max-w-[80%] text-center">
            {activeSegment.translated_text && (
              <div className="bg-black/75 px-4 py-1 rounded text-white text-base mb-1">
                {activeSegment.translated_text}
              </div>
            )}
            <div className="bg-black/60 px-4 py-1 rounded text-zinc-300 text-sm">
              {activeSegment.text}
            </div>
          </div>
        )}
      </div>

      {/* Transport controls */}
      <div className="flex items-center justify-center gap-4 py-2 bg-zinc-900/80">
        <span className="text-xs text-zinc-500 w-12 text-right">{formatTime(currentTime)}</span>
        <button
          onClick={togglePlay}
          className="text-white hover:text-blue-400 text-lg w-8 text-center"
        >
          {isPlaying ? "⏸" : "▶"}
        </button>
        <span className="text-xs text-zinc-500 w-12">
          {videoRef.current ? formatTime(videoRef.current.duration * 1000 || 0) : "--:--"}
        </span>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/VideoPlayer.tsx
git commit -m "feat: VideoPlayer — HTML5 video with subtitle overlay + transport controls"
```

---

### Task 3: Subtitle List Component (Inline Editing + Confidence Flags)

**Files:**
- Create: `frontend/src/components/editor/SubtitleList.tsx`

- [ ] **Step 1: Create frontend/src/components/editor/SubtitleList.tsx**

```tsx
import { useRef, useEffect } from "react";
import { useEditorStore } from "../../store/editorStore";

const CONFIDENCE_THRESHOLD = 0.9;

function formatTimecode(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const msRem = ms % 1000;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(msRem).padStart(3, "0")}`;
}

export function SubtitleList() {
  const {
    segments,
    selectedIndex,
    confidenceScores,
    selectSegment,
    updateSegment,
  } = useEditorStore();
  const listRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to selected segment
  useEffect(() => {
    if (selectedIndex === null || !listRef.current) return;
    const el = listRef.current.children[selectedIndex] as HTMLElement | undefined;
    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selectedIndex]);

  return (
    <div ref={listRef} className="flex-1 overflow-auto space-y-1 p-2">
      {segments.map((seg, i) => {
        const isSelected = selectedIndex === i;
        const confidence = confidenceScores[i];
        const isLowConfidence = confidence !== undefined && confidence < CONFIDENCE_THRESHOLD;

        return (
          <div
            key={i}
            onClick={() => selectSegment(i)}
            className={`rounded-lg p-2 cursor-pointer transition text-sm ${
              isSelected
                ? "bg-blue-500/10 border border-blue-500/30"
                : isLowConfidence
                ? "bg-red-500/5 border border-red-500/20"
                : "bg-zinc-900 border border-transparent hover:bg-zinc-800"
            }`}
          >
            {/* Header: index + timecode + confidence */}
            <div className="flex justify-between items-center mb-1 text-xs">
              <span className="text-zinc-600">#{i + 1}</span>
              <div className="flex items-center gap-2">
                {isLowConfidence && (
                  <span className="text-red-400 font-medium">⚠ {Math.round(confidence * 100)}%</span>
                )}
                <span className="text-zinc-600">
                  {formatTimecode(seg.start_time)} → {formatTimecode(seg.end_time)}
                </span>
              </div>
            </div>

            {/* Source text */}
            {isSelected ? (
              <textarea
                value={seg.text}
                onChange={(e) => updateSegment(i, { text: e.target.value })}
                className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-200 text-sm resize-none mb-1"
                rows={2}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <div className="text-zinc-200 mb-1">{seg.text}</div>
            )}

            {/* Translation */}
            {isSelected ? (
              <textarea
                value={seg.translated_text || ""}
                onChange={(e) => updateSegment(i, { translated_text: e.target.value })}
                className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-blue-400 text-sm resize-none"
                rows={2}
                placeholder="Translation..."
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              seg.translated_text && (
                <div className={isLowConfidence ? "text-red-400" : "text-blue-400"}>
                  {seg.translated_text}
                </div>
              )
            )}
          </div>
        );
      })}
      {segments.length === 0 && (
        <p className="text-zinc-600 text-sm text-center py-8">No subtitles loaded</p>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/SubtitleList.tsx
git commit -m "feat: SubtitleList — bilingual inline editing + confidence flags"
```

---

### Task 4: Waveform Timeline Component

**Files:**
- Create: `frontend/src/components/editor/Waveform.tsx`

- [ ] **Step 1: Install wavesurfer.js**

```bash
cd frontend && npm install wavesurfer.js
```

- [ ] **Step 2: Create frontend/src/components/editor/Waveform.tsx**

```tsx
import { useRef, useEffect, useCallback } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin, { type Region } from "wavesurfer.js/dist/plugins/regions.js";
import { useEditorStore } from "../../store/editorStore";
import { preview } from "../../services/api";

interface WaveformProps {
  taskId: number;
}

const CONFIDENCE_THRESHOLD = 0.9;

export function Waveform({ taskId }: WaveformProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const {
    segments,
    selectedIndex,
    confidenceScores,
    currentTime,
    isPlaying,
    setCurrentTime,
    selectSegment,
    updateSegment,
  } = useEditorStore();

  // Initialize WaveSurfer
  useEffect(() => {
    if (!containerRef.current) return;

    const regions = RegionsPlugin.create();
    regionsRef.current = regions;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#4a4a5a",
      progressColor: "#60a5fa",
      cursorColor: "#ffffff",
      cursorWidth: 2,
      height: 80,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      url: preview.videoUrl(taskId),
      plugins: [regions],
    });

    ws.on("timeupdate", (time: number) => {
      setCurrentTime(Math.round(time * 1000));
    });

    ws.on("click", () => {
      // Click on waveform seeks the video — handled by timeupdate
    });

    wsRef.current = ws;

    return () => {
      ws.destroy();
      wsRef.current = null;
    };
  }, [taskId, setCurrentTime]);

  // Update regions when segments change
  useEffect(() => {
    const regions = regionsRef.current;
    if (!regions) return;

    // Clear existing regions
    regions.clearRegions();

    // Add segment regions
    segments.forEach((seg, i) => {
      const isLow = confidenceScores[i] !== undefined && confidenceScores[i] < CONFIDENCE_THRESHOLD;
      const isSelected = selectedIndex === i;

      regions.addRegion({
        start: seg.start_time / 1000,
        end: seg.end_time / 1000,
        color: isSelected
          ? "rgba(96, 165, 250, 0.2)"
          : isLow
          ? "rgba(248, 113, 113, 0.15)"
          : "rgba(52, 211, 153, 0.1)",
        drag: false,
        resize: true,
        id: `seg-${i}`,
      });
    });
  }, [segments, selectedIndex, confidenceScores]);

  // Handle region resize (drag boundaries)
  useEffect(() => {
    const regions = regionsRef.current;
    if (!regions) return;

    const handleRegionUpdate = (region: Region) => {
      const match = region.id.match(/^seg-(\d+)$/);
      if (!match) return;
      const idx = parseInt(match[1], 10);
      updateSegment(idx, {
        start_time: Math.round(region.start * 1000),
        end_time: Math.round(region.end * 1000),
      });
    };

    regions.on("region-updated", handleRegionUpdate);

    const handleRegionClick = (region: Region) => {
      const match = region.id.match(/^seg-(\d+)$/);
      if (!match) return;
      selectSegment(parseInt(match[1], 10));
    };

    regions.on("region-clicked", handleRegionClick);

    return () => {
      regions.un("region-updated", handleRegionUpdate);
      regions.un("region-clicked", handleRegionClick);
    };
  }, [updateSegment, selectSegment]);

  // Sync external seek (from subtitle list click)
  useEffect(() => {
    const ws = wsRef.current;
    if (!ws || !ws.getDuration()) return;
    const wsTime = ws.getCurrentTime() * 1000;
    if (Math.abs(wsTime - currentTime) > 500) {
      ws.seekTo(currentTime / 1000 / ws.getDuration());
    }
  }, [currentTime]);

  return (
    <div className="bg-zinc-900/50 border-t border-zinc-800">
      <div ref={containerRef} className="px-3 py-2" />
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

If build fails due to wavesurfer.js types, the regions plugin import path may need adjustment. Try `wavesurfer.js/dist/plugins/regions.esm.js` or check the installed version's exports.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/editor/Waveform.tsx frontend/package.json frontend/package-lock.json
git commit -m "feat: Waveform timeline — wavesurfer.js with draggable segment regions"
```

---

### Task 5: Style Panel Component

**Files:**
- Create: `frontend/src/components/editor/StylePanel.tsx`

- [ ] **Step 1: Create frontend/src/components/editor/StylePanel.tsx**

```tsx
import { useState } from "react";

export interface SubtitleStyleConfig {
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  outlineColor: string;
  outlineWidth: number;
  shadowColor: string;
  shadowOffset: number;
  bgEnabled: boolean;
  bgColor: string;
  bgOpacity: number;
  position: "bottom" | "top" | "middle";
}

const DEFAULT_STYLE: SubtitleStyleConfig = {
  fontFamily: "Noto Sans SC",
  fontSize: 24,
  fontColor: "#ffffff",
  outlineColor: "#000000",
  outlineWidth: 2,
  shadowColor: "#000000",
  shadowOffset: 1,
  bgEnabled: false,
  bgColor: "#000000",
  bgOpacity: 0.75,
  position: "bottom",
};

interface StylePanelProps {
  onChange?: (style: SubtitleStyleConfig) => void;
}

export function StylePanel({ onChange }: StylePanelProps) {
  const [style, setStyle] = useState<SubtitleStyleConfig>(DEFAULT_STYLE);

  const update = (patch: Partial<SubtitleStyleConfig>) => {
    const next = { ...style, ...patch };
    setStyle(next);
    onChange?.(next);
  };

  return (
    <div className="space-y-3 p-3 text-sm">
      <h3 className="font-medium text-zinc-300">Subtitle Style</h3>

      <div>
        <label className="block text-xs text-zinc-500 mb-1">Font Family</label>
        <select
          value={style.fontFamily}
          onChange={(e) => update({ fontFamily: e.target.value })}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100"
        >
          <option value="Noto Sans SC">Noto Sans SC</option>
          <option value="LXGW WenKai">LXGW WenKai</option>
          <option value="Arial">Arial</option>
          <option value="Microsoft YaHei">Microsoft YaHei</option>
        </select>
      </div>

      <div>
        <label className="block text-xs text-zinc-500 mb-1">Font Size: {style.fontSize}px</label>
        <input
          type="range" min={12} max={72} value={style.fontSize}
          onChange={(e) => update({ fontSize: Number(e.target.value) })}
          className="w-full"
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs text-zinc-500 mb-1">Font Color</label>
          <input type="color" value={style.fontColor}
            onChange={(e) => update({ fontColor: e.target.value })}
            className="w-full h-8 bg-zinc-800 border border-zinc-700 rounded cursor-pointer" />
        </div>
        <div>
          <label className="block text-xs text-zinc-500 mb-1">Outline Color</label>
          <input type="color" value={style.outlineColor}
            onChange={(e) => update({ outlineColor: e.target.value })}
            className="w-full h-8 bg-zinc-800 border border-zinc-700 rounded cursor-pointer" />
        </div>
      </div>

      <div>
        <label className="block text-xs text-zinc-500 mb-1">Outline Width: {style.outlineWidth}px</label>
        <input type="range" min={0} max={6} value={style.outlineWidth}
          onChange={(e) => update({ outlineWidth: Number(e.target.value) })}
          className="w-full" />
      </div>

      <div>
        <label className="block text-xs text-zinc-500 mb-1">Position</label>
        <select value={style.position} onChange={(e) => update({ position: e.target.value as SubtitleStyleConfig["position"] })}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100">
          <option value="bottom">Bottom</option>
          <option value="top">Top</option>
          <option value="middle">Middle</option>
        </select>
      </div>

      <div>
        <label className="flex items-center gap-2 text-xs text-zinc-500">
          <input type="checkbox" checked={style.bgEnabled}
            onChange={(e) => update({ bgEnabled: e.target.checked })} />
          Background Box
        </label>
        {style.bgEnabled && (
          <div className="mt-2 grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-zinc-500 mb-1">BG Color</label>
              <input type="color" value={style.bgColor}
                onChange={(e) => update({ bgColor: e.target.value })}
                className="w-full h-8 bg-zinc-800 border border-zinc-700 rounded cursor-pointer" />
            </div>
            <div>
              <label className="block text-xs text-zinc-500 mb-1">Opacity: {Math.round(style.bgOpacity * 100)}%</label>
              <input type="range" min={0} max={100} value={style.bgOpacity * 100}
                onChange={(e) => update({ bgOpacity: Number(e.target.value) / 100 })}
                className="w-full" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/editor/StylePanel.tsx
git commit -m "feat: StylePanel — font, size, color, outline, background, position controls"
```

---

### Task 6: Editor Toolbar + Keyboard Shortcuts

**Files:**
- Create: `frontend/src/components/editor/EditorToolbar.tsx`
- Create: `frontend/src/hooks/useEditorKeyboard.ts`

- [ ] **Step 1: Create frontend/src/components/editor/EditorToolbar.tsx**

```tsx
import { useEditorStore } from "../../store/editorStore";

interface EditorToolbarProps {
  onExport?: (format: string) => void;
}

export function EditorToolbar({ onExport }: EditorToolbarProps) {
  const { isDirty, saveSubtitles, segments } = useEditorStore();

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-800">
      <div className="flex items-center gap-2">
        <span className="text-sm text-zinc-400">{segments.length} segments</span>
        {isDirty && <span className="text-xs text-amber-400">Unsaved changes</span>}
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => saveSubtitles()}
          disabled={!isDirty}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm px-3 py-1 rounded"
        >
          Save
        </button>
        <button
          onClick={() => onExport?.("srt")}
          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm px-3 py-1 rounded"
        >
          Export SRT
        </button>
        <button
          onClick={() => onExport?.("ass")}
          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm px-3 py-1 rounded"
        >
          Export ASS
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/src/hooks/useEditorKeyboard.ts**

```typescript
import { useEffect } from "react";
import { useEditorStore } from "../store/editorStore";

export function useEditorKeyboard() {
  const { selectNext, selectPrev, saveSubtitles, setIsPlaying, isPlaying } = useEditorStore();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't capture when typing in inputs
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      switch (e.key) {
        case "ArrowDown":
        case "j":
          e.preventDefault();
          selectNext();
          break;
        case "ArrowUp":
        case "k":
          e.preventDefault();
          selectPrev();
          break;
        case " ":
          e.preventDefault();
          setIsPlaying(!isPlaying);
          break;
        case "s":
          if (e.metaKey || e.ctrlKey) {
            e.preventDefault();
            saveSubtitles();
          }
          break;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectNext, selectPrev, saveSubtitles, setIsPlaying, isPlaying]);
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/editor/EditorToolbar.tsx frontend/src/hooks/useEditorKeyboard.ts
git commit -m "feat: EditorToolbar (save/export) + keyboard shortcuts (j/k/space/Cmd+S)"
```

---

### Task 7: Editor Page (Three-Panel Layout) + Route

**Files:**
- Create: `frontend/src/pages/Editor.tsx`
- Modify: `frontend/src/App.tsx` (add editor route)

- [ ] **Step 1: Create frontend/src/pages/Editor.tsx**

```tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useEditorStore } from "../store/editorStore";
import { VideoPlayer } from "../components/editor/VideoPlayer";
import { SubtitleList } from "../components/editor/SubtitleList";
import { Waveform } from "../components/editor/Waveform";
import { StylePanel } from "../components/editor/StylePanel";
import { EditorToolbar } from "../components/editor/EditorToolbar";
import { useEditorKeyboard } from "../hooks/useEditorKeyboard";

type EditorTab = "subtitles" | "style";

export function Editor() {
  const { taskId: taskIdParam } = useParams<{ taskId: string }>();
  const taskId = taskIdParam ? parseInt(taskIdParam, 10) : null;
  const { loadSubtitles } = useEditorStore();
  const [activeTab, setActiveTab] = useState<EditorTab>("subtitles");

  useEditorKeyboard();

  useEffect(() => {
    if (taskId) loadSubtitles(taskId);
  }, [taskId, loadSubtitles]);

  if (!taskId) return <p className="text-zinc-500">Invalid task ID</p>;

  return (
    <div className="flex flex-col h-full -m-6">
      {/* Toolbar */}
      <EditorToolbar />

      {/* Main content: video (left) + subtitle panel (right) */}
      <div className="flex flex-1 min-h-0">
        {/* Left: Video player */}
        <div className="flex-1 min-w-0">
          <VideoPlayer taskId={taskId} />
        </div>

        {/* Right: Tabs + content */}
        <div className="w-96 border-l border-zinc-800 flex flex-col">
          {/* Tab bar */}
          <div className="flex border-b border-zinc-800 text-sm">
            <button
              onClick={() => setActiveTab("subtitles")}
              className={`px-4 py-2 ${
                activeTab === "subtitles"
                  ? "text-blue-400 border-b-2 border-blue-400"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              Subtitles
            </button>
            <button
              onClick={() => setActiveTab("style")}
              className={`px-4 py-2 ${
                activeTab === "style"
                  ? "text-blue-400 border-b-2 border-blue-400"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              Style
            </button>
          </div>

          {/* Tab content */}
          {activeTab === "subtitles" ? <SubtitleList /> : <StylePanel />}
        </div>
      </div>

      {/* Bottom: Waveform */}
      <Waveform taskId={taskId} />
    </div>
  );
}
```

- [ ] **Step 2: Update frontend/src/App.tsx — add editor route**

Add import at top:
```tsx
import { Editor } from "./pages/Editor";
```

Add route inside the protected layout routes, after the settings route:
```tsx
          <Route path="/editor/:taskId" element={<Editor />} />
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Editor.tsx frontend/src/App.tsx
git commit -m "feat: Editor page — three-panel layout with video, subtitles, waveform"
```

---

### Task 8: Final Build Verification + Push

- [ ] **Step 1: Full frontend build**

```bash
cd frontend && npm run build
```

Expected: No errors

- [ ] **Step 2: Verify backend tests still pass**

```bash
cd backend && python3 -m pytest tests/ -v
```

Expected: 73 tests PASS

- [ ] **Step 3: Push**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai"
git push origin main
```

---

## Task Summary

| Task | Description | Key Component |
|------|-------------|---------------|
| 1 | Editor Zustand store | `editorStore.ts` — segments, selection, playback |
| 2 | Video player + subtitle overlay | `VideoPlayer.tsx` — HTML5 video, seek sync, overlay |
| 3 | Subtitle list + inline editing | `SubtitleList.tsx` — bilingual, confidence flags, edit |
| 4 | Waveform timeline | `Waveform.tsx` — wavesurfer.js, draggable regions |
| 5 | Style panel | `StylePanel.tsx` — font, color, outline, bg, position |
| 6 | Toolbar + keyboard shortcuts | `EditorToolbar.tsx` + `useEditorKeyboard.ts` |
| 7 | Editor page + route | `Editor.tsx` — three-panel layout, route wiring |
| 8 | Final build + push | Verification |

**Phase 4B output:** A fully functional subtitle editor with:
- Video player synced to subtitle selection (click subtitle → seek video)
- Subtitle overlay on video preview
- Bilingual subtitle list with inline text editing
- Low-confidence segments highlighted with red + ⚠ marker
- Audio waveform timeline with draggable segment boundaries
- Subtitle style customization (font, size, color, outline, background, position)
- Keyboard shortcuts (j/k navigate, space play/pause, Cmd+S save)
- Save + export SRT/ASS toolbar
- **The complete Studio Captioner AI application is ready for use**
