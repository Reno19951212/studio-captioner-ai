import { useState, useEffect } from "react";
import { useSettingsStore } from "../store/settingsStore";
import type { Settings } from "../types/settings";

export function SettingsPage() {
  const { settings, fetchSettings, updateSettings, serverUrl, setServerUrl } = useSettingsStore();
  const [local, setLocal] = useState<Settings | null>(null);
  const [localUrl, setLocalUrl] = useState(serverUrl);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  // Sync local state when settings load
  useEffect(() => {
    if (settings && !local) setLocal({ ...settings });
  }, [settings, local]);

  const handleSave = async () => {
    if (!local) return;
    setError("");
    try {
      await updateSettings(local);
      setServerUrl(localUrl);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    }
  };

  if (!local) return <p className="text-zinc-500">Loading settings...</p>;

  const field = (label: string, key: keyof Settings, placeholder = "") => (
    <div>
      <label className="block text-sm text-zinc-400 mb-1">{label}</label>
      <input
        value={local[key]}
        onChange={(e) => setLocal({ ...local, [key]: e.target.value })}
        placeholder={placeholder}
        className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
      />
    </div>
  );

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <div className="space-y-4">
        {error && <div className="text-red-400 text-sm">{error}</div>}

        <div>
          <label className="block text-sm text-zinc-400 mb-1">Server URL</label>
          <input
            value={localUrl}
            onChange={(e) => setLocalUrl(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
          />
          <p className="text-xs text-zinc-600 mt-1">URL to connect this app to the backend</p>
        </div>

        {field("Shared Storage Base Path", "storage_base_path", "/data/media")}
        {field("Default ASR Model", "default_asr_model")}

        <div>
          <label className="block text-sm text-zinc-400 mb-1">LLM API Base</label>
          <input
            value={local.llm_api_base}
            onChange={(e) => setLocal({ ...local, llm_api_base: e.target.value })}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
          />
          <p className="text-xs text-zinc-600 mt-1">Ollama: http://localhost:11434/v1</p>
        </div>

        {field("LLM Model", "llm_model")}

        <button
          onClick={handleSave}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 text-sm font-medium"
        >
          {saved ? "✓ Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
