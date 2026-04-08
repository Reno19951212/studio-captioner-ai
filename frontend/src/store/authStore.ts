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
  token: null, userId: null, userName: null, isAuthenticated: false,
  login: async (name, password) => {
    const resp = await auth.login(name, password);
    localStorage.setItem("token", resp.token);
    localStorage.setItem("userId", String(resp.id));
    localStorage.setItem("userName", resp.name);
    set({ token: resp.token, userId: resp.id, userName: resp.name, isAuthenticated: true });
  },
  register: async (name, password) => { await auth.register(name, password); },
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
    if (token && userId) set({ token, userId: Number(userId), userName, isAuthenticated: true });
  },
}));
