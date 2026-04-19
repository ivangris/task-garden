export const SCHEMA_VERSION = "0.1.0";

export const extractionCandidateShape = {
  title: "string",
  details: "string | null",
  project_or_group: "string | null",
  priority: "'low' | 'medium' | 'high' | 'critical'",
  effort: "'small' | 'medium' | 'large'",
  energy: "'low' | 'medium' | 'high'",
  labels: "string[]",
  due_date: "string | null",
  parent_task_title: "string | null",
  confidence: "number",
  source_excerpt: "string | null"
} as const;

