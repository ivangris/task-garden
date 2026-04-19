import { useEffect, useState, type FormEvent } from "react";

import type { Settings } from "../../lib/types";

type SettingsScreenProps = {
  settings: Settings | null;
  onSave: (payload: Partial<Settings>) => Promise<void>;
};

export function SettingsScreen({ settings, onSave }: SettingsScreenProps): JSX.Element {
  const [draft, setDraft] = useState<Settings | null>(settings);

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  if (!settings || !draft) {
    return (
      <section className="workspace">
        <section className="surface-panel">
          <p className="empty-state">Loading settings…</p>
        </section>
      </section>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!draft) {
      return;
    }
    await onSave(draft);
  }

  return (
    <section className="workspace">
      <div className="hero-card hero-card--compact">
        <div>
          <p className="section-eyebrow">Settings</p>
          <h3>Keep local-first defaults visible and editable.</h3>
        </div>
      </div>

      <form className="surface-panel" onSubmit={handleSubmit}>
        <div className="form-grid">
          <label className="toggle-field">
            <span>Local-only mode</span>
            <input
              type="checkbox"
              checked={draft.local_only_mode}
              onChange={(event) => setDraft({ ...draft, local_only_mode: event.target.checked })}
            />
          </label>

          <label className="toggle-field">
            <span>Cloud enabled</span>
            <input
              type="checkbox"
              checked={draft.cloud_enabled}
              onChange={(event) => setDraft({ ...draft, cloud_enabled: event.target.checked })}
            />
          </label>

          <label className="field">
            <span>STT provider</span>
            <input value={draft.stt_provider} onChange={(event) => setDraft({ ...draft, stt_provider: event.target.value })} />
          </label>

          <label className="field">
            <span>Extraction provider</span>
            <input
              value={draft.task_extraction_provider}
              onChange={(event) => setDraft({ ...draft, task_extraction_provider: event.target.value })}
            />
          </label>

          <label className="field">
            <span>Sync provider</span>
            <input value={draft.sync_provider} onChange={(event) => setDraft({ ...draft, sync_provider: event.target.value })} />
          </label>

          <label className="field">
            <span>Auth provider</span>
            <input value={draft.auth_provider} onChange={(event) => setDraft({ ...draft, auth_provider: event.target.value })} />
          </label>

          <label className="field">
            <span>STT model</span>
            <input value={draft.stt_model} onChange={(event) => setDraft({ ...draft, stt_model: event.target.value })} />
          </label>

          <label className="field">
            <span>Extraction model</span>
            <input
              value={draft.extraction_model}
              onChange={(event) => setDraft({ ...draft, extraction_model: event.target.value })}
            />
          </label>

          <label className="field field--full">
            <span>Sync base URL</span>
            <input
              value={draft.sync_base_url ?? ""}
              onChange={(event) => setDraft({ ...draft, sync_base_url: event.target.value || null })}
            />
          </label>
        </div>

        <div className="form-actions">
          <span className="helper-text">Cloud-facing options remain optional and disabled by default.</span>
          <button className="primary-button" type="submit">
            Save Settings
          </button>
        </div>
      </form>
    </section>
  );
}
