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
import { Editor } from "./pages/Editor";

export default function App() {
  const loadFromStorage = useAuthStore((s) => s.loadFromStorage);
  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-task" element={<NewTask />} />
          <Route path="/glossary" element={<GlossaryPage />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/editor/:taskId" element={<Editor />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
