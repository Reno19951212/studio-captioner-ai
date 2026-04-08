import { create } from "zustand";
import { settings as settingsApi } from "../services/api";
import type { Settings, AvailableModels } from "../types/settings";

interface SettingsState {
  settings: Settings | null;
  models: AvailableModels | null;
  serverUrl: string;
  fetchSettings: () => Promise<void>;
  updateSettings: (data: Partial<Settings>) => Promise<void>;
  fetchModels: () => Promise<void>;
  setServerUrl: (url: string) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: null, models: null,
  serverUrl: localStorage.getItem("serverUrl") || "http://localhost:8000",
  fetchSettings: async () => { const r = await settingsApi.get(); set({ settings: r }); },
  updateSettings: async (data) => { const r = await settingsApi.update(data); set({ settings: r }); },
  fetchModels: async () => { const r = await settingsApi.models(); set({ models: r }); },
  setServerUrl: (url) => { localStorage.setItem("serverUrl", url); set({ serverUrl: url }); },
}));
