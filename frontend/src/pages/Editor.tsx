import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useEditorStore } from "../store/editorStore";
import { VideoPlayer } from "../components/editor/VideoPlayer";
import { SubtitleList } from "../components/editor/SubtitleList";
import { Waveform } from "../components/editor/Waveform";
import { StylePanel } from "../components/editor/StylePanel";
import { EditorToolbar } from "../components/editor/EditorToolbar";
import { useEditorKeyboard } from "../hooks/useEditorKeyboard";
import { subtitles as subtitlesApi } from "../services/api";

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

  const handleExport = async (format: string) => {
    if (!taskId) return;
    try {
      const blob = await subtitlesApi.exportPost(taskId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `subtitles.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
    }
  };

  const handleSynthesize = async (format: string, quality: string) => {
    if (!taskId) return;
    const token = localStorage.getItem("token");
    const resp = await fetch(`http://localhost:8000/api/tasks/${taskId}/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ output_format: format, quality }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || "Synthesis failed");
    }
  };

  if (!taskId) return <p className="text-zinc-500">Invalid task ID</p>;

  return (
    <div className="flex flex-col h-full -m-6">
      <EditorToolbar onExport={handleExport} onSynthesize={handleSynthesize} />
      <div className="flex flex-1 min-h-0">
        <div className="flex-1 min-w-0">
          <VideoPlayer taskId={taskId} />
        </div>
        <div className="w-96 border-l border-zinc-800 flex flex-col">
          <div className="flex border-b border-zinc-800 text-sm">
            <button onClick={() => setActiveTab("subtitles")}
              className={`px-4 py-2 ${activeTab === "subtitles" ? "text-blue-400 border-b-2 border-blue-400" : "text-zinc-500 hover:text-zinc-300"}`}>
              Subtitles
            </button>
            <button onClick={() => setActiveTab("style")}
              className={`px-4 py-2 ${activeTab === "style" ? "text-blue-400 border-b-2 border-blue-400" : "text-zinc-500 hover:text-zinc-300"}`}>
              Style
            </button>
          </div>
          {activeTab === "subtitles" ? <SubtitleList /> : <StylePanel />}
        </div>
      </div>
      <Waveform taskId={taskId} />
    </div>
  );
}
