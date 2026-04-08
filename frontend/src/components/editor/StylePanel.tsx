import { useEditorStore } from "../../store/editorStore";

export interface SubtitleStyleConfig {
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  outlineColor: string;
  outlineWidth: number;
  bgEnabled: boolean;
  bgColor: string;
  bgOpacity: number;
  position: "bottom" | "top" | "middle";
}

export function StylePanel() {
  const { subtitleStyle: style, setSubtitleStyle } = useEditorStore();
  const update = (patch: Partial<SubtitleStyleConfig>) => {
    setSubtitleStyle({ ...style, ...patch });
  };

  return (
    <div className="space-y-3 p-3 text-sm overflow-auto flex-1">
      <h3 className="font-medium text-zinc-300">Subtitle Style</h3>
      <div>
        <label className="block text-xs text-zinc-500 mb-1">Font Family</label>
        <select value={style.fontFamily} onChange={(e) => update({ fontFamily: e.target.value })}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100">
          <option value="Noto Sans SC">Noto Sans SC</option>
          <option value="LXGW WenKai">LXGW WenKai</option>
          <option value="Arial">Arial</option>
          <option value="Microsoft YaHei">Microsoft YaHei</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-zinc-500 mb-1">Font Size: {style.fontSize}px</label>
        <input type="range" min={12} max={72} value={style.fontSize}
          onChange={(e) => update({ fontSize: Number(e.target.value) })} className="w-full" />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs text-zinc-500 mb-1">Font Color</label>
          <input type="color" value={style.fontColor}
            onChange={(e) => update({ fontColor: e.target.value })}
            className="w-full h-8 bg-zinc-800 border border-zinc-700 rounded cursor-pointer" />
        </div>
        <div>
          <label className="block text-xs text-zinc-500 mb-1">Outline Color</label>
          <input type="color" value={style.outlineColor}
            onChange={(e) => update({ outlineColor: e.target.value })}
            className="w-full h-8 bg-zinc-800 border border-zinc-700 rounded cursor-pointer" />
        </div>
      </div>
      <div>
        <label className="block text-xs text-zinc-500 mb-1">Outline Width: {style.outlineWidth}px</label>
        <input type="range" min={0} max={6} value={style.outlineWidth}
          onChange={(e) => update({ outlineWidth: Number(e.target.value) })} className="w-full" />
      </div>
      <div>
        <label className="block text-xs text-zinc-500 mb-1">Position</label>
        <select value={style.position}
          onChange={(e) => update({ position: e.target.value as SubtitleStyleConfig["position"] })}
          className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-100">
          <option value="bottom">Bottom</option>
          <option value="top">Top</option>
          <option value="middle">Middle</option>
        </select>
      </div>
      <div>
        <label className="flex items-center gap-2 text-xs text-zinc-500 cursor-pointer">
          <input type="checkbox" checked={style.bgEnabled}
            onChange={(e) => update({ bgEnabled: e.target.checked })} />
          Background Box
        </label>
        {style.bgEnabled && (
          <div className="mt-2 grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-zinc-500 mb-1">BG Color</label>
              <input type="color" value={style.bgColor}
                onChange={(e) => update({ bgColor: e.target.value })}
                className="w-full h-8 bg-zinc-800 border border-zinc-700 rounded cursor-pointer" />
            </div>
            <div>
              <label className="block text-xs text-zinc-500 mb-1">Opacity: {Math.round(style.bgOpacity * 100)}%</label>
              <input type="range" min={0} max={100} value={style.bgOpacity * 100}
                onChange={(e) => update({ bgOpacity: Number(e.target.value) / 100 })} className="w-full" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
