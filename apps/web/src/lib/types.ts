export type NavScreen = "capture" | "inbox" | "today" | "this-week" | "projects" | "completed" | "garden" | "recaps" | "settings";

export type SourceType = "typed" | "pasted" | "audio_transcript";
export type TaskStatus = "inbox" | "planned" | "in_progress" | "blocked" | "completed" | "archived";
export type TaskPriority = "low" | "medium" | "high" | "critical";
export type TaskEffort = "small" | "medium" | "large";
export type TaskEnergy = "low" | "medium" | "high";

export type RawEntry = {
  id: string;
  source_type: SourceType;
  raw_text: string;
  audio_file_ref: string | null;
  transcript_provider_name: string | null;
  transcript_model_name: string | null;
  transcript_metadata: Record<string, unknown>;
  entry_status: string;
  device_id: string | null;
  created_at: string;
  updated_at: string;
};

export type TranscriptSegment = {
  id: string;
  raw_entry_id: string;
  segment_index: number;
  start_ms: number | null;
  end_ms: number | null;
  text: string;
  speaker_label: string | null;
};

export type TranscriptionResult = {
  raw_entry: RawEntry;
  segments: TranscriptSegment[];
};

export type ExtractionCandidateStatus = "pending_review" | "accepted" | "edited" | "rejected";
export type ExtractionCandidateDecision = "accepted" | "rejected";

export type ExtractionCandidate = {
  id: string;
  extraction_batch_id: string;
  title: string;
  details: string | null;
  project_or_group: string | null;
  priority: TaskPriority;
  effort: TaskEffort;
  energy: TaskEnergy;
  labels: string[];
  due_date: string | null;
  parent_task_title: string | null;
  confidence: number;
  source_excerpt: string | null;
  candidate_status: ExtractionCandidateStatus;
};

export type ExtractionBatch = {
  id: string;
  raw_entry_id: string;
  provider_name: string;
  model_name: string;
  schema_version: string;
  prompt_version: string;
  summary: string | null;
  needs_review: boolean;
  open_questions: string[];
  created_at: string;
  candidates: ExtractionCandidate[];
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
  recap_narrative_provider: string;
  sync_provider: string;
  auth_provider: string;
  stt_model: string;
  extraction_model: string;
  recap_model: string;
  ollama_base_url: string;
  extraction_timeout_seconds: number;
  sync_base_url: string | null;
  stt_executable_path: string | null;
  stt_model_path: string | null;
  stt_ready: boolean;
};

export type ProviderCheckResult = {
  kind: "task_extraction" | "recap_narrative" | "stt";
  provider_name: string;
  ok: boolean;
  message: string;
  model_name: string | null;
  normalized_base_url: string | null;
  details: Record<string, unknown>;
};

export type LocalModelOption = {
  name: string;
  provider_name: string;
  usable_for_chat: boolean;
  size: number | null;
  modified_at: string | null;
};

export type LocalModelsResult = {
  ollama_base_url: string;
  preferred_chat_model: string | null;
  models: LocalModelOption[];
};

export type RegisteredDevice = {
  id: string;
  device_name: string;
  platform: string;
  app_version: string | null;
  registered_at: string;
  last_seen_at: string;
  last_sync_at: string | null;
  is_active: boolean;
};

export type SyncStatus = {
  provider_name: string;
  sync_enabled: boolean;
  current_device: RegisteredDevice | null;
  registered_device_count: number;
  latest_sequence: number;
  last_pull_cursor: number | null;
  last_sync_at: string | null;
};

export type RecommendationReason = {
  label: string;
  value: string;
};

export type RecommendationItem = {
  id: string;
  rule_type: "stale_task" | "overloaded_week" | "neglected_project" | "large_task_breakdown" | "small_wins";
  level: "info" | "warning";
  title: string;
  rationale: string;
  task_id: string | null;
  project_id: string | null;
  metadata: Record<string, unknown>;
  reasons: RecommendationReason[];
};

export type CurrentRecommendations = {
  snapshot_id: string;
  generated_at: string;
  items: RecommendationItem[];
  thresholds: Record<string, number>;
};

export type WeeklyPreview = {
  snapshot_id: string;
  generated_at: string;
  window_start: string;
  window_end: string;
  top_focus_items: Task[];
  warnings: RecommendationItem[];
  suggestion_summaries: string[];
  thresholds: Record<string, number>;
};

export type GardenState = {
  id: string;
  baseline_key: string;
  stage_key: string;
  total_xp: number;
  current_level: number;
  total_growth_units: number;
  total_decay_points: number;
  active_task_count: number;
  overdue_task_count: number;
  restored_tile_count: number;
  healthy_tile_count: number;
  lush_tile_count: number;
  health_score: number;
  last_recomputed_at: string;
};

export type GardenZone = {
  id: string;
  name: string;
  zone_key: string;
  sort_order: number;
  tile_count: number;
  unlocked_at: string | null;
};

export type GardenTile = {
  id: string;
  zone_id: string;
  tile_index: number;
  coord_x: number;
  coord_y: number;
  tile_state: "desert" | "recovering" | "healthy" | "lush";
  growth_units: number;
  decay_points: number;
  last_changed_at: string;
};

export type UnlockEntry = {
  id: string;
  unlock_key: string;
  unlock_type: string;
  threshold_value: number;
  unlocked_at: string;
};

export type DecayEvent = {
  id: string;
  task_id: string;
  task_title: string;
  days_overdue: number;
  decay_points: number;
  recorded_at: string;
};

export type RecoveryEvent = {
  id: string;
  task_id: string;
  task_title: string;
  recovery_points: number;
  xp_amount: number;
  recorded_at: string;
};

export type GardenOverview = {
  state: GardenState;
  zones: GardenZone[];
  unlocks: UnlockEntry[];
  recent_decay_events: DecayEvent[];
  recent_recovery_events: RecoveryEvent[];
};

export type GardenTilesPayload = {
  state: GardenState;
  zones: GardenZone[];
  tiles: GardenTile[];
  plants: {
    id: string;
    garden_tile_id: string;
    plant_key: string;
    growth_stage: string;
    unlocked_at: string | null;
  }[];
  decorations: {
    id: string;
    garden_tile_id: string;
    decoration_key: string;
    variant_key: string | null;
    unlocked_at: string | null;
  }[];
};

export type CreateEntryInput = {
  source_type: SourceType;
  raw_text: string;
};

export type CreateAudioEntryInput = {
  device_id?: string;
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

export type ConfirmExtractionCandidateInput = {
  id: string;
  decision: ExtractionCandidateDecision;
  title: string;
  details?: string | null;
  project_or_group?: string | null;
  priority: TaskPriority;
  effort: TaskEffort;
  energy: TaskEnergy;
  labels: string[];
  due_date?: string | null;
  parent_task_title?: string | null;
  confidence: number;
  source_excerpt?: string | null;
};

export type RecapPeriodType = "weekly" | "monthly" | "yearly";

export type RecapMetricValue = {
  metric_key: string;
  numeric_value: number | null;
  text_value: string | null;
  json_value: Record<string, unknown>;
};

export type RecapHighlightCard = {
  id: string;
  period_id: string;
  card_type: string;
  title: string;
  subtitle: string | null;
  primary_value: string | null;
  secondary_value: string | null;
  supporting_text: string | null;
  visual_hint: string | null;
  sort_order: number;
};

export type RecapMilestone = {
  id: string;
  period_id: string;
  milestone_key: string;
  title: string;
  description: string;
  sort_order: number;
  metric_value: number | null;
  detected_at: string | null;
};

export type RecapStreakSummary = {
  id: string;
  period_id: string;
  current_streak_days: number;
  longest_streak_days: number;
  period_best_streak_days: number;
  active_days: number;
  streak_start: string | null;
  streak_end: string | null;
};

export type RecapProjectSummary = {
  id: string;
  period_id: string;
  project_id: string | null;
  project_name: string;
  completed_task_count: number;
  xp_gained: number;
  completion_share: number;
  effort_small_count: number;
  effort_medium_count: number;
  effort_large_count: number;
  latest_completion_at: string | null;
  sort_order: number;
};

export type RecapNarrative = {
  id: string | null;
  period_id: string;
  generation_status: "not_generated" | "disabled" | "generated" | "failed";
  provider_name: string | null;
  model_name: string | null;
  prompt_version: string | null;
  source_summary_version: string | null;
  source_summary_hash: string | null;
  narrative_text: string | null;
  error_metadata: Record<string, unknown>;
  generated_at: string | null;
};

export type RecapPeriod = {
  id: string;
  period_type: RecapPeriodType;
  period_label: string;
  window_start: string;
  window_end: string;
  generated_at: string;
  metrics: RecapMetricValue[];
  cards: RecapHighlightCard[];
  milestones: RecapMilestone[];
  streak_summary: RecapStreakSummary | null;
  project_summaries: RecapProjectSummary[];
  narrative?: RecapNarrative | null;
};
