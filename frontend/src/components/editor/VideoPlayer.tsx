import { useRef, useEffect, useCallback } from "react";
import { useEditorStore } from "../../store/editorStore";
import { preview } from "../../services/api";

interface VideoPlayerProps { taskId: number; }

export function VideoPlayer({ taskId }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const {
    segments, currentTime, isPlaying, selectedIndex,
    setCurrentTime, setIsPlaying, getActiveSegmentIndex,
    subtitleStyle: style,
  } = useEditorStore();

  const activeIndex = getActiveSegmentIndex();
  const activeSegment = activeIndex >= 0 ? segments[activeIndex] : null;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying && video.paused) video.play();
    if (!isPlaying && !video.paused) video.pause();
  }, [isPlaying]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || selectedIndex === null) return;
    const seg = segments[selectedIndex];
    if (seg) video.currentTime = seg.start_time / 1000;
  }, [selectedIndex, segments]);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (video) setCurrentTime(Math.round(video.currentTime * 1000));
  }, [setCurrentTime]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) { video.play(); setIsPlaying(true); }
    else { video.pause(); setIsPlaying(false); }
  };

  const formatTime = (ms: number) => {
    const totalSec = Math.floor(ms / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  };

  // Build subtitle overlay position class
  const positionClass =
    style.position === "top" ? "top-6" :
    style.position === "middle" ? "top-1/2 -translate-y-1/2" :
    "bottom-10";

  // Build text shadow from outline settings
  const textShadow =
    style.outlineWidth > 0
      ? `${style.outlineWidth}px ${style.outlineWidth}px 0 ${style.outlineColor},
         -${style.outlineWidth}px ${style.outlineWidth}px 0 ${style.outlineColor},
         ${style.outlineWidth}px -${style.outlineWidth}px 0 ${style.outlineColor},
         -${style.outlineWidth}px -${style.outlineWidth}px 0 ${style.outlineColor}`
      : undefined;

  // Build background style
  const bgStyle = style.bgEnabled
    ? {
        backgroundColor: style.bgColor,
        opacity: style.bgOpacity,
        position: "absolute" as const,
        inset: 0,
        borderRadius: "4px",
      }
    : undefined;

  const subtitleTextStyle = {
    fontFamily: style.fontFamily,
    fontSize: `${style.fontSize}px`,
    color: style.fontColor,
    textShadow,
    lineHeight: 1.4,
  };

  return (
    <div className="flex flex-col bg-black rounded-lg overflow-hidden h-full">
      <div className="flex-1 relative flex items-center justify-center min-h-0">
        <video ref={videoRef} src={preview.videoUrl(taskId)} onTimeUpdate={handleTimeUpdate}
          onPlay={() => setIsPlaying(true)} onPause={() => setIsPlaying(false)}
          className="max-w-full max-h-full object-contain" preload="metadata" />

        {activeSegment && (
          <div className={`absolute left-1/2 -translate-x-1/2 max-w-[85%] text-center ${positionClass}`}>
            {/* Primary line: translated text (if exists) */}
            {activeSegment.translated_text && (
              <div className="relative inline-block mb-1 px-3 py-0.5 rounded">
                {bgStyle && <div style={bgStyle} />}
                <span className="relative" style={subtitleTextStyle}>
                  {activeSegment.translated_text}
                </span>
              </div>
            )}
            {/* Secondary line: source text (smaller, dimmer) */}
            <div className="relative inline-block px-2 py-0.5 rounded">
              {bgStyle && <div style={{ ...bgStyle, opacity: (style.bgOpacity ?? 0.75) * 0.7 }} />}
              <span
                className="relative"
                style={{
                  ...subtitleTextStyle,
                  fontSize: `${Math.max(12, style.fontSize - 4)}px`,
                  color: style.fontColor + "cc",
                }}
              >
                {activeSegment.text}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-center gap-4 py-2 bg-zinc-900/80">
        <span className="text-xs text-zinc-500 w-12 text-right">{formatTime(currentTime)}</span>
        <button onClick={togglePlay} className="text-white hover:text-blue-400 text-lg w-8 text-center">
          {isPlaying ? "⏸" : "▶"}
        </button>
        <span className="text-xs text-zinc-500 w-12">
          {videoRef.current ? formatTime((videoRef.current.duration || 0) * 1000) : "--:--"}
        </span>
      </div>
    </div>
  );
}
