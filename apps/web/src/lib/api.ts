import type {
  CreateEntryInput,
  CreateProjectInput,
  CreateTaskInput,
  Project,
  RawEntry,
  Settings,
  Task,
  UpdateTaskInput,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  listEntries: () => request<{ items: RawEntry[] }>("/entries"),
  createEntry: (payload: CreateEntryInput) =>
    request<RawEntry>("/entries", { method: "POST", body: JSON.stringify(payload) }),
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
  getSettings: () => request<Settings>("/settings"),
  patchSettings: (payload: Partial<Settings>) =>
    request<Settings>("/settings", { method: "PATCH", body: JSON.stringify(payload) }),
};

