import { formatDate, toApiDate, toDateInputValue, type TaskFilters } from "../../features/tasks/task-utils";
import type { CurrentRecommendations, Project, Task, TaskStatus, WeeklyPreview } from "../../lib/types";

type TaskScreenProps = {
  title: string;
  subtitle: string;
  tasks: Task[];
  projects: Project[];
  recommendations: CurrentRecommendations | null;
  weeklyPreview: WeeklyPreview | null;
  filters: TaskFilters;
  onFiltersChange: (filters: TaskFilters) => void;
  onStatusChange: (taskId: string, status: TaskStatus) => Promise<void>;
  onComplete: (taskId: string) => Promise<void>;
  onReopen: (taskId: string) => Promise<void>;
  onProjectChange: (taskId: string, projectId: string) => Promise<void>;
  onDueDateChange: (taskId: string, dueDate: string | null) => Promise<void>;
};

const statusOptions: TaskStatus[] = ["inbox", "planned", "in_progress", "blocked", "completed", "archived"];

export function TaskScreen({
  title,
  subtitle,
  tasks,
  projects,
  recommendations,
  weeklyPreview,
  filters,
  onFiltersChange,
  onStatusChange,
  onComplete,
  onReopen,
  onProjectChange,
  onDueDateChange,
}: TaskScreenProps): JSX.Element {
  return (
    <section className="workspace">
      <div className="hero-card hero-card--compact">
        <div>
          <p className="section-eyebrow">{title}</p>
          <h3>{subtitle}</h3>
        </div>
        <div className="hero-card__stats">
          <span className="stat-pill">{tasks.length} visible</span>
        </div>
      </div>

      {recommendations && recommendations.items.length > 0 ? (
        <section className="planning-strip">
          {weeklyPreview ? (
            <article className="surface-panel planning-card planning-card--wide">
              <div className="surface-panel__header">
                <div>
                  <p className="section-eyebrow">Weekly Preview</p>
                  <h4>Top focus for the next seven days</h4>
                </div>
                <span className="meta-chip">{weeklyPreview.top_focus_items.length} focus items</span>
              </div>

              <div className="planning-focus-list">
                {weeklyPreview.top_focus_items.map((task) => (
                  <div key={task.id} className="planning-focus-item">
                    <strong>{task.title}</strong>
                    <span>
                      {task.project_name ?? "No project"} · due {formatDate(task.due_date)}
                    </span>
                  </div>
                ))}
              </div>

              {weeklyPreview.suggestion_summaries.length > 0 ? (
                <div className="chip-row">
                  {weeklyPreview.suggestion_summaries.map((summary) => (
                    <span key={summary} className="meta-chip">
                      {summary}
                    </span>
                  ))}
                </div>
              ) : null}
            </article>
          ) : null}

          {recommendations.items.slice(0, weeklyPreview ? 2 : 3).map((item) => (
            <article key={item.id} className={`surface-panel planning-card planning-card--${item.level}`}>
              <div className="planning-card__meta">
                <span className="section-eyebrow">{item.rule_type.replace(/_/g, " ")}</span>
                <span className="meta-chip">{item.level}</span>
              </div>
              <h4>{item.title}</h4>
              <p className="muted-copy">{item.rationale}</p>
              <div className="chip-row">
                {item.reasons.map((reason) => (
                  <span key={`${item.id}-${reason.label}`} className="meta-chip">
                    {reason.label}: {reason.value}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </section>
      ) : null}

      <section className="surface-panel">
        <div className="surface-panel__header surface-panel__header--stack">
          <div>
            <p className="section-eyebrow">Filters</p>
            <h4>Keep the list tight</h4>
          </div>
          <div className="filter-row">
            <label className="field field--inline">
              <span>Status</span>
              <select
                value={filters.status}
                onChange={(event) => onFiltersChange({ ...filters, status: event.target.value })}
              >
                <option value="all">All</option>
                {statusOptions.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>
            </label>

            <label className="field field--inline">
              <span>Project</span>
              <select
                value={filters.projectId}
                onChange={(event) => onFiltersChange({ ...filters, projectId: event.target.value })}
              >
                <option value="all">All projects</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>

        <div className="task-table">
          <div className="task-table__head">
            <span>Task</span>
            <span>Status</span>
            <span>Project</span>
            <span>Dates</span>
            <span>Actions</span>
          </div>

          {tasks.length === 0 ? <p className="empty-state">No tasks match this view yet.</p> : null}

          {tasks.map((task) => (
            <article key={task.id} className="task-row">
              <div className="task-row__main">
                <strong>{task.title}</strong>
                {task.details ? <p>{task.details}</p> : null}
                <div className="chip-row">
                  <span className="meta-chip">priority {task.priority}</span>
                  <span className="meta-chip">effort {task.effort}</span>
                  <span className="meta-chip">energy {task.energy}</span>
                </div>
              </div>

              <label className="field field--inline">
                <span className="sr-only">Status</span>
                <select value={task.status} onChange={(event) => onStatusChange(task.id, event.target.value as TaskStatus)}>
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </label>

              <div className="task-row__project">
                <label className="field field--inline">
                  <span className="sr-only">Project</span>
                  <select value={task.project_id ?? ""} onChange={(event) => onProjectChange(task.id, event.target.value)}>
                    <option value="">No project</option>
                    {projects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="task-row__dates">
                <span>Created {formatDate(task.created_at)}</span>
                <label className="field field--inline">
                  <span className="sr-only">Due date</span>
                  <input
                    type="date"
                    value={toDateInputValue(task.due_date)}
                    onChange={(event) => onDueDateChange(task.id, event.target.value ? toApiDate(event.target.value) ?? null : null)}
                  />
                </label>
              </div>

              <div className="task-row__actions">
                {task.status === "completed" ? (
                  <button className="secondary-button" type="button" onClick={() => onReopen(task.id)}>
                    Reopen
                  </button>
                ) : (
                  <button className="primary-button primary-button--small" type="button" onClick={() => onComplete(task.id)}>
                    Complete
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
