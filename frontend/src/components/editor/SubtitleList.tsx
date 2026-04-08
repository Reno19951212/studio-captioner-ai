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
  const { segments, selectedIndex, confidenceScores, selectSegment, updateSegment } = useEditorStore();
  const listRef = useRef<HTMLDivElement>(null);

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
          <div key={i} onClick={() => selectSegment(i)}
            className={`rounded-lg p-2 cursor-pointer transition text-sm ${
              isSelected ? "bg-blue-500/10 border border-blue-500/30"
              : isLowConfidence ? "bg-red-500/5 border border-red-500/20"
              : "bg-zinc-900 border border-transparent hover:bg-zinc-800"
            }`}>
            <div className="flex justify-between items-center mb-1 text-xs">
              <span className="text-zinc-600">#{i + 1}</span>
              <div className="flex items-center gap-2">
                {isLowConfidence && <span className="text-red-400 font-medium">⚠ {Math.round(confidence * 100)}%</span>}
                <span className="text-zinc-600">{formatTimecode(seg.start_time)} → {formatTimecode(seg.end_time)}</span>
              </div>
            </div>
            {isSelected ? (
              <textarea value={seg.text} onChange={(e) => updateSegment(i, { text: e.target.value })}
                className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-200 text-sm resize-none mb-1"
                rows={2} onClick={(e) => e.stopPropagation()} />
            ) : (
              <div className="text-zinc-200 mb-1">{seg.text}</div>
            )}
            {isSelected ? (
              <textarea value={seg.translated_text || ""} onChange={(e) => updateSegment(i, { translated_text: e.target.value })}
                className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-blue-400 text-sm resize-none"
                rows={2} placeholder="Translation..." onClick={(e) => e.stopPropagation()} />
            ) : (
              seg.translated_text && <div className={isLowConfidence ? "text-red-400" : "text-blue-400"}>{seg.translated_text}</div>
            )}
          </div>
        );
      })}
      {segments.length === 0 && <p className="text-zinc-600 text-sm text-center py-8">No subtitles loaded</p>}
    </div>
  );
}
