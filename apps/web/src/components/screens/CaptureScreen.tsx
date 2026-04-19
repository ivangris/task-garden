import { useState, type FormEvent } from "react";

import { formatDate, toApiDate } from "../../features/tasks/task-utils";
import type { CreateEntryInput, CreateTaskInput, Project, RawEntry, TaskEffort, TaskEnergy, TaskPriority, TaskStatus } from "../../lib/types";

type CaptureScreenProps = {
  entries: RawEntry[];
  projects: Project[];
  onCreateEntry: (payload: CreateEntryInput) => Promise<void>;
  onCreateTask: (payload: CreateTaskInput) => Promise<void>;
};

const priorityOptions: TaskPriority[] = ["low", "medium", "high", "critical"];
const effortOptions: TaskEffort[] = ["small", "medium", "large"];
const energyOptions: TaskEnergy[] = ["low", "medium", "high"];
const statusOptions: TaskStatus[] = ["inbox", "planned", "in_progress", "blocked"];

export function CaptureScreen({ entries, projects, onCreateEntry, onCreateTask }: CaptureScreenProps): JSX.Element {
  const [rawText, setRawText] = useState("");
  const [sourceType, setSourceType] = useState<"typed" | "pasted">("typed");
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDetails, setTaskDetails] = useState("");
  const [taskProjectId, setTaskProjectId] = useState("");
  const [taskDueDate, setTaskDueDate] = useState("");
  const [taskStatus, setTaskStatus] = useState<TaskStatus>("inbox");
  const [taskPriority, setTaskPriority] = useState<TaskPriority>("medium");
  const [taskEffort, setTaskEffort] = useState<TaskEffort>("medium");
  const [taskEnergy, setTaskEnergy] = useState<TaskEnergy>("medium");

  async function handleSaveEntry(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await onCreateEntry({ source_type: sourceType, raw_text: rawText });
    setRawText("");
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await onCreateTask({
      title: taskTitle,
      details: taskDetails || undefined,
      project_id: taskProjectId || undefined,
      due_date: toApiDate(taskDueDate),
      status: taskStatus,
      priority: taskPriority,
      effort: taskEffort,
      energy: taskEnergy,
    });
    setTaskTitle("");
    setTaskDetails("");
    setTaskProjectId("");
    setTaskDueDate("");
    setTaskStatus("inbox");
    setTaskPriority("medium");
    setTaskEffort("medium");
    setTaskEnergy("medium");
  }

  return (
    <section className="workspace">
      <div className="hero-card">
        <div>
          <p className="section-eyebrow">Capture</p>
          <h3>Dump the thought, keep the structure under your control.</h3>
        </div>
        <p className="muted-copy">Nothing here behaves like chat. Raw notes and manual tasks stay explicit and editable.</p>
      </div>

      <div className="screen-grid screen-grid--capture">
        <form className="surface-panel" onSubmit={handleSaveEntry}>
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Raw Entry</p>
              <h4>Typed or pasted note</h4>
            </div>
            <select value={sourceType} onChange={(event) => setSourceType(event.target.value as "typed" | "pasted")}>
              <option value="typed">Typed</option>
              <option value="pasted">Pasted</option>
            </select>
          </div>

          <textarea
            className="text-area"
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
            placeholder="Write out the thought in plain language. Raw input is preserved exactly as entered."
            rows={9}
            required
          />

          <div className="form-actions">
            <span className="helper-text">Saved raw entries stay available even before extraction exists.</span>
            <button className="primary-button" type="submit">
              Save Raw Entry
            </button>
          </div>
        </form>

        <form className="surface-panel" onSubmit={handleCreateTask}>
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Manual Task</p>
              <h4>Create work without AI</h4>
            </div>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>Title</span>
              <input value={taskTitle} onChange={(event) => setTaskTitle(event.target.value)} required />
            </label>

            <label className="field field--full">
              <span>Details</span>
              <textarea
                className="text-area text-area--compact"
                value={taskDetails}
                onChange={(event) => setTaskDetails(event.target.value)}
                rows={4}
                placeholder="Optional notes, next step, or context."
              />
            </label>

            <label className="field">
              <span>Project</span>
              <select value={taskProjectId} onChange={(event) => setTaskProjectId(event.target.value)}>
                <option value="">No project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Due date</span>
              <input type="date" value={taskDueDate} onChange={(event) => setTaskDueDate(event.target.value)} />
            </label>

            <label className="field">
              <span>Status</span>
              <select value={taskStatus} onChange={(event) => setTaskStatus(event.target.value as TaskStatus)}>
                {statusOptions.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Priority</span>
              <select value={taskPriority} onChange={(event) => setTaskPriority(event.target.value as TaskPriority)}>
                {priorityOptions.map((priority) => (
                  <option key={priority} value={priority}>
                    {priority}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Effort</span>
              <select value={taskEffort} onChange={(event) => setTaskEffort(event.target.value as TaskEffort)}>
                {effortOptions.map((effort) => (
                  <option key={effort} value={effort}>
                    {effort}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Energy</span>
              <select value={taskEnergy} onChange={(event) => setTaskEnergy(event.target.value as TaskEnergy)}>
                {energyOptions.map((energy) => (
                  <option key={energy} value={energy}>
                    {energy}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="form-actions">
            <span className="helper-text">Manual creation is the first-class path until extraction is wired.</span>
            <button className="primary-button" type="submit">
              Create Task
            </button>
          </div>
        </form>
      </div>

      <section className="surface-panel">
        <div className="surface-panel__header">
          <div>
            <p className="section-eyebrow">Recent Raw Entries</p>
            <h4>Preserved source material</h4>
          </div>
        </div>

        <div className="entry-list">
          {entries.length === 0 ? <p className="empty-state">No raw entries yet.</p> : null}
          {entries.map((entry) => (
            <article key={entry.id} className="entry-card">
              <div className="entry-card__meta">
                <span className="meta-chip">{entry.source_type}</span>
                <span className="meta-chip">{entry.entry_status}</span>
                <span>{formatDate(entry.created_at)}</span>
              </div>
              <p>{entry.raw_text}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
