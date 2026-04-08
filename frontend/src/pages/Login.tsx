import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export function Login() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { login, register, isAuthenticated, loadFromStorage } = useAuthStore();
  const navigate = useNavigate();
  const nameRef = useRef<HTMLInputElement>(null);

  // Auto-redirect if already logged in
  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  useEffect(() => {
    if (isAuthenticated) navigate("/", { replace: true });
  }, [isAuthenticated, navigate]);

  // Focus username on mount
  useEffect(() => { nameRef.current?.focus(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !password.trim()) { setError("Please enter username and password"); return; }
    setError("");
    setLoading(true);
    try {
      if (isRegister) await register(name.trim(), password);
      await login(name.trim(), password);
      navigate("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-zinc-950">
      <form onSubmit={handleSubmit} className="bg-zinc-900 p-8 rounded-lg w-80 space-y-4 shadow-xl">
        <div className="text-center">
          <h1 className="text-xl font-bold text-zinc-100">Studio Captioner AI</h1>
          <p className="text-xs text-zinc-500 mt-1">On-premise video captioning</p>
        </div>
        {error && <div className="bg-red-900/30 border border-red-700 text-red-400 text-sm text-center py-2 px-3 rounded">{error}</div>}
        <input
          ref={nameRef}
          type="text"
          placeholder="Username"
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoComplete="username"
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-700 text-white rounded py-2 text-sm font-medium"
        >
          {loading ? "…" : isRegister ? "Register & Login" : "Login"}
        </button>
        <button
          type="button"
          onClick={() => { setIsRegister(!isRegister); setError(""); }}
          className="w-full text-zinc-500 text-xs hover:text-zinc-300"
        >
          {isRegister ? "Already have an account? Login" : "New user? Register"}
        </button>
      </form>
    </div>
  );
}
