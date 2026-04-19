import { useState, type FormEvent } from "react";

import type { CreateProjectInput, Project, Task } from "../../lib/types";

type ProjectsScreenProps = {
  projects: Project[];
  tasks: Task[];
  onCreateProject: (payload: CreateProjectInput) => Promise<void>;
};

export function ProjectsScreen({ projects, tasks, onCreateProject }: ProjectsScreenProps): JSX.Element {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    await onCreateProject({ name, description });
    setName("");
    setDescription("");
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
                  <div>
                    <strong>{project.name}</strong>
                    {project.description ? <p>{project.description}</p> : <p className="muted-copy">No description yet.</p>}
                  </div>
                  <span className="meta-chip">{taskCount} active</span>
                </article>
              );
            })}
          </div>
        </section>
      </div>
    </section>
  );
}
