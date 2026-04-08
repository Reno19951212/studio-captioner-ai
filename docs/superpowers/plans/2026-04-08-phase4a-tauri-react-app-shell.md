# Phase 4A: Tauri + React App Shell — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Tauri v2 + React desktop application with all pages except the Subtitle Editor (Phase 4B) — Dashboard, New Task, Glossary management, History, and Settings — connected to the FastAPI backend via REST and WebSocket.

**Architecture:** Tauri v2 wraps a Vite + React 18 + TypeScript app. Zustand stores manage state. An API client layer (`services/api.ts`) wraps all REST calls with JWT auth. A WebSocket hook (`hooks/useWebSocket.ts`) provides real-time updates. shadcn/ui components provide consistent UI. Each page is a separate route with its own state slice.

**Tech Stack:** Tauri v2, React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand, React Router

**Working directory:** `/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/frontend`

**Prerequisites:** Node.js (v24+), npm, Rust/cargo (for Tauri)

---

## File Structure

```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── index.html
├── src-tauri/
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── src/
│       └── main.rs
├── src/
│   ├── main.tsx                 # React entry point
│   ├── App.tsx                  # Router + Layout
│   ├── types/
│   │   ├── task.ts              # Task, QueueStatus types
│   │   ├── glossary.ts          # Glossary, GlossaryEntry types
│   │   └── settings.ts          # Settings types
│   ├── services/
│   │   ├── api.ts               # REST client with JWT
│   │   └── ws.ts                # WebSocket client
│   ├── hooks/
│   │   ├── useWebSocket.ts      # WS connection hook
│   │   └── useAuth.ts           # Auth state hook
│   ├── store/
│   │   ├── authStore.ts         # Auth state (token, user)
│   │   ├── taskStore.ts         # Tasks + queue state
│   │   └── settingsStore.ts     # Settings state
│   ├── components/
│   │   ├── common/
│   │   │   ├── Layout.tsx       # Sidebar + main content layout
│   │   │   ├── Sidebar.tsx      # Navigation sidebar
│   │   │   └── ProtectedRoute.tsx
│   │   └── queue/
│   │       ├── QueueList.tsx     # Queue item list
│   │       └── ProgressBar.tsx   # Task progress bar
│   └── pages/
│       ├── Login.tsx
│       ├── Dashboard.tsx
│       ├── NewTask.tsx
│       ├── Glossary.tsx
│       ├── History.tsx
│       └── Settings.tsx
```

---

### Task 1: Scaffold Tauri v2 + React + Vite Project

**Files:**
- Create: entire `frontend/` scaffold via CLI tools

- [ ] **Step 1: Create Vite + React + TypeScript project**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai"
rm -rf frontend
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Initialize Tauri v2**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai/frontend"
npm install --save-dev @tauri-apps/cli@latest
npx tauri init
```

When prompted:
- App name: `Studio Captioner AI`
- Window title: `Studio Captioner AI`
- Web assets path: `../dist`
- Dev server URL: `http://localhost:5173`
- Frontend dev command: `npm run dev`
- Frontend build command: `npm run build`

- [ ] **Step 3: Install Tauri API package**

```bash
npm install @tauri-apps/api@latest
```

- [ ] **Step 4: Install UI dependencies**

```bash
npm install react-router-dom zustand tailwindcss @tailwindcss/vite
npm install --save-dev @types/react-router-dom
```

- [ ] **Step 5: Configure Tailwind**

Replace `frontend/src/index.css` with:

```css
@import "tailwindcss";
```

Update `frontend/vite.config.ts`:

```typescript
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
  },
  clearScreen: false,
});
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd frontend && npm run dev &
sleep 3
curl -s http://localhost:5173 | head -5
kill %1
```

Expected: HTML response from Vite dev server

- [ ] **Step 7: Commit**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai"
git add frontend/
git commit -m "chore: scaffold Tauri v2 + React + Vite + Tailwind project"
```

---

### Task 2: TypeScript Types + API Client

**Files:**
- Create: `frontend/src/types/task.ts`
- Create: `frontend/src/types/glossary.ts`
- Create: `frontend/src/types/settings.ts`
- Create: `frontend/src/services/api.ts`

- [ ] **Step 1: Create frontend/src/types/task.ts**

```typescript
export interface Task {
  id: number;
  user_id: number;
  status: "queued" | "processing" | "ready_for_review" | "completed" | "failed";
  video_path: string;
  output_path: string | null;
  subtitle_path: string | null;
  progress: number;
  stage: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface TaskCreate {
  video_path: string;
  asr_model?: string;
  config?: Record<string, unknown>;
}

export interface QueueStatus {
  queue_length: number;
  current_task: Task | null;
}

export interface SubtitleSegment {
  text: string;
  start_time: number;
  end_time: number;
  translated_text: string | null;
}
```

- [ ] **Step 2: Create frontend/src/types/glossary.ts**

```typescript
export interface Glossary {
  id: number;
  name: string;
  description: string;
  created_by: number;
  created_at: string;
}

export interface GlossaryEntry {
  id: number;
  glossary_id: number;
  source_term: string;
  target_term: string;
}
```

- [ ] **Step 3: Create frontend/src/types/settings.ts**

```typescript
export interface Settings {
  storage_base_path: string;
  default_asr_model: string;
  default_whisper_model: string;
  llm_api_base: string;
  llm_model: string;
}

export interface AvailableModels {
  asr_models: string[];
  whisper_sizes: string[];
}
```

- [ ] **Step 4: Create frontend/src/services/api.ts**

```typescript
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

// Auth
export const auth = {
  register: (name: string, password: string) =>
    request<{ id: number; name: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, password }),
    }),
  login: (name: string, password: string) =>
    request<{ token: string; id: number; name: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ name, password }),
    }),
};

// Tasks
export const tasks = {
  create: (data: TaskCreate) =>
    request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(data) }),
  list: () => request<Task[]>("/api/tasks"),
  get: (id: number) => request<Task>(`/api/tasks/${id}`),
  delete: (id: number) => request<{ detail: string }>(`/api/tasks/${id}`, { method: "DELETE" }),
  queue: () => request<QueueStatus>("/api/queue"),
};

// Subtitles
export const subtitles = {
  get: (taskId: number) =>
    request<{ segments: SubtitleSegment[] }>(`/api/tasks/${taskId}/subtitles`),
  save: (taskId: number, segments: SubtitleSegment[]) =>
    request<{ detail: string }>(`/api/tasks/${taskId}/subtitles`, {
      method: "PUT",
      body: JSON.stringify({ segments }),
    }),
  exportUrl: (taskId: number, format: string) =>
    `${BASE_URL}/api/tasks/${taskId}/export?format=${format}`,
};

// Glossary
export const glossaries = {
  list: () => request<Glossary[]>("/api/glossaries"),
  create: (name: string, description = "") =>
    request<Glossary>("/api/glossaries", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  delete: (id: number) =>
    request<{ detail: string }>(`/api/glossaries/${id}`, { method: "DELETE" }),
  getEntries: (id: number) => request<GlossaryEntry[]>(`/api/glossaries/${id}/entries`),
  addEntries: (id: number, entries: { source_term: string; target_term: string }[]) =>
    request<GlossaryEntry[]>(`/api/glossaries/${id}/entries`, {
      method: "POST",
      body: JSON.stringify({ entries }),
    }),
  exportUrl: (id: number) => `${BASE_URL}/api/glossaries/${id}/export`,
};

// Settings
export const settings = {
  get: () => request<Settings>("/api/settings"),
  update: (data: Partial<Settings>) =>
    request<Settings>("/api/settings", { method: "PUT", body: JSON.stringify(data) }),
  models: () => request<AvailableModels>("/api/settings/models"),
};

// Preview
export const preview = {
  videoUrl: (taskId: number) => `${BASE_URL}/api/preview/${taskId}/video`,
  waveformUrl: (taskId: number) => `${BASE_URL}/api/preview/${taskId}/waveform`,
  thumbnailUrl: (taskId: number) => `${BASE_URL}/api/preview/${taskId}/thumbnail`,
};
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/ frontend/src/services/
git commit -m "feat: TypeScript types + REST API client with JWT auth"
```

---

### Task 3: Zustand Stores + Auth Hook

**Files:**
- Create: `frontend/src/store/authStore.ts`
- Create: `frontend/src/store/taskStore.ts`
- Create: `frontend/src/store/settingsStore.ts`
- Create: `frontend/src/hooks/useAuth.ts`
- Create: `frontend/src/services/ws.ts`
- Create: `frontend/src/hooks/useWebSocket.ts`

- [ ] **Step 1: Create frontend/src/store/authStore.ts**

```typescript
import { create } from "zustand";
import { auth } from "../services/api";

interface AuthState {
  token: string | null;
  userId: number | null;
  userName: string | null;
  isAuthenticated: boolean;
  login: (name: string, password: string) => Promise<void>;
  register: (name: string, password: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  userId: null,
  userName: null,
  isAuthenticated: false,

  login: async (name, password) => {
    const resp = await auth.login(name, password);
    localStorage.setItem("token", resp.token);
    localStorage.setItem("userId", String(resp.id));
    localStorage.setItem("userName", resp.name);
    set({ token: resp.token, userId: resp.id, userName: resp.name, isAuthenticated: true });
  },

  register: async (name, password) => {
    await auth.register(name, password);
  },

  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    localStorage.removeItem("userName");
    set({ token: null, userId: null, userName: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("userId");
    const userName = localStorage.getItem("userName");
    if (token && userId) {
      set({
        token,
        userId: Number(userId),
        userName,
        isAuthenticated: true,
      });
    }
  },
}));
```

- [ ] **Step 2: Create frontend/src/store/taskStore.ts**

```typescript
import { create } from "zustand";
import { tasks } from "../services/api";
import type { Task, QueueStatus } from "../types/task";

interface TaskState {
  tasks: Task[];
  queueStatus: QueueStatus | null;
  loading: boolean;
  fetchTasks: () => Promise<void>;
  fetchQueue: () => Promise<void>;
  createTask: (videoPath: string, asrModel?: string) => Promise<Task>;
  deleteTask: (id: number) => Promise<void>;
  updateTaskFromWs: (taskId: number, data: Partial<Task>) => void;
  updateQueueFromWs: (data: QueueStatus) => void;
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  queueStatus: null,
  loading: false,

  fetchTasks: async () => {
    set({ loading: true });
    const result = await tasks.list();
    set({ tasks: result, loading: false });
  },

  fetchQueue: async () => {
    const result = await tasks.queue();
    set({ queueStatus: result });
  },

  createTask: async (videoPath, asrModel = "faster_whisper") => {
    const task = await tasks.create({ video_path: videoPath, asr_model: asrModel });
    set({ tasks: [task, ...get().tasks] });
    return task;
  },

  deleteTask: async (id) => {
    await tasks.delete(id);
    set({ tasks: get().tasks.filter((t) => t.id !== id) });
  },

  updateTaskFromWs: (taskId, data) => {
    set({
      tasks: get().tasks.map((t) => (t.id === taskId ? { ...t, ...data } : t)),
    });
  },

  updateQueueFromWs: (data) => {
    set({ queueStatus: data });
  },
}));
```

- [ ] **Step 3: Create frontend/src/store/settingsStore.ts**

```typescript
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

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: null,
  models: null,
  serverUrl: localStorage.getItem("serverUrl") || "http://localhost:8000",

  fetchSettings: async () => {
    const result = await settingsApi.get();
    set({ settings: result });
  },

  updateSettings: async (data) => {
    const result = await settingsApi.update(data);
    set({ settings: result });
  },

  fetchModels: async () => {
    const result = await settingsApi.models();
    set({ models: result });
  },

  setServerUrl: (url) => {
    localStorage.setItem("serverUrl", url);
    set({ serverUrl: url });
  },
}));
```

- [ ] **Step 4: Create frontend/src/hooks/useAuth.ts**

```typescript
import { useEffect } from "react";
import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const store = useAuthStore();

  useEffect(() => {
    store.loadFromStorage();
  }, []);

  return store;
}
```

- [ ] **Step 5: Create frontend/src/services/ws.ts**

```typescript
const WS_BASE = "ws://localhost:8000";

export function connectTaskWs(
  taskId: number,
  onMessage: (data: Record<string, unknown>) => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/tasks/${taskId}`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  return ws;
}

export function connectQueueWs(
  onMessage: (data: Record<string, unknown>) => void
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/queue`);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  return ws;
}
```

- [ ] **Step 6: Create frontend/src/hooks/useWebSocket.ts**

```typescript
import { useEffect, useRef } from "react";
import { connectQueueWs } from "../services/ws";
import { useTaskStore } from "../store/taskStore";
import type { QueueStatus } from "../types/task";

export function useQueueWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const updateQueueFromWs = useTaskStore((s) => s.updateQueueFromWs);

  useEffect(() => {
    const ws = connectQueueWs((data) => {
      updateQueueFromWs(data as unknown as QueueStatus);
    });
    wsRef.current = ws;
    return () => ws.close();
  }, [updateQueueFromWs]);

  return wsRef;
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/store/ frontend/src/hooks/ frontend/src/services/ws.ts
git commit -m "feat: Zustand stores (auth, task, settings) + WebSocket hooks"
```

---

### Task 4: App Layout + Sidebar + Router + Login Page

**Files:**
- Create: `frontend/src/components/common/Layout.tsx`
- Create: `frontend/src/components/common/Sidebar.tsx`
- Create: `frontend/src/components/common/ProtectedRoute.tsx`
- Create: `frontend/src/pages/Login.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Create frontend/src/components/common/Sidebar.tsx**

```tsx
import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const navItems = [
  { to: "/", label: "Dashboard", icon: "📊" },
  { to: "/new-task", label: "New Task", icon: "➕" },
  { to: "/glossary", label: "Glossary", icon: "📖" },
  { to: "/history", label: "History", icon: "📋" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const { userName, logout } = useAuthStore();

  return (
    <aside className="w-56 bg-zinc-900 border-r border-zinc-800 flex flex-col h-screen">
      <div className="p-4 text-blue-400 font-bold text-sm">Studio Captioner AI</div>
      <nav className="flex-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-2.5 text-sm ${
                isActive
                  ? "bg-blue-500/10 text-blue-400 border-l-2 border-blue-400"
                  : "text-zinc-400 hover:text-zinc-200 border-l-2 border-transparent"
              }`
            }
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-zinc-800 p-3">
        <div className="text-xs text-zinc-500">{userName}</div>
        <button onClick={logout} className="text-xs text-zinc-600 hover:text-zinc-400 mt-1">
          Logout
        </button>
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Create frontend/src/components/common/Layout.tsx**

```tsx
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";

export function Layout() {
  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 3: Create frontend/src/components/common/ProtectedRoute.tsx**

```tsx
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
```

- [ ] **Step 4: Create frontend/src/pages/Login.tsx**

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export function Login() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const { login, register } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      if (isRegister) {
        await register(name, password);
      }
      await login(name, password);
      navigate("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-zinc-950">
      <form onSubmit={handleSubmit} className="bg-zinc-900 p-8 rounded-lg w-80 space-y-4">
        <h1 className="text-xl font-bold text-zinc-100 text-center">Studio Captioner AI</h1>
        {error && <div className="text-red-400 text-sm text-center">{error}</div>}
        <input
          type="text"
          placeholder="Username"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
        />
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded py-2 text-sm font-medium"
        >
          {isRegister ? "Register & Login" : "Login"}
        </button>
        <button
          type="button"
          onClick={() => setIsRegister(!isRegister)}
          className="w-full text-zinc-500 text-xs hover:text-zinc-300"
        >
          {isRegister ? "Already have an account? Login" : "New user? Register"}
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 5: Replace frontend/src/App.tsx**

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { Layout } from "./components/common/Layout";
import { ProtectedRoute } from "./components/common/ProtectedRoute";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { NewTask } from "./pages/NewTask";
import { GlossaryPage } from "./pages/Glossary";
import { History } from "./pages/History";
import { SettingsPage } from "./pages/Settings";
import { useAuthStore } from "./store/authStore";

export default function App() {
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-task" element={<NewTask />} />
          <Route path="/glossary" element={<GlossaryPage />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 6: Replace frontend/src/main.tsx**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 7: Create stub pages (Dashboard, NewTask, Glossary, History, Settings)**

Create `frontend/src/pages/Dashboard.tsx`:
```tsx
export function Dashboard() {
  return <div><h1 className="text-2xl font-bold mb-4">Dashboard</h1><p className="text-zinc-500">Coming next...</p></div>;
}
```

Create `frontend/src/pages/NewTask.tsx`:
```tsx
export function NewTask() {
  return <div><h1 className="text-2xl font-bold mb-4">New Task</h1><p className="text-zinc-500">Coming next...</p></div>;
}
```

Create `frontend/src/pages/Glossary.tsx`:
```tsx
export function GlossaryPage() {
  return <div><h1 className="text-2xl font-bold mb-4">Glossary</h1><p className="text-zinc-500">Coming next...</p></div>;
}
```

Create `frontend/src/pages/History.tsx`:
```tsx
export function History() {
  return <div><h1 className="text-2xl font-bold mb-4">History</h1><p className="text-zinc-500">Coming next...</p></div>;
}
```

Create `frontend/src/pages/Settings.tsx`:
```tsx
export function SettingsPage() {
  return <div><h1 className="text-2xl font-bold mb-4">Settings</h1><p className="text-zinc-500">Coming next...</p></div>;
}
```

- [ ] **Step 8: Verify build succeeds**

```bash
cd frontend && npm run build
```

Expected: Build succeeds without errors

- [ ] **Step 9: Commit**

```bash
git add frontend/src/
git commit -m "feat: app layout, sidebar, router, login page, stub pages"
```

---

### Task 5: Dashboard Page (Queue Status + Real-time Progress)

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/components/queue/QueueList.tsx`
- Create: `frontend/src/components/queue/ProgressBar.tsx`

- [ ] **Step 1: Create frontend/src/components/queue/ProgressBar.tsx**

```tsx
interface ProgressBarProps {
  progress: number;
  stage: string | null;
}

export function ProgressBar({ progress, stage }: ProgressBarProps) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-zinc-400">{stage || "Waiting"}</span>
        <span className="text-emerald-400">{progress}%</span>
      </div>
      <div className="bg-zinc-800 rounded-full h-1.5">
        <div
          className="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create frontend/src/components/queue/QueueList.tsx**

```tsx
import type { Task } from "../../types/task";
import { ProgressBar } from "./ProgressBar";

interface QueueListProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
}

export function QueueList({ tasks, onTaskClick }: QueueListProps) {
  const statusColor: Record<string, string> = {
    queued: "text-amber-400",
    processing: "text-emerald-400",
    ready_for_review: "text-pink-400",
    completed: "text-blue-400",
    failed: "text-red-400",
  };

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <div
          key={task.id}
          onClick={() => onTaskClick?.(task)}
          className="bg-zinc-900 rounded-lg p-3 cursor-pointer hover:bg-zinc-800/80 transition"
        >
          <div className="flex justify-between items-center mb-1">
            <span className="text-sm text-zinc-200 truncate max-w-xs">
              {task.video_path.split("/").pop()}
            </span>
            <span className={`text-xs ${statusColor[task.status] || "text-zinc-500"}`}>
              {task.status.replace("_", " ")}
            </span>
          </div>
          {task.status === "processing" && (
            <ProgressBar progress={task.progress} stage={task.stage} />
          )}
        </div>
      ))}
      {tasks.length === 0 && <p className="text-zinc-600 text-sm">No tasks</p>}
    </div>
  );
}
```

- [ ] **Step 3: Replace frontend/src/pages/Dashboard.tsx**

```tsx
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTaskStore } from "../store/taskStore";
import { useQueueWebSocket } from "../hooks/useWebSocket";
import { QueueList } from "../components/queue/QueueList";
import type { Task } from "../types/task";

export function Dashboard() {
  const { tasks, queueStatus, fetchTasks, fetchQueue } = useTaskStore();
  const navigate = useNavigate();
  useQueueWebSocket();

  useEffect(() => {
    fetchTasks();
    fetchQueue();
  }, [fetchTasks, fetchQueue]);

  const queued = tasks.filter((t) => t.status === "queued");
  const processing = tasks.filter((t) => t.status === "processing");
  const review = tasks.filter((t) => t.status === "ready_for_review");
  const completed = tasks.filter((t) => t.status === "completed");

  const handleTaskClick = (task: Task) => {
    if (task.status === "ready_for_review" || task.status === "completed") {
      navigate(`/editor/${task.id}`);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Status cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-emerald-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-emerald-400">{processing.length}</div>
          <div className="text-xs text-zinc-500 mt-1">Processing</div>
        </div>
        <div className="bg-amber-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-amber-400">{queued.length}</div>
          <div className="text-xs text-zinc-500 mt-1">In Queue</div>
        </div>
        <div className="bg-pink-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-pink-400">{review.length}</div>
          <div className="text-xs text-zinc-500 mt-1">Needs Review</div>
        </div>
        <div className="bg-blue-500/10 rounded-lg p-4 text-center">
          <div className="text-3xl font-bold text-blue-400">{completed.length}</div>
          <div className="text-xs text-zinc-500 mt-1">Completed</div>
        </div>
      </div>

      {/* Current processing */}
      {processing.length > 0 && (
        <section className="mb-6">
          <h2 className="text-sm font-medium text-zinc-400 mb-2">Processing</h2>
          <QueueList tasks={processing} />
        </section>
      )}

      {/* Queue */}
      {queued.length > 0 && (
        <section className="mb-6">
          <h2 className="text-sm font-medium text-zinc-400 mb-2">Queue</h2>
          <QueueList tasks={queued} />
        </section>
      )}

      {/* Needs review */}
      {review.length > 0 && (
        <section>
          <h2 className="text-sm font-medium text-zinc-400 mb-2">Needs Review</h2>
          <QueueList tasks={review} onTaskClick={handleTaskClick} />
        </section>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: Dashboard page with queue status cards + real-time progress"
```

---

### Task 6: New Task Page

**Files:**
- Modify: `frontend/src/pages/NewTask.tsx`

- [ ] **Step 1: Replace frontend/src/pages/NewTask.tsx**

```tsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTaskStore } from "../store/taskStore";
import { useSettingsStore } from "../store/settingsStore";
import { glossaries as glossaryApi } from "../services/api";
import type { Glossary } from "../types/glossary";

export function NewTask() {
  const [videoPath, setVideoPath] = useState("");
  const [asrModel, setAsrModel] = useState("faster_whisper");
  const [selectedGlossary, setSelectedGlossary] = useState<number | null>(null);
  const [glossaryList, setGlossaryList] = useState<Glossary[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const { createTask } = useTaskStore();
  const { models, fetchModels } = useSettingsStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchModels();
    glossaryApi.list().then(setGlossaryList).catch(() => {});
  }, [fetchModels]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoPath.trim()) {
      setError("Please enter a video path");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      await createTask(videoPath.trim(), asrModel);
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
          <label className="block text-sm text-zinc-400 mb-1">Video Path (on shared storage)</label>
          <input
            type="text"
            value={videoPath}
            onChange={(e) => setVideoPath(e.target.value)}
            placeholder="/shared/input/interview.mxf"
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          />
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1">ASR Engine</label>
          <select
            value={asrModel}
            onChange={(e) => setAsrModel(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          >
            {(models?.asr_models || ["faster_whisper", "whisper_cpp"]).map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1">Glossary (optional)</label>
          <select
            value={selectedGlossary ?? ""}
            onChange={(e) => setSelectedGlossary(e.target.value ? Number(e.target.value) : null)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          >
            <option value="">None</option>
            {glossaryList.map((g) => (
              <option key={g.id} value={g.id}>{g.name}</option>
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
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/NewTask.tsx
git commit -m "feat: New Task page — video path, ASR engine, glossary selection"
```

---

### Task 7: Glossary Management Page

**Files:**
- Modify: `frontend/src/pages/Glossary.tsx`

- [ ] **Step 1: Replace frontend/src/pages/Glossary.tsx**

```tsx
import { useState, useEffect } from "react";
import { glossaries as api } from "../services/api";
import type { Glossary, GlossaryEntry } from "../types/glossary";

export function GlossaryPage() {
  const [list, setList] = useState<Glossary[]>([]);
  const [selected, setSelected] = useState<Glossary | null>(null);
  const [entries, setEntries] = useState<GlossaryEntry[]>([]);
  const [newName, setNewName] = useState("");
  const [newSource, setNewSource] = useState("");
  const [newTarget, setNewTarget] = useState("");

  useEffect(() => {
    api.list().then(setList);
  }, []);

  const selectGlossary = async (g: Glossary) => {
    setSelected(g);
    const e = await api.getEntries(g.id);
    setEntries(e);
  };

  const createGlossary = async () => {
    if (!newName.trim()) return;
    const g = await api.create(newName.trim());
    setList([g, ...list]);
    setNewName("");
    selectGlossary(g);
  };

  const deleteGlossary = async (id: number) => {
    await api.delete(id);
    setList(list.filter((g) => g.id !== id));
    if (selected?.id === id) {
      setSelected(null);
      setEntries([]);
    }
  };

  const addEntry = async () => {
    if (!selected || !newSource.trim() || !newTarget.trim()) return;
    const added = await api.addEntries(selected.id, [
      { source_term: newSource.trim(), target_term: newTarget.trim() },
    ]);
    setEntries([...entries, ...added]);
    setNewSource("");
    setNewTarget("");
  };

  const handleCsvImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selected || !e.target.files?.[0]) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    const token = localStorage.getItem("token");
    await fetch(`http://localhost:8000/api/glossaries/${selected.id}/import`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    const updated = await api.getEntries(selected.id);
    setEntries(updated);
    e.target.value = "";
  };

  return (
    <div className="flex gap-6 h-full">
      {/* Left: glossary list */}
      <div className="w-64 space-y-3">
        <h1 className="text-2xl font-bold">Glossary</h1>
        <div className="flex gap-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="New glossary name"
            className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-100"
            onKeyDown={(e) => e.key === "Enter" && createGlossary()}
          />
          <button onClick={createGlossary} className="bg-blue-600 px-3 py-1 rounded text-sm">+</button>
        </div>
        <div className="space-y-1">
          {list.map((g) => (
            <div
              key={g.id}
              className={`flex justify-between items-center px-3 py-2 rounded cursor-pointer text-sm ${
                selected?.id === g.id ? "bg-blue-500/10 text-blue-400" : "text-zinc-400 hover:bg-zinc-800"
              }`}
              onClick={() => selectGlossary(g)}
            >
              <span className="truncate">{g.name}</span>
              <button
                onClick={(e) => { e.stopPropagation(); deleteGlossary(g.id); }}
                className="text-zinc-600 hover:text-red-400 text-xs"
              >
                x
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Right: entries */}
      <div className="flex-1">
        {selected ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">{selected.name}</h2>
              <div className="flex gap-2">
                <label className="bg-zinc-800 px-3 py-1 rounded text-sm cursor-pointer hover:bg-zinc-700">
                  Import CSV
                  <input type="file" accept=".csv" className="hidden" onChange={handleCsvImport} />
                </label>
                <a
                  href={api.exportUrl(selected.id)}
                  target="_blank"
                  className="bg-zinc-800 px-3 py-1 rounded text-sm hover:bg-zinc-700"
                >
                  Export CSV
                </a>
              </div>
            </div>

            {/* Add entry form */}
            <div className="flex gap-2 mb-4">
              <input
                value={newSource}
                onChange={(e) => setNewSource(e.target.value)}
                placeholder="English term"
                className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-100"
              />
              <input
                value={newTarget}
                onChange={(e) => setNewTarget(e.target.value)}
                placeholder="Chinese translation"
                className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-100"
                onKeyDown={(e) => e.key === "Enter" && addEntry()}
              />
              <button onClick={addEntry} className="bg-blue-600 px-3 py-1 rounded text-sm">Add</button>
            </div>

            {/* Entries table */}
            <div className="space-y-1">
              {entries.map((entry) => (
                <div key={entry.id} className="flex gap-4 bg-zinc-900 rounded px-3 py-2 text-sm">
                  <span className="flex-1 text-zinc-200">{entry.source_term}</span>
                  <span className="flex-1 text-blue-400">{entry.target_term}</span>
                </div>
              ))}
              {entries.length === 0 && <p className="text-zinc-600 text-sm">No entries yet</p>}
            </div>
          </>
        ) : (
          <p className="text-zinc-600">Select a glossary to view entries</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Glossary.tsx
git commit -m "feat: Glossary management page — CRUD, CSV import/export"
```

---

### Task 8: History + Settings Pages

**Files:**
- Modify: `frontend/src/pages/History.tsx`
- Modify: `frontend/src/pages/Settings.tsx`

- [ ] **Step 1: Replace frontend/src/pages/History.tsx**

```tsx
import { useEffect } from "react";
import { useTaskStore } from "../store/taskStore";
import { QueueList } from "../components/queue/QueueList";

export function History() {
  const { tasks, fetchTasks } = useTaskStore();

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const sorted = [...tasks].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">History</h1>
      <QueueList tasks={sorted} />
    </div>
  );
}
```

- [ ] **Step 2: Replace frontend/src/pages/Settings.tsx**

```tsx
import { useState, useEffect } from "react";
import { useSettingsStore } from "../store/settingsStore";

export function SettingsPage() {
  const { settings, fetchSettings, updateSettings, serverUrl, setServerUrl } = useSettingsStore();
  const [localUrl, setLocalUrl] = useState(serverUrl);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async () => {
    if (settings) {
      await updateSettings(settings);
    }
    setServerUrl(localUrl);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (!settings) return <p className="text-zinc-500">Loading settings...</p>;

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Server URL</label>
          <input
            value={localUrl}
            onChange={(e) => setLocalUrl(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Shared Storage Path</label>
          <input
            value={settings.storage_base_path}
            onChange={(e) => updateSettings({ storage_base_path: e.target.value })}
            placeholder="/data/media"
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">Default ASR Model</label>
          <input
            value={settings.default_asr_model}
            onChange={(e) => updateSettings({ default_asr_model: e.target.value })}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">LLM API Base</label>
          <input
            value={settings.llm_api_base}
            onChange={(e) => updateSettings({ llm_api_base: e.target.value })}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1">LLM Model</label>
          <input
            value={settings.llm_model}
            onChange={(e) => updateSettings({ llm_model: e.target.value })}
            className="w-full bg-zinc-900 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100"
          />
        </div>
        <button
          onClick={handleSave}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2 text-sm"
        >
          {saved ? "Saved!" : "Save Settings"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: History + Settings pages"
```

---

### Task 9: Final Build Verification + Push

**Files:**
- No new files

- [ ] **Step 1: Full frontend build**

```bash
cd frontend && npm run build
```

Expected: No errors

- [ ] **Step 2: Run backend tests to confirm no regressions**

```bash
cd backend && python3 -m pytest tests/ -v
```

Expected: 73 tests PASS

- [ ] **Step 3: Commit and push**

```bash
cd "/Users/renomacm2/Documents/GitHub Remote Project/studio-captioner-ai"
git push origin main
```

---

## Task Summary

| Task | Description |
|------|-------------|
| 1 | Scaffold Tauri v2 + React + Vite + Tailwind |
| 2 | TypeScript types + REST API client with JWT |
| 3 | Zustand stores (auth, task, settings) + WebSocket hooks |
| 4 | App layout, sidebar, router, login page |
| 5 | Dashboard page (queue status + real-time progress) |
| 6 | New Task page (video path, ASR, glossary selection) |
| 7 | Glossary management page (CRUD, CSV import/export) |
| 8 | History + Settings pages |
| 9 | Final build verification + push |

**Phase 4A output:** A working Tauri desktop app with:
- Login/register with JWT auth
- Sidebar navigation (6 pages)
- Dashboard with real-time queue status via WebSocket
- New Task submission (video path, ASR engine, glossary)
- Glossary management (CRUD, CSV import/export)
- Task history list
- Server settings configuration
- Ready for Phase 4B (Subtitle Editor)
