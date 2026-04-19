export type NavScreen = "capture" | "inbox" | "today" | "this-week" | "projects" | "completed" | "settings";

export type SourceType = "typed" | "pasted" | "audio_transcript";
export type TaskStatus = "inbox" | "planned" | "in_progress" | "blocked" | "completed" | "archived";
export type TaskPriority = "low" | "medium" | "high" | "critical";
export type TaskEffort = "small" | "medium" | "large";
export type TaskEnergy = "low" | "medium" | "high";

export type RawEntry = {
  id: string;
  source_type: SourceType;
  raw_text: string;
  entry_status: string;
  device_id: string | null;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: string;
  name: string;
  description: string | null;
  color_token: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
};

export type Task = {
  id: string;
  title: string;
  details: string | null;
  project_id: string | null;
  project_name: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  effort: TaskEffort;
  energy: TaskEnergy;
  source_raw_entry_id: string | null;
  created_at: string;
  updated_at: string;
  due_date: string | null;
  completed_at: string | null;
  device_id: string | null;
};

export type Settings = {
  local_only_mode: boolean;
  cloud_enabled: boolean;
  stt_provider: string;
  task_extraction_provider: string;
  sync_provider: string;
  auth_provider: string;
  stt_model: string;
  extraction_model: string;
  sync_base_url: string | null;
};

export type CreateEntryInput = {
  source_type: SourceType;
  raw_text: string;
};

export type CreateProjectInput = {
  name: string;
  description?: string;
  color_token?: string;
};

export type CreateTaskInput = {
  title: string;
  details?: string;
  project_id?: string;
  status: TaskStatus;
  priority: TaskPriority;
  effort: TaskEffort;
  energy: TaskEnergy;
  due_date?: string;
  source_raw_entry_id?: string;
};

export type UpdateTaskInput = Partial<Pick<Task, "title" | "details" | "project_id" | "status" | "priority" | "effort" | "energy">> & {
  due_date?: string | null;
};

