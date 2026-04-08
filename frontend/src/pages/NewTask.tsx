import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTaskStore } from "../store/taskStore";
import { useSettingsStore } from "../store/settingsStore";
import { glossaries as glossaryApi } from "../services/api";
import type { Glossary } from "../types/glossary";

const WHISPER_MODEL_LABELS: Record<string, string> = {
  tiny: "Tiny (75MB) — Fast, low quality",
  base: "Base (141MB) — Fast, basic quality",
  small: "Small (466MB) — Moderate speed & quality",
  medium: "Medium (1.5GB) — Good quality, slower",
  "large-v1": "Large v1 (2.9GB) — High quality",
  "large-v2": "Large v2 (2.9GB) — Best quality",
  "large-v3": "Large v3 (2.9GB) — Latest, best quality",
};

export function NewTask() {
  const [videoPath, setVideoPath] = useState("");
  const [asrModel] = useState("whisper_cpp");
  const [whisperModel, setWhisperModel] = useState("base");
  const [glossaryList, setGlossaryList] = useState<Glossary[]>([]);
  const [selectedGlossary, setSelectedGlossary] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const { createTask } = useTaskStore();
  const { models, fetchModels } = useSettingsStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchModels();
    glossaryApi.list().then(setGlossaryList).catch(() => {});
  }, [fetchModels]);

  // Auto-select best available model
  useEffect(() => {
    if (models?.whisper_sizes?.length) {
      const preferred = ["large-v2", "large-v3", "medium", "small", "base", "tiny"];
      const best = preferred.find((m) => models.whisper_sizes.includes(m));
      if (best) setWhisperModel(best);
    }
  }, [models]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoPath.trim()) {
      setError("Please enter a video path");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await createTask(videoPath.trim(), asrModel, whisperModel);
      navigate("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create task");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">New Task</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="text-red-400 text-sm">{error}</div>}

        <div>
          <label className="block text-sm text-zinc-400 mb-1">
            Video Path (on shared storage)
          </label>
          <input
            type="text"
            value={videoPath}
            onChange={(e) => setVideoPath(e.target.value)}
            placeholder="/shared/input/interview.mxf"
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          />
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1">Whisper Model</label>
          <select
            value={whisperModel}
            onChange={(e) => setWhisperModel(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          >
            {(models?.whisper_sizes || ["base"]).map((m) => (
              <option key={m} value={m}>
                {WHISPER_MODEL_LABELS[m] || m}
              </option>
            ))}
          </select>
          <p className="text-xs text-zinc-600 mt-1">
            Larger models are more accurate but slower. Large v2 recommended for production.
          </p>
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1">Glossary (optional)</label>
          <select
            value={selectedGlossary ?? ""}
            onChange={(e) =>
              setSelectedGlossary(e.target.value ? Number(e.target.value) : null)
            }
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          >
            <option value="">None</option>
            {glossaryList.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 text-white rounded py-2 text-sm font-medium"
        >
          {submitting ? "Submitting..." : "Submit to Queue"}
        </button>
      </form>
    </div>
  );
}
