import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";

import { formatDate, toApiDate, toDateInputValue } from "../../features/tasks/task-utils";
import type {
  ConfirmExtractionCandidateInput,
  CreateEntryInput,
  CreateTaskInput,
  ExtractionBatch,
  ExtractionCandidate,
  ExtractionCandidateDecision,
  Project,
  RawEntry,
  TaskEffort,
  TaskEnergy,
  TaskPriority,
  TaskStatus,
  TranscriptionResult,
} from "../../lib/types";

type CaptureScreenProps = {
  entries: RawEntry[];
  projects: Project[];
  activeExtraction: ExtractionBatch | null;
  latestTranscription: TranscriptionResult | null;
  extractionNotice: string | null;
  onCreateEntry: (payload: CreateEntryInput) => Promise<void>;
  onTranscribeAudio: (audioBlob: Blob, fileName?: string) => Promise<TranscriptionResult>;
  onCreateTask: (payload: CreateTaskInput) => Promise<void>;
  onRunExtract: (entryId: string) => Promise<void>;
  onConfirmExtraction: (extractionId: string, candidates: ConfirmExtractionCandidateInput[]) => Promise<void>;
  onArchiveEntry: (entryId: string) => Promise<void>;
};

type ReviewDraft = ExtractionCandidate & {
  decision: ExtractionCandidateDecision;
  labelsInput: string;
  dueDateInput: string;
};

type RecordingState = "idle" | "recording" | "ready" | "transcribing";

const priorityOptions: TaskPriority[] = ["low", "medium", "high", "critical"];
const effortOptions: TaskEffort[] = ["small", "medium", "large"];
const energyOptions: TaskEnergy[] = ["low", "medium", "high"];
const statusOptions: TaskStatus[] = ["inbox", "planned", "in_progress", "blocked"];

function candidateToDraft(candidate: ExtractionCandidate): ReviewDraft {
  return {
    ...candidate,
    decision: candidate.candidate_status === "rejected" ? "rejected" : "accepted",
    labelsInput: candidate.labels.join(", "),
    dueDateInput: toDateInputValue(candidate.due_date),
  };
}

export function CaptureScreen({
  entries,
  projects,
  activeExtraction,
  latestTranscription,
  extractionNotice,
  onCreateEntry,
  onTranscribeAudio,
  onCreateTask,
  onRunExtract,
  onConfirmExtraction,
  onArchiveEntry,
}: CaptureScreenProps): JSX.Element {
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
  const [reviewDrafts, setReviewDrafts] = useState<ReviewDraft[]>([]);
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [micError, setMicError] = useState<string | null>(null);
  const [micLevel, setMicLevel] = useState(0.12);
  const [showManualTask, setShowManualTask] = useState(false);
  const [showRecentNotes, setShowRecentNotes] = useState(false);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    setReviewDrafts(activeExtraction?.candidates.map(candidateToDraft) ?? []);
  }, [activeExtraction]);

  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        void audioContextRef.current.close();
      }
    };
  }, [audioUrl]);

  const acceptedCount = useMemo(
    () => reviewDrafts.filter((candidate) => candidate.decision === "accepted").length,
    [reviewDrafts],
  );

  const waveformBars = Array.from({ length: 14 }, (_, index) => {
    const swing = Math.sin(index * 0.9 + micLevel * 8);
    return Math.max(0.22, Math.min(1, micLevel * 1.2 + (swing + 1) * 0.18));
  });

  function stopAudioMonitoring(): void {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    analyserRef.current = null;
    if (audioContextRef.current) {
      void audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setMicLevel(0.12);
  }

  function startAudioMonitoring(stream: MediaStream): void {
    const AudioContextCtor = window.AudioContext ?? (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioContextCtor) {
      return;
    }
    const context = new AudioContextCtor();
    const analyser = context.createAnalyser();
    analyser.fftSize = 64;
    const source = context.createMediaStreamSource(stream);
    source.connect(analyser);
    const buffer = new Uint8Array(analyser.frequencyBinCount);

    audioContextRef.current = context;
    analyserRef.current = analyser;

    const tick = (): void => {
      if (!analyserRef.current) {
        return;
      }
      analyserRef.current.getByteFrequencyData(buffer);
      const average = buffer.reduce((sum, value) => sum + value, 0) / buffer.length;
      setMicLevel(Math.max(0.08, average / 255));
      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);
  }

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

  async function handleConfirmReview(): Promise<void> {
    if (!activeExtraction) {
      return;
    }

    await onConfirmExtraction(
      activeExtraction.id,
      reviewDrafts.map((candidate) => ({
        id: candidate.id,
        decision: candidate.decision,
        title: candidate.title,
        details: candidate.details,
        project_or_group: candidate.project_or_group,
        priority: candidate.priority,
        effort: candidate.effort,
        energy: candidate.energy,
        labels: candidate.labelsInput
          .split(",")
          .map((label) => label.trim())
          .filter(Boolean),
        due_date: toApiDate(candidate.dueDateInput) ?? null,
        parent_task_title: candidate.parent_task_title,
        confidence: candidate.confidence,
        source_excerpt: candidate.source_excerpt,
      })),
    );
  }

  async function handleToggleRecording(): Promise<void> {
    setMicError(null);

    if (recordingState === "recording") {
      recorderRef.current?.stop();
      stopAudioMonitoring();
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setMicError("This browser does not support microphone recording.");
      return;
    }

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }
    setAudioBlob(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      streamRef.current = stream;
      recorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      });

      recorder.addEventListener("stop", () => {
        const nextBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType || "audio/webm" });
        setAudioBlob(nextBlob);
        setAudioUrl(URL.createObjectURL(nextBlob));
        setRecordingState("ready");
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      });

      startAudioMonitoring(stream);
      recorder.start();
      setRecordingState("recording");
    } catch (error) {
      setMicError(error instanceof Error ? error.message : "Microphone access failed.");
      stopAudioMonitoring();
    }
  }

  async function handleTranscribeRecording(): Promise<void> {
    if (!audioBlob) {
      return;
    }
    setRecordingState("transcribing");
    try {
      await onTranscribeAudio(audioBlob, `task-garden-${Date.now()}.webm`);
      setRecordingState("ready");
    } catch (error) {
      setRecordingState("ready");
      setMicError(error instanceof Error ? error.message : "Transcription failed.");
    }
  }

  function updateDraft(candidateId: string, updates: Partial<ReviewDraft>): void {
    setReviewDrafts((current) => current.map((candidate) => (candidate.id === candidateId ? { ...candidate, ...updates } : candidate)));
  }

  return (
    <section className="workspace">
      <div className="hero-card hero-card--capture">
        <div>
          <p className="section-eyebrow">Capture</p>
          <h3>Get the thought out first. Shape it when you have the energy.</h3>
        </div>
      </div>

      {extractionNotice ? <div className="info-banner">{extractionNotice}</div> : null}
      {micError ? <div className="error-banner">{micError}</div> : null}

      <div className="screen-grid screen-grid--capture screen-grid--capture-focus">
        <form className="surface-panel surface-panel--composer" onSubmit={handleSaveEntry}>
          <div className="composer-shell">
            <div className="composer-shell__header">
              <div>
                <p className="section-eyebrow">Composer</p>
                <h4>Type or speak in one place</h4>
              </div>
              <div className="chip-row">
                <button
                  className={`toggle-chip${sourceType === "typed" ? " toggle-chip--active" : ""}`}
                  type="button"
                  onClick={() => setSourceType("typed")}
                >
                  Typed
                </button>
                <button
                  className={`toggle-chip${sourceType === "pasted" ? " toggle-chip--active" : ""}`}
                  type="button"
                  onClick={() => setSourceType("pasted")}
                >
                  Pasted
                </button>
              </div>
            </div>

            <div className={`composer-input${recordingState === "recording" ? " composer-input--recording" : ""}`}>
              <textarea
                className="composer-input__textarea"
                value={rawText}
                onChange={(event) => setRawText(event.target.value)}
                placeholder="Dump the note in plain language, or tap the mic and talk it through."
                rows={8}
              />
              <button
                className={`composer-mic-button${recordingState === "recording" ? " composer-mic-button--recording" : ""}`}
                type="button"
                onClick={() => void handleToggleRecording()}
                disabled={recordingState === "transcribing"}
                aria-label={recordingState === "recording" ? "Stop recording" : "Start recording"}
              >
                {recordingState === "recording" ? "Stop" : "Mic"}
              </button>
            </div>

            <div className="composer-footer">
              <div className={`wave-meter${recordingState === "recording" ? " wave-meter--active" : ""}`} aria-hidden="true">
                {waveformBars.map((bar, index) => (
                  <span key={index} style={{ transform: `scaleY(${bar})` }} />
                ))}
              </div>
              <div className="composer-footer__actions">
                {audioBlob ? (
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => void handleTranscribeRecording()}
                    disabled={recordingState === "transcribing"}
                  >
                    {recordingState === "transcribing" ? "Transcribing..." : "Transcribe"}
                  </button>
                ) : null}
                <button className="primary-button" type="submit" disabled={!rawText.trim()}>
                  Save Note
                </button>
              </div>
            </div>

            {audioUrl ? (
              <div className="audio-preview">
                <audio controls src={audioUrl} />
              </div>
            ) : null}

            {latestTranscription ? (
              <div className="transcript-preview">
                <div className="transcript-preview__header">
                  <div>
                    <p className="section-eyebrow">Transcript</p>
                    <strong>Saved as a raw entry</strong>
                  </div>
                  <div className="chip-row">
                    {latestTranscription.raw_entry.transcript_provider_name ? (
                      <span className="meta-chip">{latestTranscription.raw_entry.transcript_provider_name}</span>
                    ) : null}
                    <span className="meta-chip">{formatDate(latestTranscription.raw_entry.created_at)}</span>
                  </div>
                </div>
                <p>{latestTranscription.raw_entry.raw_text}</p>
                <div className="form-actions">
                  <span className="helper-text">Nothing turns into a task until you review it.</span>
                  <button className="primary-button" type="button" onClick={() => void onRunExtract(latestTranscription.raw_entry.id)}>
                    Extract Tasks
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </form>

        <section className={`surface-panel manual-task-panel${showManualTask ? " manual-task-panel--open" : ""}`}>
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Manual</p>
              <h4>Add a task directly</h4>
            </div>
            <button className="secondary-button secondary-button--ghost" type="button" onClick={() => setShowManualTask((value) => !value)}>
              {showManualTask ? "Hide" : "Add manually"}
            </button>
          </div>

          {showManualTask ? <form onSubmit={handleCreateTask}>
            <div className="form-grid">
              <label className="field field--full">
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
                  placeholder="Optional context."
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
              <span className="helper-text">Useful when you already know the task shape.</span>
              <button className="primary-button" type="submit">
                Create Task
              </button>
            </div>
          </form> : <p className="muted-copy">Keep capture focused. Open this when you already know the exact task.</p>}
        </section>
      </div>

      <section className="surface-panel">
        <div className="surface-panel__header">
          <div>
            <p className="section-eyebrow">Recent notes</p>
            <h4>{entries.length} preserved {entries.length === 1 ? "note" : "notes"}</h4>
          </div>
          <button className="secondary-button secondary-button--ghost" type="button" onClick={() => setShowRecentNotes((value) => !value)}>
            {showRecentNotes ? "Collapse" : "Show"}
          </button>
        </div>

        {showRecentNotes ? <div className="entry-list">
          {entries.length === 0 ? <p className="empty-state">Nothing captured yet.</p> : null}
          {entries.map((entry) => (
            <article key={entry.id} className="entry-card entry-card--stack">
              <div className="entry-card__meta">
                <span className="meta-chip">{entry.source_type}</span>
                <span className="meta-chip">{formatDate(entry.created_at)}</span>
                {entry.transcript_provider_name ? <span className="meta-chip">{entry.transcript_provider_name}</span> : null}
              </div>
              <p>{entry.raw_text || "Audio saved. Transcript still pending."}</p>
              <div className="entry-card__actions">
                <button className="secondary-button" type="button" onClick={() => void onRunExtract(entry.id)} disabled={!entry.raw_text.trim()}>
                  Extract Tasks
                </button>
                <button className="secondary-button secondary-button--ghost" type="button" onClick={() => void onArchiveEntry(entry.id)}>
                  Remove
                </button>
              </div>
            </article>
          ))}
        </div> : <p className="muted-copy">Notes stay preserved without taking over the capture screen.</p>}
      </section>

      {activeExtraction ? (
        <section className="surface-panel review-surface">
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Review</p>
              <h4>Suggested tasks</h4>
              <p className="muted-copy">{activeExtraction.summary ?? "Review each suggestion before it becomes real work."}</p>
            </div>
            <div className="review-summary">
              <span className="meta-chip">{reviewDrafts.length} suggestions</span>
              <span className="meta-chip">{acceptedCount} selected</span>
            </div>
          </div>

          <div className="review-callout">
            <strong>Still just suggestions.</strong>
            <span>Edit, reject, or confirm only what belongs in your task list.</span>
          </div>

          <div className="review-list">
            {reviewDrafts.map((candidate) => (
              <article key={candidate.id} className="review-card">
                <div className="review-card__header">
                  <div className="decision-toggle" role="group" aria-label="Candidate decision">
                    <button
                      className={`toggle-chip${candidate.decision === "accepted" ? " toggle-chip--active" : ""}`}
                      type="button"
                      onClick={() => updateDraft(candidate.id, { decision: "accepted" })}
                    >
                      Keep
                    </button>
                    <button
                      className={`toggle-chip${candidate.decision === "rejected" ? " toggle-chip--danger" : ""}`}
                      type="button"
                      onClick={() => updateDraft(candidate.id, { decision: "rejected" })}
                    >
                      Reject
                    </button>
                  </div>
                  <span className="meta-chip">{Math.round(candidate.confidence * 100)}%</span>
                </div>

                <div className="form-grid form-grid--review">
                  <label className="field field--full">
                    <span>Title</span>
                    <input value={candidate.title} onChange={(event) => updateDraft(candidate.id, { title: event.target.value })} />
                  </label>

                  <label className="field field--full">
                    <span>Details</span>
                    <textarea
                      className="text-area text-area--compact"
                      value={candidate.details ?? ""}
                      onChange={(event) => updateDraft(candidate.id, { details: event.target.value })}
                      rows={3}
                    />
                  </label>

                  <label className="field">
                    <span>Project / Group</span>
                    <input
                      value={candidate.project_or_group ?? ""}
                      onChange={(event) => updateDraft(candidate.id, { project_or_group: event.target.value || null })}
                    />
                  </label>

                  <label className="field">
                    <span>Due date</span>
                    <input
                      type="date"
                      value={candidate.dueDateInput}
                      onChange={(event) => updateDraft(candidate.id, { dueDateInput: event.target.value })}
                    />
                  </label>

                  <label className="field">
                    <span>Priority</span>
                    <select
                      value={candidate.priority}
                      onChange={(event) => updateDraft(candidate.id, { priority: event.target.value as TaskPriority })}
                    >
                      {priorityOptions.map((priority) => (
                        <option key={priority} value={priority}>
                          {priority}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Effort</span>
                    <select value={candidate.effort} onChange={(event) => updateDraft(candidate.id, { effort: event.target.value as TaskEffort })}>
                      {effortOptions.map((effort) => (
                        <option key={effort} value={effort}>
                          {effort}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Energy</span>
                    <select value={candidate.energy} onChange={(event) => updateDraft(candidate.id, { energy: event.target.value as TaskEnergy })}>
                      {energyOptions.map((energy) => (
                        <option key={energy} value={energy}>
                          {energy}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="field">
                    <span>Labels</span>
                    <input
                      value={candidate.labelsInput}
                      onChange={(event) => updateDraft(candidate.id, { labelsInput: event.target.value })}
                      placeholder="comma-separated"
                    />
                  </label>
                </div>

                <div className="review-excerpt">
                  <p className="section-eyebrow">Source excerpt</p>
                  <p>{candidate.source_excerpt ?? "No excerpt available."}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="form-actions">
            <span className="helper-text">Only confirmed items become real tasks.</span>
            <button
              className="primary-button"
              type="button"
              onClick={() => void handleConfirmReview()}
              disabled={acceptedCount === 0 || !activeExtraction.needs_review}
            >
              Confirm Selected Tasks
            </button>
          </div>
        </section>
      ) : null}
    </section>
  );
}
