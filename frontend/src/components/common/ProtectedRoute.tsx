import { Navigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  // Also check localStorage directly to survive full page reloads
  const hasToken = !!localStorage.getItem("token");
  if (!isAuthenticated && !hasToken) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
