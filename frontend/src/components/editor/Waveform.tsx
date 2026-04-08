import { useRef, useEffect } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import { useEditorStore } from "../../store/editorStore";
import { preview } from "../../services/api";

interface WaveformProps { taskId: number; }

const CONFIDENCE_THRESHOLD = 0.9;

export function Waveform({ taskId }: WaveformProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const seekingFromStore = useRef(false);

  const {
    segments, selectedIndex, confidenceScores, currentTime,
    setCurrentTime, selectSegment, updateSegment,
  } = useEditorStore();

  // Initialize WaveSurfer — load AUDIO waveform JSON (not raw video)
  useEffect(() => {
    if (!containerRef.current) return;
    const regions = RegionsPlugin.create();
    regionsRef.current = regions;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#4a4a5a",
      progressColor: "#60a5fa",
      cursorColor: "#ffffff",
      cursorWidth: 2,
      height: 80,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      // Use the video URL directly — wavesurfer can decode audio from mp4
      url: preview.videoUrl(taskId),
      plugins: [regions],
    });

    ws.on("timeupdate", (time: number) => {
      if (!seekingFromStore.current) {
        setCurrentTime(Math.round(time * 1000));
      }
    });

    ws.on("click", () => {
      // Clicking waveform updates currentTime via timeupdate
    });

    wsRef.current = ws;
    return () => { ws.destroy(); wsRef.current = null; };
  }, [taskId, setCurrentTime]);

  // Update regions when segments change
  useEffect(() => {
    const regions = regionsRef.current;
    if (!regions) return;
    regions.clearRegions();

    segments.forEach((seg, i) => {
      const isLow = confidenceScores[i] !== undefined && confidenceScores[i] < CONFIDENCE_THRESHOLD;
      const isSelected = selectedIndex === i;
      regions.addRegion({
        start: seg.start_time / 1000,
        end: seg.end_time / 1000,
        color: isSelected
          ? "rgba(96, 165, 250, 0.25)"
          : isLow
          ? "rgba(248, 113, 113, 0.15)"
          : "rgba(52, 211, 153, 0.08)",
        drag: true,
        resize: true,
        id: `seg-${i}`,
      });
    });
  }, [segments, selectedIndex, confidenceScores]);

  // Handle region drag/resize
  useEffect(() => {
    const regions = regionsRef.current;
    if (!regions) return;

    const handleUpdate = (region: any) => {
      const match = region.id?.match(/^seg-(\d+)$/);
      if (!match) return;
      updateSegment(parseInt(match[1], 10), {
        start_time: Math.round(region.start * 1000),
        end_time: Math.round(region.end * 1000),
      });
    };

    const handleClick = (region: any) => {
      const match = region.id?.match(/^seg-(\d+)$/);
      if (!match) return;
      selectSegment(parseInt(match[1], 10));
    };

    regions.on("region-updated", handleUpdate);
    regions.on("region-clicked", handleClick);
    return () => {
      regions.un("region-updated", handleUpdate);
      regions.un("region-clicked", handleClick);
    };
  }, [updateSegment, selectSegment]);

  // Seek waveform when video currentTime changes externally (from subtitle click)
  useEffect(() => {
    const ws = wsRef.current;
    if (!ws) return;
    const duration = ws.getDuration();
    if (!duration) return;
    const wsMs = Math.round(ws.getCurrentTime() * 1000);
    if (Math.abs(wsMs - currentTime) > 300) {
      seekingFromStore.current = true;
      ws.seekTo(Math.max(0, Math.min(currentTime / 1000 / duration, 1)));
      setTimeout(() => { seekingFromStore.current = false; }, 200);
    }
  }, [currentTime]);

  return (
    <div className="bg-zinc-900/60 border-t border-zinc-800">
      <div className="text-xs text-zinc-600 px-3 pt-1">Waveform — drag regions to adjust timing</div>
      <div ref={containerRef} className="px-3 py-1" />
    </div>
  );
}
