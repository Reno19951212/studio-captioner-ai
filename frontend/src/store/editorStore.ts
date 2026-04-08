import { create } from "zustand";
import { subtitles as subtitlesApi } from "../services/api";
import type { SubtitleSegment } from "../types/task";

interface EditorState {
  taskId: number | null;
  segments: SubtitleSegment[];
  selectedIndex: number | null;
  currentTime: number;
  isPlaying: boolean;
  isDirty: boolean;
  confidenceScores: number[];
  loadSubtitles: (taskId: number) => Promise<void>;
  saveSubtitles: () => Promise<void>;
  updateSegment: (index: number, updates: Partial<SubtitleSegment>) => void;
  selectSegment: (index: number | null) => void;
  setCurrentTime: (ms: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setConfidenceScores: (scores: number[]) => void;
  getActiveSegmentIndex: () => number;
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
    return segments.findIndex((s) => currentTime >= s.start_time && currentTime <= s.end_time);
  },

  selectNext: () => {
    const { selectedIndex, segments } = get();
    if (selectedIndex === null) { if (segments.length > 0) set({ selectedIndex: 0 }); }
    else if (selectedIndex < segments.length - 1) set({ selectedIndex: selectedIndex + 1 });
  },

  selectPrev: () => {
    const { selectedIndex } = get();
    if (selectedIndex !== null && selectedIndex > 0) set({ selectedIndex: selectedIndex - 1 });
  },
}));
