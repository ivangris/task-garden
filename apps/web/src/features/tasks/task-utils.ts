import type { NavScreen, Project, Task } from "../../lib/types";

export type TaskFilters = {
  status: string;
  projectId: string;
};

export function formatDate(value: string | null): string {
  if (!value) {
    return "No date";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "No date";
  }

  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function toApiDate(value: string): string | undefined {
  if (!value) {
    return undefined;
  }

  return new Date(`${value}T12:00:00`).toISOString();
}

export function toDateInputValue(value: string | null): string {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toISOString().slice(0, 10);
}

function isToday(value: string | null): boolean {
  if (!value) {
    return false;
  }

  const date = new Date(value);
  const now = new Date();
  return date.toDateString() === now.toDateString();
}

function isThisWeek(value: string | null): boolean {
  if (!value) {
    return false;
  }

  const date = new Date(value);
  const now = new Date();
  const end = new Date(now);
  end.setDate(now.getDate() + 6);
  return date >= new Date(now.getFullYear(), now.getMonth(), now.getDate()) && date <= end;
}

export function tasksForScreen(screen: NavScreen, tasks: Task[]): Task[] {
  switch (screen) {
    case "inbox":
      return tasks.filter((task) => task.status === "inbox");
    case "today":
      return tasks.filter((task) => task.status !== "completed" && isToday(task.due_date));
    case "this-week":
      return tasks.filter((task) => task.status !== "completed" && isThisWeek(task.due_date));
    case "completed":
      return tasks.filter((task) => task.status === "completed");
    default:
      return tasks.filter((task) => task.status !== "completed");
  }
}

export function applyTaskFilters(tasks: Task[], filters: TaskFilters): Task[] {
  return tasks.filter((task) => {
    if (filters.status !== "all" && task.status !== filters.status) {
      return false;
    }

    if (filters.projectId !== "all" && task.project_id !== filters.projectId) {
      return false;
    }

    return true;
  });
}

export function projectNameMap(projects: Project[]): Record<string, string> {
  return Object.fromEntries(projects.map((project) => [project.id, project.name]));
}
