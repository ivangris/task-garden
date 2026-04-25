import { useState, type FormEvent } from "react";

import type { CreateProjectInput, DeleteProjectMode, Project, Task, UpdateProjectInput } from "../../lib/types";

type ProjectsScreenProps = {
  projects: Project[];
  tasks: Task[];
  onCreateProject: (payload: CreateProjectInput) => Promise<void>;
  onUpdateProject: (projectId: string, payload: UpdateProjectInput) => Promise<void>;
  onDeleteProject: (projectId: string, taskMode: DeleteProjectMode) => Promise<void>;
};

export function ProjectsScreen({ projects, tasks, onCreateProject, onUpdateProject, onDeleteProject }: ProjectsScreenProps): JSX.Element {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [deleteProjectId, setDeleteProjectId] = useState<string | null>(null);
  const [deleteMode, setDeleteMode] = useState<DeleteProjectMode>("unassign");

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await onCreateProject({ name, description });
    setName("");
    setDescription("");
  }

  function startEditing(project: Project): void {
    setEditingProjectId(project.id);
    setEditName(project.name);
    setEditDescription(project.description ?? "");
  }

  async function handleUpdateProject(event: FormEvent<HTMLFormElement>, projectId: string): Promise<void> {
    event.preventDefault();
    await onUpdateProject(projectId, { name: editName, description: editDescription });
    setEditingProjectId(null);
    setEditName("");
    setEditDescription("");
  }

  async function handleDeleteProject(project: Project): Promise<void> {
    if (deleteMode === "delete") {
      const confirmed = window.confirm(`Delete "${project.name}" and its associated tasks? This cannot be undone.`);
      if (!confirmed) {
        return;
      }
    }
    await onDeleteProject(project.id, deleteMode);
    setDeleteProjectId(null);
    setDeleteMode("unassign");
  }

  return (
    <section className="workspace">
      <div className="hero-card hero-card--compact">
        <div>
          <p className="section-eyebrow">Projects</p>
          <h3>Group work without adding clutter.</h3>
        </div>
      </div>

      <div className="screen-grid">
        <form className="surface-panel" onSubmit={handleSubmit}>
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Create Project</p>
              <h4>Lightweight grouping</h4>
            </div>
          </div>

          <div className="form-grid">
            <label className="field">
              <span>Name</span>
              <input value={name} onChange={(event) => setName(event.target.value)} required />
            </label>

            <label className="field field--full">
              <span>Description</span>
              <textarea
                className="text-area text-area--compact"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={4}
              />
            </label>
          </div>

          <div className="form-actions">
            <span className="helper-text">Projects stay optional so capture never slows down.</span>
            <button className="primary-button" type="submit">
              Save Project
            </button>
          </div>
        </form>

        <section className="surface-panel">
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Project List</p>
              <h4>Current groups</h4>
            </div>
          </div>

          <div className="project-list">
            {projects.length === 0 ? <p className="empty-state">No projects yet.</p> : null}
            {projects.map((project) => {
              const taskCount = tasks.filter((task) => task.project_id === project.id && task.status !== "completed").length;
              return (
                <article key={project.id} className="project-card">
                  {editingProjectId === project.id ? (
                    <form className="project-edit-form" onSubmit={(event) => void handleUpdateProject(event, project.id)}>
                      <label className="field field--full">
                        <span>Name</span>
                        <input value={editName} onChange={(event) => setEditName(event.target.value)} required />
                      </label>
                      <label className="field field--full">
                        <span>Description</span>
                        <textarea
                          className="text-area text-area--compact"
                          value={editDescription}
                          onChange={(event) => setEditDescription(event.target.value)}
                          rows={3}
                        />
                      </label>
                      <div className="form-actions">
                        <button className="secondary-button secondary-button--ghost" type="button" onClick={() => setEditingProjectId(null)}>
                          Cancel
                        </button>
                        <button className="primary-button primary-button--small" type="submit">
                          Save
                        </button>
                      </div>
                    </form>
                  ) : (
                    <>
                      <div>
                        <strong>{project.name}</strong>
                        {project.description ? <p>{project.description}</p> : <p className="muted-copy">No description yet.</p>}
                      </div>
                      <div className="project-card__actions">
                        <span className="meta-chip">{taskCount} active</span>
                        <button className="secondary-button secondary-button--ghost" type="button" onClick={() => startEditing(project)}>
                          Edit
                        </button>
                        <button className="secondary-button secondary-button--ghost" type="button" onClick={() => setDeleteProjectId(project.id)}>
                          Delete
                        </button>
                      </div>
                    </>
                  )}

                  {deleteProjectId === project.id ? (
                    <div className="project-delete-panel">
                      <label className="field">
                        <span>Delete option</span>
                        <select value={deleteMode} onChange={(event) => setDeleteMode(event.target.value as DeleteProjectMode)}>
                          <option value="unassign">Delete project, keep tasks</option>
                          <option value="delete">Delete project and tasks</option>
                        </select>
                      </label>
                      <div className="form-actions">
                        <button className="secondary-button secondary-button--ghost" type="button" onClick={() => setDeleteProjectId(null)}>
                          Cancel
                        </button>
                        <button className={deleteMode === "delete" ? "danger-button" : "secondary-button"} type="button" onClick={() => void handleDeleteProject(project)}>
                          {deleteMode === "delete" ? "Delete tasks too" : "Delete project"}
                        </button>
                      </div>
                    </div>
                  ) : null}
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </section>
  );
}
