import { useEditorStore } from "../../store/editorStore";

interface EditorToolbarProps { onExport?: (format: string) => void; }

export function EditorToolbar({ onExport }: EditorToolbarProps) {
  const { isDirty, saveSubtitles, segments } = useEditorStore();

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-800">
      <div className="flex items-center gap-2">
        <span className="text-sm text-zinc-400">{segments.length} segments</span>
        {isDirty && <span className="text-xs text-amber-400">Unsaved changes</span>}
      </div>
      <div className="flex gap-2">
        <button onClick={() => saveSubtitles()} disabled={!isDirty}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm px-3 py-1 rounded">Save</button>
        <button onClick={() => onExport?.("srt")}
          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm px-3 py-1 rounded">Export SRT</button>
        <button onClick={() => onExport?.("ass")}
          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-sm px-3 py-1 rounded">Export ASS</button>
      </div>
    </div>
  );
}
