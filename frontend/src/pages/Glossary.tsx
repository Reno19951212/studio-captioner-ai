import { useState, useEffect } from "react";
import { glossaries as api } from "../services/api";
import type { Glossary, GlossaryEntry } from "../types/glossary";

export function GlossaryPage() {
  const [list, setList] = useState<Glossary[]>([]);
  const [selected, setSelected] = useState<Glossary | null>(null);
  const [entries, setEntries] = useState<GlossaryEntry[]>([]);
  const [newName, setNewName] = useState("");
  const [newSource, setNewSource] = useState("");
  const [newTarget, setNewTarget] = useState("");

  useEffect(() => { api.list().then(setList); }, []);

  const selectGlossary = async (g: Glossary) => { setSelected(g); setEntries(await api.getEntries(g.id)); };
  const createGlossary = async () => { if (!newName.trim()) return; const g = await api.create(newName.trim()); setList([g, ...list]); setNewName(""); selectGlossary(g); };
  const deleteGlossary = async (id: number) => { await api.delete(id); setList(list.filter((g) => g.id !== id)); if (selected?.id === id) { setSelected(null); setEntries([]); } };
  const addEntry = async () => {
    if (!selected || !newSource.trim() || !newTarget.trim()) return;
    const added = await api.addEntries(selected.id, [{ source_term: newSource.trim(), target_term: newTarget.trim() }]);
    setEntries([...entries, ...added]); setNewSource(""); setNewTarget("");
  };
  const handleCsvImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selected || !e.target.files?.[0]) return;
    const formData = new FormData(); formData.append("file", e.target.files[0]);
    const token = localStorage.getItem("token");
    await fetch(`http://localhost:8000/api/glossaries/${selected.id}/import`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData });
    setEntries(await api.getEntries(selected.id)); e.target.value = "";
  };

  return (
    <div className="flex gap-6 h-full">
      <div className="w-64 space-y-3">
        <h1 className="text-2xl font-bold">Glossary</h1>
        <div className="flex gap-2">
          <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="New glossary name"
            className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-100"
            onKeyDown={(e) => e.key === "Enter" && createGlossary()} />
          <button onClick={createGlossary} className="bg-blue-600 px-3 py-1 rounded text-sm">+</button>
        </div>
        <div className="space-y-1">
          {list.map((g) => (
            <div key={g.id} onClick={() => selectGlossary(g)}
              className={`flex justify-between items-center px-3 py-2 rounded cursor-pointer text-sm ${selected?.id === g.id ? "bg-blue-500/10 text-blue-400" : "text-zinc-400 hover:bg-zinc-800"}`}>
              <span className="truncate">{g.name}</span>
              <button onClick={(e) => { e.stopPropagation(); deleteGlossary(g.id); }} className="text-zinc-600 hover:text-red-400 text-xs">x</button>
            </div>
          ))}
        </div>
      </div>
      <div className="flex-1">
        {selected ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">{selected.name}</h2>
              <div className="flex gap-2">
                <label className="bg-zinc-800 px-3 py-1 rounded text-sm cursor-pointer hover:bg-zinc-700">
                  Import CSV<input type="file" accept=".csv" className="hidden" onChange={handleCsvImport} />
                </label>
                <a href={api.exportUrl(selected.id)} target="_blank" className="bg-zinc-800 px-3 py-1 rounded text-sm hover:bg-zinc-700">Export CSV</a>
              </div>
            </div>
            <div className="flex gap-2 mb-4">
              <input value={newSource} onChange={(e) => setNewSource(e.target.value)} placeholder="English term"
                className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-100" />
              <input value={newTarget} onChange={(e) => setNewTarget(e.target.value)} placeholder="Chinese translation"
                className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2 py-1 text-sm text-zinc-100"
                onKeyDown={(e) => e.key === "Enter" && addEntry()} />
              <button onClick={addEntry} className="bg-blue-600 px-3 py-1 rounded text-sm">Add</button>
            </div>
            <div className="space-y-1">
              {entries.map((entry) => (
                <div key={entry.id} className="flex gap-4 bg-zinc-900 rounded px-3 py-2 text-sm">
                  <span className="flex-1 text-zinc-200">{entry.source_term}</span>
                  <span className="flex-1 text-blue-400">{entry.target_term}</span>
                </div>
              ))}
              {entries.length === 0 && <p className="text-zinc-600 text-sm">No entries yet</p>}
            </div>
          </>
        ) : <p className="text-zinc-600">Select a glossary to view entries</p>}
      </div>
    </div>
  );
}
