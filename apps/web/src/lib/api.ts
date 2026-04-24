import type {
  CurrentRecommendations,
  CreateAudioEntryInput,
  ConfirmExtractionCandidateInput,
  CreateEntryInput,
  CreateProjectInput,
  CreateTaskInput,
  ExtractionBatch,
  GardenOverview,
  GardenTilesPayload,
  LocalModelsResult,
  Project,
  ProviderCheckResult,
  RawEntry,
  RecapHighlightCard,
  RecapNarrative,
  RecapPeriod,
  RegisteredDevice,
  Settings,
  SyncStatus,
  Task,
  TranscriptionResult,
  UpdateTaskInput,
  WeeklyPreview,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
let currentDeviceId: string | null = null;

function withDeviceHeaders(headers: HeadersInit | undefined): HeadersInit {
  return {
    ...(headers ?? {}),
    ...(currentDeviceId ? { "X-Task-Garden-Device-Id": currentDeviceId } : {}),
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...withDeviceHeaders(init?.headers),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      detail = parsed.detail || text;
    } catch {
      detail = text;
    }
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  setDeviceId: (deviceId: string | null) => {
    currentDeviceId = deviceId;
  },
  listEntries: () => request<{ items: RawEntry[] }>("/entries"),
  archiveEntry: (entryId: string) => request<RawEntry>(`/entries/${entryId}`, { method: "DELETE" }),
  createEntry: (payload: CreateEntryInput) =>
    request<RawEntry>("/entries", { method: "POST", body: JSON.stringify(payload) }),
  createAudioEntry: (payload: CreateAudioEntryInput = {}) =>
    request<RawEntry>("/entries/audio", { method: "POST", body: JSON.stringify(payload) }),
  transcribeEntryAudio: (entryId: string, audioBlob: Blob, fileName = "task-garden-recording.webm") => {
    const body = new FormData();
    body.append("audio", audioBlob, fileName);
    return request<TranscriptionResult>(`/entries/${entryId}/transcribe`, { method: "POST", body });
  },
  extractEntry: (entryId: string) => request<ExtractionBatch>(`/entries/${entryId}/extract`, { method: "POST" }),
  getExtraction: (extractionId: string) => request<ExtractionBatch>(`/extractions/${extractionId}`),
  confirmExtraction: (extractionId: string, candidates: ConfirmExtractionCandidateInput[]) =>
    request<{
      extraction_id: string;
      created_task_ids: string[];
      accepted_count: number;
      rejected_count: number;
      updated_candidates: ExtractionBatch["candidates"];
    }>(`/extractions/${extractionId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ candidates }),
    }),
  listTasks: () => request<{ items: Task[] }>("/tasks"),
  createTask: (payload: CreateTaskInput) =>
    request<Task>("/tasks", { method: "POST", body: JSON.stringify(payload) }),
  patchTask: (taskId: string, payload: UpdateTaskInput) =>
    request<Task>(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  completeTask: (taskId: string) => request<Task>(`/tasks/${taskId}/complete`, { method: "POST" }),
  reopenTask: (taskId: string) => request<Task>(`/tasks/${taskId}/reopen`, { method: "POST" }),
  listProjects: () => request<{ items: Project[] }>("/projects"),
  createProject: (payload: CreateProjectInput) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(payload) }),
  getGardenState: () => request<GardenOverview>("/garden/state"),
  getGardenTiles: () => request<GardenTilesPayload>("/garden/tiles"),
  recomputeGarden: () => request<GardenOverview>("/garden/recompute", { method: "POST" }),
  getCurrentRecommendations: () => request<CurrentRecommendations>("/recommendations/current"),
  createWeeklyPreview: () => request<WeeklyPreview>("/planning/weekly-preview", { method: "POST" }),
  getSettings: () => request<Settings>("/settings"),
  patchSettings: (payload: Partial<Settings>) =>
    request<Settings>("/settings", { method: "PATCH", body: JSON.stringify(payload) }),
  checkProvider: (kind: "task_extraction" | "recap_narrative" | "stt") =>
    request<ProviderCheckResult>("/settings/providers/check", { method: "POST", body: JSON.stringify({ kind }) }),
  listLocalModels: () => request<LocalModelsResult>("/settings/local-models"),
  getSyncStatus: (deviceId?: string) =>
    request<SyncStatus>(deviceId ? `/sync?device_id=${encodeURIComponent(deviceId)}` : "/sync"),
  registerDevice: (payload: { device_id?: string; device_name: string; platform: string; app_version?: string }) =>
    request<RegisteredDevice>("/sync/register-device", { method: "POST", body: JSON.stringify(payload) }),
  generateWeeklyRecap: () => request<RecapPeriod>("/recaps/generate-weekly", { method: "POST" }),
  generateMonthlyRecap: () => request<RecapPeriod>("/recaps/generate-monthly", { method: "POST" }),
  generateYearlyRecap: () => request<RecapPeriod>("/recaps/generate-yearly", { method: "POST" }),
  getRecap: (periodId: string) => request<RecapPeriod>(`/recaps/${periodId}`),
  getRecapCards: (periodId: string) => request<{ items: RecapHighlightCard[] }>(`/recaps/${periodId}/cards`),
  getRecapNarrative: (periodId: string) => request<RecapNarrative>(`/recaps/${periodId}/narrative`),
  generateRecapNarrative: (periodId: string) =>
    request<RecapNarrative>(`/recaps/${periodId}/generate-narrative`, { method: "POST" }),
};
