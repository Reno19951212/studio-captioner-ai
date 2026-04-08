import { useState, useEffect, useCallback } from "react";

type ToastType = "success" | "error" | "info";

interface Toast { id: number; message: string; type: ToastType; }

let _addToast: ((msg: string, type?: ToastType) => void) | null = null;

export function toast(message: string, type: ToastType = "success") {
  _addToast?.(message, type);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  let nextId = 0;

  const add = useCallback((message: string, type: ToastType = "success") => {
    const id = ++nextId;
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);

  useEffect(() => { _addToast = add; return () => { _addToast = null; }; }, [add]);

  const colors: Record<ToastType, string> = {
    success: "bg-emerald-700 text-white",
    error: "bg-red-700 text-white",
    info: "bg-zinc-700 text-zinc-100",
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`${colors[t.type]} rounded-lg px-4 py-2 text-sm shadow-lg
            transition-all duration-300 pointer-events-auto max-w-sm`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}
