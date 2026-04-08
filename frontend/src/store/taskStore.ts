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
  tasks: [], queueStatus: null, loading: false,
  fetchTasks: async () => { set({ loading: true }); const r = await tasks.list(); set({ tasks: r, loading: false }); },
  fetchQueue: async () => { const r = await tasks.queue(); set({ queueStatus: r }); },
  createTask: async (videoPath, asrModel = "faster_whisper") => {
    const task = await tasks.create({ video_path: videoPath, asr_model: asrModel });
    set({ tasks: [task, ...get().tasks] }); return task;
  },
  deleteTask: async (id) => { await tasks.delete(id); set({ tasks: get().tasks.filter((t) => t.id !== id) }); },
  updateTaskFromWs: (taskId, data) => { set({ tasks: get().tasks.map((t) => t.id === taskId ? { ...t, ...data } : t) }); },
  updateQueueFromWs: (data) => { set({ queueStatus: data }); },
}));
