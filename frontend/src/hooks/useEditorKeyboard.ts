import { useEffect } from "react";
import { useEditorStore } from "../store/editorStore";

export function useEditorKeyboard() {
  const { selectNext, selectPrev, saveSubtitles, setIsPlaying, isPlaying } = useEditorStore();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      switch (e.key) {
        case "ArrowDown": case "j": e.preventDefault(); selectNext(); break;
        case "ArrowUp": case "k": e.preventDefault(); selectPrev(); break;
        case " ": e.preventDefault(); setIsPlaying(!isPlaying); break;
        case "s":
          if (e.metaKey || e.ctrlKey) { e.preventDefault(); saveSubtitles(); }
          break;
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [selectNext, selectPrev, saveSubtitles, setIsPlaying, isPlaying]);
}
