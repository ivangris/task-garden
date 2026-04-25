import type { NavScreen, Project, Task } from "../../lib/types";

export type TaskFilters = {
  status: string;
  projectId: string;
  dateRange: "all_active" | "today" | "this_week" | "overdue" | "completed";
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

function startOfLocalDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function dayKey(value: string | null): number | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return startOfLocalDay(date).getTime();
}

function isActiveTask(task: Task): boolean {
  return task.status !== "completed" && task.status !== "archived";
}

function isDueToday(value: string | null): boolean {
  const taskDay = dayKey(value);
  if (taskDay === null) {
    return false;
  }

  return taskDay === startOfLocalDay(new Date()).getTime();
}

function isOverdue(value: string | null): boolean {
  const taskDay = dayKey(value);
  if (taskDay === null) {
    return false;
  }

  return taskDay < startOfLocalDay(new Date()).getTime();
}

function isDueThisWeek(value: string | null): boolean {
  const taskDay = dayKey(value);
  if (taskDay === null) {
    return false;
  }

  const today = startOfLocalDay(new Date());
  const weekEnd = new Date(today);
  weekEnd.setDate(today.getDate() + 6);
  return taskDay >= today.getTime() && taskDay <= weekEnd.getTime();
}

function sortTasksForPlanning(tasks: Task[]): Task[] {
  return [...tasks].sort((a, b) => {
    const aDue = dayKey(a.due_date) ?? Number.MAX_SAFE_INTEGER;
    const bDue = dayKey(b.due_date) ?? Number.MAX_SAFE_INTEGER;
    if (aDue !== bDue) {
      return aDue - bDue;
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

export function tasksForScreen(screen: NavScreen, tasks: Task[]): Task[] {
  switch (screen) {
    case "inbox":
    case "planning":
      return sortTasksForPlanning(tasks);
    default:
      return sortTasksForPlanning(tasks.filter((task) => isActiveTask(task)));
  }
}

export function applyTaskFilters(tasks: Task[], filters: TaskFilters): Task[] {
  return tasks.filter((task) => {
    if (filters.dateRange === "completed") {
      if (task.status !== "completed") {
        return false;
      }
    } else {
      if (!isActiveTask(task)) {
        return false;
      }
      if (filters.dateRange === "today" && !isDueToday(task.due_date)) {
        return false;
      }
      if (filters.dateRange === "this_week" && !isDueThisWeek(task.due_date)) {
        return false;
      }
      if (filters.dateRange === "overdue" && !isOverdue(task.due_date)) {
        return false;
      }
      if (filters.status !== "all" && task.status !== filters.status) {
        return false;
      }
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
