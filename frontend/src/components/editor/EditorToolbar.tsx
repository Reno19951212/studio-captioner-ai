import { useState } from "react";
import { useEditorStore } from "../../store/editorStore";

interface EditorToolbarProps {
  onExport?: (format: string) => void;
  onSynthesize?: (format: string, quality: string) => Promise<void>;
}

export function EditorToolbar({ onExport, onSynthesize }: EditorToolbarProps) {
  const { isDirty, saveSubtitles, segments } = useEditorStore();
  const [synthesizing, setSynthesizing] = useState(false);
  const [synthFormat, setSynthFormat] = useState("mp4");

  const handleSynthesize = async () => {
    if (!onSynthesize) return;
    setSynthesizing(true);
    try {
      await onSynthesize(synthFormat, "medium");
    } finally {
      setSynthesizing(false);
    }
  };

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-800">
      <div className="flex items-center gap-2">
        <span className="text-sm text-zinc-400">{segments.length} segments</span>
        {isDirty && <span className="text-xs text-amber-400">● Unsaved</span>}
        <span className="text-xs text-zinc-600">j/k navigate · Space play · ⌘S save</span>
      </div>
      <div className="flex gap-2 items-center">
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
        <div className="h-4 w-px bg-zinc-700" />
        <select
          value={synthFormat}
          onChange={(e) => setSynthFormat(e.target.value)}
          className="bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs rounded px-2 py-1"
        >
          <option value="mp4">MP4</option>
          <option value="mxf">MXF (DNxHD)</option>
        </select>
        <button
          onClick={handleSynthesize}
          disabled={synthesizing || !onSynthesize}
          className="bg-emerald-700 hover:bg-emerald-600 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm px-3 py-1 rounded"
        >
          {synthesizing ? "Burning…" : "Burn to Video"}
        </button>
      </div>
    </div>
  );
}
