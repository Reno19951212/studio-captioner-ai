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
      if (isRegister) await register(name, password);
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
        <input type="text" placeholder="Username" value={name} onChange={(e) => setName(e.target.value)}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100" />
        <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded py-2 text-sm font-medium">
          {isRegister ? "Register & Login" : "Login"}
        </button>
        <button type="button" onClick={() => setIsRegister(!isRegister)} className="w-full text-zinc-500 text-xs hover:text-zinc-300">
          {isRegister ? "Already have an account? Login" : "New user? Register"}
        </button>
      </form>
    </div>
  );
}
