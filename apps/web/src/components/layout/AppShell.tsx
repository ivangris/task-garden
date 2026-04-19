import { useEffect, useMemo, useState } from "react";

import { CaptureScreen } from "../screens/CaptureScreen";
import { ProjectsScreen } from "../screens/ProjectsScreen";
import { SettingsScreen } from "../screens/SettingsScreen";
import { TaskScreen } from "../screens/TaskScreen";
import { navItems } from "../../features/navigation/nav-items";
import { api } from "../../lib/api";
import type {
  CreateEntryInput,
  CreateProjectInput,
  CreateTaskInput,
  NavScreen,
  Project,
  RawEntry,
  Settings,
  Task,
  TaskStatus,
  UpdateTaskInput,
} from "../../lib/types";
import { applyTaskFilters, projectNameMap, tasksForScreen, type TaskFilters } from "../../features/tasks/task-utils";

const taskScreenCopy: Record<Exclude<NavScreen, "capture" | "projects" | "settings">, { title: string; subtitle: string }> = {
  inbox: { title: "Inbox", subtitle: "New work and loose ends waiting for a plan." },
  today: { title: "Today", subtitle: "Only work with a due date that matters right now." },
  "this-week": { title: "This Week", subtitle: "The next six days of commitments in one compact view." },
  completed: { title: "Completed", subtitle: "Closed loops, shipped work, and easy reopen support." },
};

export function AppShell(): JSX.Element {
  const [activeItemId, setActiveItemId] = useState<NavScreen>("capture");
  const [entries, setEntries] = useState<RawEntry[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [filters, setFilters] = useState<TaskFilters>({ status: "all", projectId: "all" });
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadAll(): Promise<void> {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [entryData, taskData, projectData, settingsData] = await Promise.all([
        api.listEntries(),
        api.listTasks(),
        api.listProjects(),
        api.getSettings(),
      ]);
      setEntries(entryData.items);
      setTasks(taskData.items);
      setProjects(projectData.items);
      setSettings(settingsData);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to load Task Garden.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  const visibleTasks = useMemo(() => {
    const scoped = tasksForScreen(activeItemId, tasks);
    return applyTaskFilters(scoped, filters);
  }, [activeItemId, filters, tasks]);

  const activeItem = navItems.find((item) => item.id === activeItemId) ?? navItems[0];
  const countsByProject = useMemo(() => projectNameMap(projects), [projects]);

  async function handleCreateEntry(payload: CreateEntryInput): Promise<void> {
    await api.createEntry(payload);
    const updated = await api.listEntries();
    setEntries(updated.items);
  }

  async function handleCreateTask(payload: CreateTaskInput): Promise<void> {
    await api.createTask(payload);
    const updated = await api.listTasks();
    setTasks(updated.items);
  }

  async function handlePatchTask(taskId: string, payload: UpdateTaskInput): Promise<void> {
    const updatedTask = await api.patchTask(taskId, payload);
    setTasks((current) => current.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
  }

  async function handleCompleteTask(taskId: string): Promise<void> {
    const updatedTask = await api.completeTask(taskId);
    setTasks((current) => current.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
  }

  async function handleReopenTask(taskId: string): Promise<void> {
    const updatedTask = await api.reopenTask(taskId);
    setTasks((current) => current.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
  }

  async function handleCreateProject(payload: CreateProjectInput): Promise<void> {
    const project = await api.createProject(payload);
    setProjects((current) => [...current, project].sort((a, b) => a.name.localeCompare(b.name)));
  }

  async function handleSaveSettings(payload: Partial<Settings>): Promise<void> {
    const updated = await api.patchSettings(payload);
    setSettings(updated);
  }

  function renderScreen(): JSX.Element {
    if (isLoading) {
      return (
        <section className="workspace">
          <section className="surface-panel">
            <p className="empty-state">Loading workspace…</p>
          </section>
        </section>
      );
    }

    switch (activeItemId) {
      case "capture":
        return (
          <CaptureScreen
            entries={entries}
            projects={projects}
            onCreateEntry={handleCreateEntry}
            onCreateTask={handleCreateTask}
          />
        );
      case "projects":
        return <ProjectsScreen projects={projects} tasks={tasks} onCreateProject={handleCreateProject} />;
      case "settings":
        return <SettingsScreen settings={settings} onSave={handleSaveSettings} />;
      case "inbox":
      case "today":
      case "this-week":
      case "completed":
        return (
          <TaskScreen
            title={taskScreenCopy[activeItemId].title}
            subtitle={taskScreenCopy[activeItemId].subtitle}
            tasks={visibleTasks.map((task) => ({ ...task, project_name: task.project_name ?? countsByProject[task.project_id ?? ""] ?? null }))}
            projects={projects}
            filters={filters}
            onFiltersChange={setFilters}
            onStatusChange={(taskId, status) => handlePatchTask(taskId, { status })}
            onComplete={handleCompleteTask}
            onReopen={handleReopenTask}
            onProjectChange={(taskId, projectId) => handlePatchTask(taskId, { project_id: projectId || null })}
            onDueDateChange={(taskId, dueDate) => handlePatchTask(taskId, { due_date: dueDate })}
          />
        );
      default:
        return (
          <section className="workspace">
            <section className="surface-panel">
              <p className="empty-state">This section is not part of Phase 1A.</p>
            </section>
          </section>
        );
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary">
        <div className="sidebar__brand">
          <p className="sidebar__eyebrow">Task Garden</p>
          <h1>Local-first desk</h1>
          <p className="sidebar__copy">Capture quickly, keep control, and manage work without AI dependencies.</p>
        </div>

        <nav className="sidebar__nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item${item.id === activeItemId ? " nav-item--active" : ""}`}
              onClick={() => setActiveItemId(item.id as NavScreen)}
              type="button"
            >
              <span className="nav-item__label">{item.label}</span>
              <span className="nav-item__description">{item.description}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar__footer">
          <div className="status-pill">{settings?.local_only_mode ? "Local-only active" : "Cloud optional"}</div>
        </div>
      </aside>

      <main className="content">
        <header className="content__header">
          <div>
            <p className="content__eyebrow">Workspace</p>
            <h2>{activeItem.label}</h2>
          </div>
          <button className="secondary-button" type="button" onClick={() => void loadAll()}>
            Refresh
          </button>
        </header>

        {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
        {renderScreen()}
      </main>
    </div>
  );
}
