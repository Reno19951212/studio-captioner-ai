"""CSV import/export for glossary entries."""
import csv
import io
from typing import Dict, List, Tuple

def parse_csv(content: str) -> List[Tuple[str, str]]:
    reader = csv.DictReader(io.StringIO(content))
    entries = []
    for row in reader:
        source = row.get("source_term", "").strip()
        target = row.get("target_term", "").strip()
        if source and target:
            entries.append((source, target))
    return entries

def entries_to_csv(entries: List[Dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["source_term", "target_term"])
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry)
    return output.getvalue()
