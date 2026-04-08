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
  const { segments, selectedIndex, confidenceScores, currentTime, setCurrentTime, selectSegment, updateSegment } = useEditorStore();

  // Initialize WaveSurfer
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
      url: preview.videoUrl(taskId),
      plugins: [regions],
    });

    ws.on("timeupdate", (time: number) => {
      setCurrentTime(Math.round(time * 1000));
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
        color: isSelected ? "rgba(96, 165, 250, 0.2)" : isLow ? "rgba(248, 113, 113, 0.15)" : "rgba(52, 211, 153, 0.1)",
        drag: false,
        resize: true,
        id: `seg-${i}`,
      });
    });
  }, [segments, selectedIndex, confidenceScores]);

  // Handle region interactions
  useEffect(() => {
    const regions = regionsRef.current;
    if (!regions) return;

    const handleUpdate = (region: any) => {
      const match = region.id?.match(/^seg-(\d+)$/);
      if (!match) return;
      const idx = parseInt(match[1], 10);
      updateSegment(idx, { start_time: Math.round(region.start * 1000), end_time: Math.round(region.end * 1000) });
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

  // Sync seek from external (subtitle list click)
  useEffect(() => {
    const ws = wsRef.current;
    if (!ws || !ws.getDuration()) return;
    const wsTime = ws.getCurrentTime() * 1000;
    if (Math.abs(wsTime - currentTime) > 500) {
      ws.seekTo(currentTime / 1000 / ws.getDuration());
    }
  }, [currentTime]);

  return (
    <div className="bg-zinc-900/50 border-t border-zinc-800">
      <div ref={containerRef} className="px-3 py-2" />
    </div>
  );
}
