import type { Task, TaskCreate, QueueStatus, SubtitleSegment } from "../types/task";
import type { Glossary, GlossaryEntry } from "../types/glossary";
import type { Settings, AvailableModels } from "../types/settings";

const BASE_URL = "http://localhost:8000";

function getHeaders(): Record<string, string> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  });
  if (!resp.ok) {
    const error = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(error.detail || resp.statusText);
  }
  return resp.json();
}

export const auth = {
  register: (name: string, password: string) =>
    request<{ id: number; name: string }>("/api/auth/register", {
      method: "POST", body: JSON.stringify({ name, password }),
    }),
  login: (name: string, password: string) =>
    request<{ token: string; id: number; name: string }>("/api/auth/login", {
      method: "POST", body: JSON.stringify({ name, password }),
    }),
};

export const tasks = {
  create: (data: TaskCreate) =>
    request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(data) }),
  list: () => request<Task[]>("/api/tasks"),
  get: (id: number) => request<Task>(`/api/tasks/${id}`),
  delete: (id: number) => request<{ detail: string }>(`/api/tasks/${id}`, { method: "DELETE" }),
  queue: () => request<QueueStatus>("/api/queue"),
};

export const subtitles = {
  get: (taskId: number) =>
    request<{ segments: SubtitleSegment[] }>(`/api/tasks/${taskId}/subtitles`),
  save: (taskId: number, segments: SubtitleSegment[]) =>
    request<{ detail: string }>(`/api/tasks/${taskId}/subtitles`, {
      method: "PUT", body: JSON.stringify({ segments }),
    }),
};

export const glossaries = {
  list: () => request<Glossary[]>("/api/glossaries"),
  create: (name: string, description = "") =>
    request<Glossary>("/api/glossaries", {
      method: "POST", body: JSON.stringify({ name, description }),
    }),
  delete: (id: number) =>
    request<{ detail: string }>(`/api/glossaries/${id}`, { method: "DELETE" }),
  getEntries: (id: number) => request<GlossaryEntry[]>(`/api/glossaries/${id}/entries`),
  addEntries: (id: number, entries: { source_term: string; target_term: string }[]) =>
    request<GlossaryEntry[]>(`/api/glossaries/${id}/entries`, {
      method: "POST", body: JSON.stringify({ entries }),
    }),
  exportUrl: (id: number) => `${BASE_URL}/api/glossaries/${id}/export`,
};

export const settings = {
  get: () => request<Settings>("/api/settings"),
  update: (data: Partial<Settings>) =>
    request<Settings>("/api/settings", { method: "PUT", body: JSON.stringify(data) }),
  models: () => request<AvailableModels>("/api/settings/models"),
};

export const preview = {
  videoUrl: (taskId: number) => `${BASE_URL}/api/preview/${taskId}/video`,
  waveformUrl: (taskId: number) => `${BASE_URL}/api/preview/${taskId}/waveform`,
  thumbnailUrl: (taskId: number) => `${BASE_URL}/api/preview/${taskId}/thumbnail`,
};
