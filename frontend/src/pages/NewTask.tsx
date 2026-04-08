import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTaskStore } from "../store/taskStore";
import { useSettingsStore } from "../store/settingsStore";
import { glossaries as glossaryApi } from "../services/api";
import type { Glossary } from "../types/glossary";

export function NewTask() {
  const [videoPath, setVideoPath] = useState("");
  const [asrModel, setAsrModel] = useState("faster_whisper");
  const [_glossaryList, setGlossaryList] = useState<Glossary[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const { createTask } = useTaskStore();
  const { models, fetchModels } = useSettingsStore();
  const navigate = useNavigate();

  useEffect(() => { fetchModels(); glossaryApi.list().then(setGlossaryList).catch(() => {}); }, [fetchModels]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoPath.trim()) { setError("Please enter a video path"); return; }
    setError(""); setSubmitting(true);
    try { await createTask(videoPath.trim(), asrModel); navigate("/"); }
    catch (err: unknown) { setError(err instanceof Error ? err.message : "Failed to create task"); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">New Task</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Video Path (on shared storage)</label>
          <input type="text" value={videoPath} onChange={(e) => setVideoPath(e.target.value)} placeholder="/shared/input/interview.mxf"
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">ASR Engine</label>
          <select value={asrModel} onChange={(e) => setAsrModel(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100">
            {(models?.asr_models || ["faster_whisper", "whisper_cpp"]).map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
        <button type="submit" disabled={submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 text-white rounded py-2 text-sm font-medium">
          {submitting ? "Submitting..." : "Submit to Queue"}
        </button>
      </form>
    </div>
  );
}
