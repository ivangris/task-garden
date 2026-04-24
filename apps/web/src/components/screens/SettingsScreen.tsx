import { useEffect, useState, type FormEvent } from "react";

import type { LocalModelsResult, ProviderCheckResult, Settings, SyncStatus } from "../../lib/types";

type SettingsScreenProps = {
  settings: Settings | null;
  syncStatus: SyncStatus | null;
  providerChecks: Partial<Record<"task_extraction" | "recap_narrative" | "stt", ProviderCheckResult>>;
  localModels: LocalModelsResult | null;
  onSave: (payload: Partial<Settings>) => Promise<void>;
  onRegisterDevice: () => Promise<void>;
  onCheckProvider: (kind: "task_extraction" | "recap_narrative" | "stt") => Promise<void>;
  onRefreshLocalModels: () => Promise<void>;
};

function providerCheckLabel(result: ProviderCheckResult | undefined): string {
  if (!result) {
    return "Not checked yet";
  }
  return result.ok ? "Ready" : "Needs attention";
}

export function SettingsScreen({
  settings,
  syncStatus,
  providerChecks,
  localModels,
  onSave,
  onRegisterDevice,
  onCheckProvider,
  onRefreshLocalModels,
}: SettingsScreenProps): JSX.Element {
  const [draft, setDraft] = useState<Settings | null>(settings);

  useEffect(() => {
    setDraft(settings);
  }, [settings]);

  if (!settings || !draft) {
    return (
      <section className="workspace">
        <section className="surface-panel surface-panel--empty-state">
          <p className="section-eyebrow">Settings</p>
          <h4>Loading your local setup.</h4>
          <p className="empty-state">Provider choices, device registration, and local defaults are on the way.</p>
        </section>
      </section>
    );
  }

  const chatModels = localModels?.models.filter((model) => model.usable_for_chat) ?? [];

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
          <h3>Local by default, with cleaner diagnostics when you need them.</h3>
        </div>
      </div>

      <form className="surface-panel" onSubmit={handleSubmit}>
        <div className="settings-stack">
          <section className="settings-section">
            <div className="surface-panel__header surface-panel__header--stack">
              <div>
                <p className="section-eyebrow">App Mode</p>
                <h4>Core defaults</h4>
              </div>
            </div>
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
            </div>
          </section>

          <section className="settings-section">
            <div className="surface-panel__header surface-panel__header--stack">
              <div>
                <p className="section-eyebrow">Providers</p>
                <h4>Local model setup</h4>
              </div>
              <button className="secondary-button secondary-button--ghost" type="button" onClick={() => void onRefreshLocalModels()}>
                Refresh models
              </button>
            </div>
            <div className="form-grid">
              <label className="field">
                <span>Extraction provider</span>
                <select
                  value={draft.task_extraction_provider}
                  onChange={(event) => setDraft({ ...draft, task_extraction_provider: event.target.value })}
                >
                  <option value="mock">mock</option>
                  <option value="ollama">ollama</option>
                </select>
              </label>

              <label className="field">
                <span>Extraction model</span>
                <select value={draft.extraction_model} onChange={(event) => setDraft({ ...draft, extraction_model: event.target.value })}>
                  {chatModels.length === 0 ? <option value="">No local chat models found</option> : null}
                  {chatModels.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Recap narrative provider</span>
                <select
                  value={draft.recap_narrative_provider}
                  onChange={(event) => setDraft({ ...draft, recap_narrative_provider: event.target.value })}
                >
                  <option value="off">off</option>
                  <option value="mock">mock</option>
                  <option value="ollama">ollama</option>
                </select>
              </label>

              <label className="field">
                <span>Recap model</span>
                <select value={draft.recap_model} onChange={(event) => setDraft({ ...draft, recap_model: event.target.value })}>
                  {chatModels.length === 0 ? <option value="">No local chat models found</option> : null}
                  {chatModels.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>STT provider</span>
                <select value={draft.stt_provider} onChange={(event) => setDraft({ ...draft, stt_provider: event.target.value })}>
                  <option value="whisper_cpp">whisper.cpp</option>
                  <option value="local_stub">local_stub testing mode</option>
                </select>
              </label>

              <label className="field">
                <span>STT model</span>
                <input value={draft.stt_model} onChange={(event) => setDraft({ ...draft, stt_model: event.target.value })} />
              </label>

              <label className="field field--full">
                <span>whisper.cpp executable</span>
                <input
                  value={draft.stt_executable_path ?? ""}
                  onChange={(event) => setDraft({ ...draft, stt_executable_path: event.target.value || null })}
                  placeholder="C:\\path\\to\\whisper-cli.exe"
                />
              </label>

              <label className="field field--full">
                <span>Whisper model path</span>
                <input
                  value={draft.stt_model_path ?? ""}
                  onChange={(event) => setDraft({ ...draft, stt_model_path: event.target.value || null })}
                  placeholder="C:\\path\\to\\ggml-model.bin"
                />
              </label>

              <label className="field field--full">
                <span>Ollama base URL</span>
                <input
                  value={draft.ollama_base_url}
                  onChange={(event) => setDraft({ ...draft, ollama_base_url: event.target.value })}
                  placeholder="http://127.0.0.1:11434"
                />
              </label>

              <label className="field">
                <span>Timeout (s)</span>
                <input
                  type="number"
                  min={5}
                  value={draft.extraction_timeout_seconds}
                  onChange={(event) => setDraft({ ...draft, extraction_timeout_seconds: Number(event.target.value) || 5 })}
                />
              </label>
            </div>

            <div className="settings-diagnostics">
              <article className="settings-check-card">
                <div className="settings-check-card__header">
                  <div>
                    <p className="section-eyebrow">Transcription check</p>
                    <strong>{draft.stt_ready ? "Ready" : providerCheckLabel(providerChecks.stt)}</strong>
                  </div>
                  <button className="secondary-button secondary-button--ghost" type="button" onClick={() => void onCheckProvider("stt")}>
                    Check STT
                  </button>
                </div>
                <p className="muted-copy">
                  {providerChecks.stt?.message ??
                    (draft.stt_provider === "local_stub"
                      ? "Testing mode is selected. Recordings will not produce real transcripts."
                      : "Add a local whisper.cpp executable and model before voice notes can be transcribed.")}
                </p>
              </article>

              <article className="settings-check-card">
                <div className="settings-check-card__header">
                  <div>
                    <p className="section-eyebrow">Extraction check</p>
                    <strong>{providerCheckLabel(providerChecks.task_extraction)}</strong>
                  </div>
                  <button className="secondary-button secondary-button--ghost" type="button" onClick={() => void onCheckProvider("task_extraction")}>
                    Check extraction
                  </button>
                </div>
                <p className="muted-copy">
                  {providerChecks.task_extraction?.message ?? "Useful when Ollama feels unavailable or the base URL looks suspicious."}
                </p>
                {providerChecks.task_extraction?.normalized_base_url ? (
                  <div className="chip-row">
                    <span className="meta-chip">{providerChecks.task_extraction.normalized_base_url}</span>
                  </div>
                ) : null}
              </article>

              <article className="settings-check-card">
                <div className="settings-check-card__header">
                  <div>
                    <p className="section-eyebrow">Narrative check</p>
                    <strong>{providerCheckLabel(providerChecks.recap_narrative)}</strong>
                  </div>
                  <button className="secondary-button secondary-button--ghost" type="button" onClick={() => void onCheckProvider("recap_narrative")}>
                    Check narrative
                  </button>
                </div>
                <p className="muted-copy">
                  {providerChecks.recap_narrative?.message ?? "A quick way to confirm recap reflection is reachable before you ask for it."}
                </p>
                {providerChecks.recap_narrative?.normalized_base_url ? (
                  <div className="chip-row">
                    <span className="meta-chip">{providerChecks.recap_narrative.normalized_base_url}</span>
                  </div>
                ) : null}
              </article>
            </div>
          </section>

          <section className="settings-section">
            <div className="surface-panel__header surface-panel__header--stack">
              <div>
                <p className="section-eyebrow">Device</p>
                <h4>Sync readiness</h4>
              </div>
              <div className="chip-row">
                <span className="meta-chip">{syncStatus?.provider_name === "local_only" ? "Local-only sync" : "Remote sync configured"}</span>
                <span className="meta-chip">
                  {syncStatus?.current_device ? `${syncStatus.current_device.device_name} registered` : "Device not registered"}
                </span>
                {syncStatus?.last_sync_at ? <span className="meta-chip">{`Last sync ${new Date(syncStatus.last_sync_at).toLocaleString()}`}</span> : null}
              </div>
            </div>

            <div className="form-grid">
              <label className="field">
                <span>Sync provider</span>
                <input value={draft.sync_provider} onChange={(event) => setDraft({ ...draft, sync_provider: event.target.value })} />
              </label>

              <label className="field">
                <span>Auth provider</span>
                <input value={draft.auth_provider} onChange={(event) => setDraft({ ...draft, auth_provider: event.target.value })} />
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
              <span className="helper-text">Device registration stays optional. Normal local use does not depend on sync.</span>
              <button className="secondary-button" type="button" onClick={() => void onRegisterDevice()}>
                {syncStatus?.current_device ? "Refresh device" : "Register this device"}
              </button>
            </div>
          </section>

          <div className="form-actions">
            <span className="helper-text">Use the Ollama server root URL here. Task Garden handles the `/api` routes for you.</span>
            <button className="primary-button" type="submit">
              Save Settings
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
