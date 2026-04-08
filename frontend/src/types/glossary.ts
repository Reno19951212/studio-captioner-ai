export interface Glossary {
  id: number;
  name: string;
  description: string;
  created_by: number;
  created_at: string;
}

export interface GlossaryEntry {
  id: number;
  glossary_id: number;
  source_term: string;
  target_term: string;
}
