import { useEffect, useMemo, useState } from "react";

import { CaptureScreen } from "../screens/CaptureScreen";
import { GardenScreen } from "../screens/GardenScreen";
import { ProjectsScreen } from "../screens/ProjectsScreen";
import { RecapsScreen } from "../screens/RecapsScreen";
import { SettingsScreen } from "../screens/SettingsScreen";
import { TaskScreen } from "../screens/TaskScreen";
import { navItems } from "../../features/navigation/nav-items";
import { api } from "../../lib/api";
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
  NavScreen,
  ProviderCheckResult,
  Project,
  RawEntry,
  RecapPeriod,
  RecapPeriodType,
  Settings,
  SyncStatus,
  Task,
  TaskStatus,
  TranscriptionResult,
  UpdateTaskInput,
  WeeklyPreview,
} from "../../lib/types";
import { applyTaskFilters, projectNameMap, tasksForScreen, type TaskFilters } from "../../features/tasks/task-utils";

const DEVICE_STORAGE_KEY = "task-garden-device-id";

function shellToneForStage(stageKey: string | undefined): "desert" | "recovering" | "healthy" | "lush" {
  if (stageKey === "lush_oasis") {
    return "lush";
  }
  if (stageKey === "healthy_garden") {
    return "healthy";
  }
  if (stageKey === "recovering_plot") {
    return "recovering";
  }
  return "desert";
}

const taskScreenCopy: Record<Exclude<NavScreen, "capture" | "projects" | "garden" | "recaps" | "settings">, { title: string; subtitle: string }> = {
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
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [providerChecks, setProviderChecks] = useState<Partial<Record<"task_extraction" | "recap_narrative" | "stt", ProviderCheckResult>>>({});
  const [localModels, setLocalModels] = useState<LocalModelsResult | null>(null);
  const [gardenOverview, setGardenOverview] = useState<GardenOverview | null>(null);
  const [gardenTiles, setGardenTiles] = useState<GardenTilesPayload | null>(null);
  const [currentRecommendations, setCurrentRecommendations] = useState<CurrentRecommendations | null>(null);
  const [weeklyPreview, setWeeklyPreview] = useState<WeeklyPreview | null>(null);
  const [recaps, setRecaps] = useState<Partial<Record<RecapPeriodType, RecapPeriod>>>({});
  const [activeExtraction, setActiveExtraction] = useState<ExtractionBatch | null>(null);
  const [latestTranscription, setLatestTranscription] = useState<TranscriptionResult | null>(null);
  const [extractionNotice, setExtractionNotice] = useState<string | null>(null);
  const [filters, setFilters] = useState<TaskFilters>({ status: "all", projectId: "all" });
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingRecaps, setIsLoadingRecaps] = useState(false);
  const [isGeneratingNarrative, setIsGeneratingNarrative] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const storedDeviceId = window.localStorage.getItem(DEVICE_STORAGE_KEY);
    api.setDeviceId(storedDeviceId);
  }, []);

  async function loadAll(): Promise<void> {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const storedDeviceId = window.localStorage.getItem(DEVICE_STORAGE_KEY) ?? undefined;
      const [entryData, taskData, projectData, settingsData, syncStatusData, modelData, recommendationData, weeklyPreviewData, gardenStateData, gardenTilesData] = await Promise.all([
        api.listEntries(),
        api.listTasks(),
        api.listProjects(),
        api.getSettings(),
        api.getSyncStatus(storedDeviceId),
        api.listLocalModels(),
        api.getCurrentRecommendations(),
        api.createWeeklyPreview(),
        api.getGardenState(),
        api.getGardenTiles(),
      ]);
      setEntries(entryData.items);
      setTasks(taskData.items);
      setProjects(projectData.items);
      setSettings(settingsData);
      setSyncStatus(syncStatusData);
      setLocalModels(modelData);
      setCurrentRecommendations(recommendationData);
      setWeeklyPreview(weeklyPreviewData);
      setGardenOverview(gardenStateData);
      setGardenTiles(gardenTilesData);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to load Task Garden.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  useEffect(() => {
    if (activeItemId === "garden" && !isLoading) {
      void handleRecomputeGarden();
    }
  }, [activeItemId]);

  useEffect(() => {
    if (activeItemId === "recaps" && !isLoading && Object.keys(recaps).length === 0 && !isLoadingRecaps) {
      void handleGenerateAllRecaps();
    }
  }, [activeItemId, isLoading]);

  const visibleTasks = useMemo(() => {
    const scoped = tasksForScreen(activeItemId, tasks);
    return applyTaskFilters(scoped, filters);
  }, [activeItemId, filters, tasks]);

  const activeItem = navItems.find((item) => item.id === activeItemId) ?? navItems[0];
  const countsByProject = useMemo(() => projectNameMap(projects), [projects]);
  const shellTone = shellToneForStage(gardenOverview?.state.stage_key);

  async function handleCreateEntry(payload: CreateEntryInput): Promise<void> {
    try {
      await api.createEntry(payload);
      const updated = await api.listEntries();
      setEntries(updated.items);
      setExtractionNotice("Saved. Extract whenever you're ready.");
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to save raw entry.");
      throw error;
    }
  }

  async function handleArchiveEntry(entryId: string): Promise<void> {
    const archived = await api.archiveEntry(entryId);
    setEntries((current) => current.filter((entry) => entry.id !== archived.id));
    setExtractionNotice("Note removed from Recent Notes.");
  }

  async function handleCreateAudioEntry(payload: CreateAudioEntryInput = {}): Promise<RawEntry> {
    const entry = await api.createAudioEntry(payload);
    const updated = await api.listEntries();
    setEntries(updated.items);
    return entry;
  }

  async function handleTranscribeAudio(audioBlob: Blob, fileName?: string): Promise<TranscriptionResult> {
    const shellEntry = await handleCreateAudioEntry();
    const result = await api.transcribeEntryAudio(shellEntry.id, audioBlob, fileName);
    const updatedEntries = await api.listEntries();
    setEntries(updatedEntries.items);
    setLatestTranscription(result);
    setExtractionNotice("Transcript saved. Extract from it whenever you're ready.");
    return result;
  }

  async function handleRunExtract(entryId: string): Promise<void> {
    try {
      const extraction = await api.extractEntry(entryId);
      setActiveExtraction(extraction);
      setExtractionNotice("Suggestions are ready to review.");
      const updatedEntries = await api.listEntries();
      setEntries(updatedEntries.items);
      setErrorMessage(null);
    } catch (error) {
      setActiveExtraction(null);
      setExtractionNotice(null);
      setErrorMessage(error instanceof Error ? error.message : "Extraction failed.");
      throw error;
    }
  }

  async function handleConfirmExtraction(extractionId: string, candidates: ConfirmExtractionCandidateInput[]): Promise<void> {
    try {
      const result = await api.confirmExtraction(extractionId, candidates);
      const [updatedTasks, updatedEntries, recommendationData, weeklyPreviewData, recomputedGarden, refreshedGardenTiles] = await Promise.all([
        api.listTasks(),
        api.listEntries(),
        api.getCurrentRecommendations(),
        api.createWeeklyPreview(),
        api.recomputeGarden(),
        api.getGardenTiles(),
      ]);
      setTasks(updatedTasks.items);
      setEntries(updatedEntries.items);
      setCurrentRecommendations(recommendationData);
      setWeeklyPreview(weeklyPreviewData);
      setGardenOverview(recomputedGarden);
      setGardenTiles(refreshedGardenTiles);
      setActiveExtraction((current) =>
        current && current.id === extractionId
          ? { ...current, needs_review: false, candidates: result.updated_candidates }
          : current,
      );
      setExtractionNotice(`${result.accepted_count} item${result.accepted_count === 1 ? "" : "s"} added to Inbox.`);
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to confirm extraction.");
      throw error;
    }
  }

  async function handleCreateTask(payload: CreateTaskInput): Promise<void> {
    await api.createTask(payload);
    const [updated, recommendationData, weeklyPreviewData, recomputedGarden, refreshedGardenTiles] = await Promise.all([
      api.listTasks(),
      api.getCurrentRecommendations(),
      api.createWeeklyPreview(),
      api.recomputeGarden(),
      api.getGardenTiles(),
    ]);
    setTasks(updated.items);
    setCurrentRecommendations(recommendationData);
    setWeeklyPreview(weeklyPreviewData);
    setGardenOverview(recomputedGarden);
    setGardenTiles(refreshedGardenTiles);
  }

  async function handlePatchTask(taskId: string, payload: UpdateTaskInput): Promise<void> {
    const [updatedTask, recommendationData, weeklyPreviewData, recomputedGarden, refreshedGardenTiles] = await Promise.all([
      api.patchTask(taskId, payload),
      api.getCurrentRecommendations(),
      api.createWeeklyPreview(),
      api.recomputeGarden(),
      api.getGardenTiles(),
    ]);
    setTasks((current) => current.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
    setCurrentRecommendations(recommendationData);
    setWeeklyPreview(weeklyPreviewData);
    setGardenOverview(recomputedGarden);
    setGardenTiles(refreshedGardenTiles);
  }

  async function handleCompleteTask(taskId: string): Promise<void> {
    const [updatedTask, recommendationData, weeklyPreviewData, recomputedGarden, refreshedGardenTiles] = await Promise.all([
      api.completeTask(taskId),
      api.getCurrentRecommendations(),
      api.createWeeklyPreview(),
      api.recomputeGarden(),
      api.getGardenTiles(),
    ]);
    setTasks((current) => current.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
    setCurrentRecommendations(recommendationData);
    setWeeklyPreview(weeklyPreviewData);
    setGardenOverview(recomputedGarden);
    setGardenTiles(refreshedGardenTiles);
  }

  async function handleReopenTask(taskId: string): Promise<void> {
    const [updatedTask, recommendationData, weeklyPreviewData, recomputedGarden, refreshedGardenTiles] = await Promise.all([
      api.reopenTask(taskId),
      api.getCurrentRecommendations(),
      api.createWeeklyPreview(),
      api.recomputeGarden(),
      api.getGardenTiles(),
    ]);
    setTasks((current) => current.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
    setCurrentRecommendations(recommendationData);
    setWeeklyPreview(weeklyPreviewData);
    setGardenOverview(recomputedGarden);
    setGardenTiles(refreshedGardenTiles);
  }

  async function handleCreateProject(payload: CreateProjectInput): Promise<void> {
    const project = await api.createProject(payload);
    setProjects((current) => [...current, project].sort((a, b) => a.name.localeCompare(b.name)));
    const [recommendationData, weeklyPreviewData] = await Promise.all([
      api.getCurrentRecommendations(),
      api.createWeeklyPreview(),
    ]);
    setCurrentRecommendations(recommendationData);
    setWeeklyPreview(weeklyPreviewData);
  }

  async function handleSaveSettings(payload: Partial<Settings>): Promise<void> {
    const updated = await api.patchSettings(payload);
    setSettings(updated);
    const storedDeviceId = window.localStorage.getItem(DEVICE_STORAGE_KEY) ?? undefined;
    setSyncStatus(await api.getSyncStatus(storedDeviceId));
  }

  async function handleCheckProvider(kind: "task_extraction" | "recap_narrative" | "stt"): Promise<void> {
    const result = await api.checkProvider(kind);
    setProviderChecks((current) => ({ ...current, [kind]: result }));
  }

  async function handleRefreshLocalModels(): Promise<void> {
    setLocalModels(await api.listLocalModels());
  }

  async function handleRegisterDevice(): Promise<void> {
    const existingDeviceId = window.localStorage.getItem(DEVICE_STORAGE_KEY) ?? undefined;
    const device = await api.registerDevice({
      device_id: existingDeviceId,
      device_name: window.navigator.platform.includes("Win") ? "Windows Desk" : "Task Garden Device",
      platform: window.navigator.platform || "desktop",
      app_version: "0.1.0",
    });
    window.localStorage.setItem(DEVICE_STORAGE_KEY, device.id);
    api.setDeviceId(device.id);
    setSyncStatus(await api.getSyncStatus(device.id));
  }

  async function handleRecomputeGarden(): Promise<void> {
    const [overview, tilesPayload] = await Promise.all([api.recomputeGarden(), api.getGardenTiles()]);
    setGardenOverview(overview);
    setGardenTiles(tilesPayload);
  }

  async function handleGenerateRecap(periodType: RecapPeriodType): Promise<void> {
    setIsLoadingRecaps(true);
    try {
      const generated =
        periodType === "weekly"
          ? await api.generateWeeklyRecap()
          : periodType === "monthly"
            ? await api.generateMonthlyRecap()
            : await api.generateYearlyRecap();
      const recap = await api.getRecap(generated.id);
      setRecaps((current) => ({ ...current, [periodType]: recap }));
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to generate recap.");
      throw error;
    } finally {
      setIsLoadingRecaps(false);
    }
  }

  async function handleGenerateAllRecaps(): Promise<void> {
    setIsLoadingRecaps(true);
    try {
      const [generatedWeekly, generatedMonthly, generatedYearly] = await Promise.all([
        api.generateWeeklyRecap(),
        api.generateMonthlyRecap(),
        api.generateYearlyRecap(),
      ]);
      const [weekly, monthly, yearly] = await Promise.all([
        api.getRecap(generatedWeekly.id),
        api.getRecap(generatedMonthly.id),
        api.getRecap(generatedYearly.id),
      ]);
      setRecaps({ weekly, monthly, yearly });
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to generate recaps.");
    } finally {
      setIsLoadingRecaps(false);
    }
  }

  async function handleGenerateNarrative(periodType: RecapPeriodType): Promise<void> {
    let recap = recaps[periodType];
    if (!recap) {
      const generated =
        periodType === "weekly"
          ? await api.generateWeeklyRecap()
          : periodType === "monthly"
            ? await api.generateMonthlyRecap()
            : await api.generateYearlyRecap();
      recap = await api.getRecap(generated.id);
      setRecaps((current) => ({ ...current, [periodType]: recap }));
    }

    setIsGeneratingNarrative(true);
    try {
      const narrative = await api.generateRecapNarrative(recap.id);
      setRecaps((current) => ({
        ...current,
        [periodType]: current[periodType]
          ? {
              ...current[periodType],
              narrative,
            }
          : current[periodType],
      }));
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unable to generate recap narrative.");
      throw error;
    } finally {
      setIsGeneratingNarrative(false);
    }
  }

  function renderScreen(): JSX.Element {
    if (isLoading) {
      return (
        <section className="workspace">
          <section className="surface-panel">
            <p className="empty-state">Loading workspace...</p>
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
            activeExtraction={activeExtraction}
            latestTranscription={latestTranscription}
            extractionNotice={extractionNotice}
            onCreateEntry={handleCreateEntry}
            onTranscribeAudio={handleTranscribeAudio}
            onCreateTask={handleCreateTask}
            onRunExtract={handleRunExtract}
            onConfirmExtraction={handleConfirmExtraction}
            onArchiveEntry={handleArchiveEntry}
          />
        );
      case "projects":
        return <ProjectsScreen projects={projects} tasks={tasks} onCreateProject={handleCreateProject} />;
      case "garden":
        return <GardenScreen overview={gardenOverview} tilesPayload={gardenTiles} onRecompute={handleRecomputeGarden} />;
      case "recaps":
        return (
          <RecapsScreen
            recaps={recaps}
            isLoading={isLoadingRecaps}
            isGeneratingNarrative={isGeneratingNarrative}
            onGenerate={handleGenerateRecap}
            onGenerateNarrative={handleGenerateNarrative}
          />
        );
      case "settings":
        return (
          <SettingsScreen
            settings={settings}
            syncStatus={syncStatus}
            providerChecks={providerChecks}
            localModels={localModels}
            onSave={handleSaveSettings}
            onRegisterDevice={handleRegisterDevice}
            onCheckProvider={handleCheckProvider}
            onRefreshLocalModels={handleRefreshLocalModels}
          />
        );
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
            recommendations={activeItemId === "today" || activeItemId === "this-week" ? currentRecommendations : null}
            weeklyPreview={activeItemId === "this-week" ? weeklyPreview : null}
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
    <div className={`app-shell app-shell--${shellTone}`}>
      <aside className="sidebar" aria-label="Primary">
        <div className="sidebar__brand">
          <p className="sidebar__eyebrow">Task Garden</p>
          <h1>Calm capture, visible follow-through.</h1>
          <p className="sidebar__copy">A local-first planning desk with a restorative layer, not a noisy pipeline.</p>
        </div>

        <nav className="sidebar__nav">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item${item.id === activeItemId ? " nav-item--active" : ""}`}
              onClick={() => setActiveItemId(item.id as NavScreen)}
              type="button"
            >
              <span className="nav-item__label-row">
                <span className="nav-item__icon" aria-hidden="true">{item.icon}</span>
                <span className="nav-item__label">{item.label}</span>
              </span>
              <span className="nav-item__description">{item.description}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar__footer">
          <div className="status-pill">{settings?.local_only_mode ? "Local-first" : "Hybrid mode"}</div>
        </div>
      </aside>

      <main className="content">
        <header className="content__header">
          <div>
            <p className="content__eyebrow">Workspace</p>
            <h2>{activeItem.label}</h2>
          </div>
          <button className="secondary-button secondary-button--ghost" type="button" onClick={() => void loadAll()}>
            Refresh
          </button>
        </header>

        {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
        {renderScreen()}
      </main>
    </div>
  );
}
