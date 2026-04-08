import { useState, useEffect } from "react";
import { useSettingsStore } from "../store/settingsStore";

export function SettingsPage() {
  const { settings, fetchSettings, updateSettings, serverUrl, setServerUrl } = useSettingsStore();
  const [localUrl, setLocalUrl] = useState(serverUrl);
  const [saved, setSaved] = useState(false);

  useEffect(() => { fetchSettings(); }, [fetchSettings]);

  const handleSave = async () => {
    if (settings) await updateSettings(settings);
    setServerUrl(localUrl);
    setSaved(true); setTimeout(() => setSaved(false), 2000);
  };

  if (!settings) return <p className="text-zinc-500">Loading settings...</p>;

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Server URL</label>
          <input value={localUrl} onChange={(e) => setLocalUrl(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Shared Storage Path</label>
          <input value={settings.storage_base_path} onChange={(e) => updateSettings({ storage_base_path: e.target.value })} placeholder="/data/media"
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Default ASR Model</label>
          <input value={settings.default_asr_model} onChange={(e) => updateSettings({ default_asr_model: e.target.value })}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">LLM API Base</label>
          <input value={settings.llm_api_base} onChange={(e) => updateSettings({ llm_api_base: e.target.value })}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">LLM Model</label>
          <input value={settings.llm_model} onChange={(e) => updateSettings({ llm_model: e.target.value })}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        </div>
        <button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 text-sm">
          {saved ? "Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
