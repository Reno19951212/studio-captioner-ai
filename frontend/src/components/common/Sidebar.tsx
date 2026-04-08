import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/new-task", label: "New Task" },
  { to: "/glossary", label: "Glossary" },
  { to: "/history", label: "History" },
  { to: "/settings", label: "Settings" },
];

export function Sidebar() {
  const { userName, logout } = useAuthStore();
  return (
    <aside className="w-56 bg-zinc-900 border-r border-zinc-800 flex flex-col h-screen">
      <div className="p-4 text-blue-400 font-bold text-sm">Studio Captioner AI</div>
      <nav className="flex-1">
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-2 px-4 py-2.5 text-sm ${isActive ? "bg-blue-500/10 text-blue-400 border-l-2 border-blue-400" : "text-zinc-400 hover:text-zinc-200 border-l-2 border-transparent"}`
            }>{item.label}</NavLink>
        ))}
      </nav>
      <div className="border-t border-zinc-800 p-3">
        <div className="text-xs text-zinc-500">{userName}</div>
        <button onClick={logout} className="text-xs text-zinc-600 hover:text-zinc-400 mt-1">Logout</button>
      </div>
    </aside>
  );
}
