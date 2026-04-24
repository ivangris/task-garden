import { useMemo, useState, type JSX } from "react";

import { metricJson, metricMap, metricNumber, metricText, stageChangeLabel } from "../../features/recaps/recap-utils";
import { formatDate } from "../../features/tasks/task-utils";
import type { RecapNarrative, RecapPeriod, RecapPeriodType } from "../../lib/types";

type RecapsScreenProps = {
  recaps: Partial<Record<RecapPeriodType, RecapPeriod>>;
  isLoading: boolean;
  isGeneratingNarrative: boolean;
  onGenerate: (periodType: RecapPeriodType) => Promise<void>;
  onGenerateNarrative: (periodType: RecapPeriodType) => Promise<void>;
};

const periodOrder: RecapPeriodType[] = ["weekly", "monthly", "yearly"];

function narrativeStatusLabel(narrative: RecapNarrative | null | undefined): string {
  if (!narrative || narrative.generation_status === "not_generated") {
    return "Not generated";
  }
  if (narrative.generation_status === "generated") {
    return `${narrative.provider_name ?? "local"} / ${narrative.model_name ?? "default"}`;
  }
  if (narrative.generation_status === "disabled") {
    return "Narrative off";
  }
  return "Generation failed";
}

export function RecapsScreen({
  recaps,
  isLoading,
  isGeneratingNarrative,
  onGenerate,
  onGenerateNarrative,
}: RecapsScreenProps): JSX.Element {
  const [activePeriod, setActivePeriod] = useState<RecapPeriodType>("yearly");
  const recap = recaps[activePeriod] ?? null;
  const metrics = useMemo(() => metricMap(recap), [recap]);
  const heroCard = recap?.cards.find((card) => card.card_type === "hero") ?? null;
  const topProjectNames = (metricJson(metrics, "top_projects").names as string[] | undefined) ?? [];
  const narrative = recap?.narrative ?? null;

  return (
    <section className="workspace">
      <div className="hero-card recap-hero">
        <div className="recap-hero__copy">
          <p className="section-eyebrow">Recaps</p>
          <h3>{heroCard?.title ?? "Look back at what moved."}</h3>
          <p className="muted-copy">
            {heroCard?.supporting_text ?? "Deterministic accomplishment snapshots built from tasks, activity, and garden progress."}
          </p>
        </div>
        <div className="recap-tabs" role="tablist" aria-label="Recap periods">
          {periodOrder.map((period) => (
            <button
              key={period}
              className={`toggle-chip${period === activePeriod ? " toggle-chip--active" : ""}`}
              type="button"
              role="tab"
              aria-selected={period === activePeriod}
              onClick={() => setActivePeriod(period)}
            >
              {period.replace(/^\w/, (value) => value.toUpperCase())}
            </button>
          ))}
        </div>
      </div>

      <section className="surface-panel recap-toolbar">
        <div>
          <p className="section-eyebrow">Current Period</p>
          <h4>{recap?.period_label ?? `${activePeriod.replace(/^\w/, (value) => value.toUpperCase())} recap`}</h4>
          <p className="muted-copy">
            {recap ? `Updated ${formatDate(recap.generated_at)}` : "Generate a recap when you want a clean snapshot of progress."}
          </p>
        </div>
        <button className="primary-button" type="button" onClick={() => void onGenerate(activePeriod)}>
          {isLoading ? "Generating..." : `Refresh ${activePeriod}`}
        </button>
      </section>

      {!recap && !isLoading ? (
        <section className="surface-panel surface-panel--empty-state">
          <p className="section-eyebrow">Recap</p>
          <h4>This view is ready whenever you want to look back.</h4>
          <p className="empty-state">Generate a {activePeriod} recap to turn recent work, garden change, and streaks into a calm summary.</p>
        </section>
      ) : null}

      {recap ? (
        <>
          <section className="recap-metrics-grid">
            <article className="surface-panel recap-stat-card recap-stat-card--hero">
              <p className="section-eyebrow">Completed</p>
              <strong>{metricNumber(metrics, "total_tasks_completed") ?? 0}</strong>
              <span>tasks finished</span>
            </article>
            <article className="surface-panel recap-stat-card">
              <p className="section-eyebrow">Active Days</p>
              <strong>{metricNumber(metrics, "active_days") ?? 0}</strong>
              <span>days with momentum</span>
            </article>
            <article className="surface-panel recap-stat-card">
              <p className="section-eyebrow">XP Gained</p>
              <strong>{metricNumber(metrics, "xp_gained") ?? 0}</strong>
              <span>garden progress</span>
            </article>
            <article className="surface-panel recap-stat-card">
              <p className="section-eyebrow">Garden Shift</p>
              <strong>{`${metricNumber(metrics, "garden_health_delta") ?? 0 > -1 ? "+" : ""}${metricNumber(metrics, "garden_health_delta") ?? 0}`}</strong>
              <span>{stageChangeLabel(metricText(metrics, "garden_stage_change"))}</span>
            </article>
          </section>

          <section className="screen-grid recap-screen-grid">
            <section className="surface-panel surface-panel--wide">
              <div className="surface-panel__header surface-panel__header--stack">
                <div>
                  <p className="section-eyebrow">Highlights</p>
                  <h4>Concrete wins from the period</h4>
                </div>
                <p className="muted-copy">The facts stay primary. These cards simply give the period a clearer shape.</p>
              </div>
              <div className="recap-card-grid">
                {recap.cards
                  .filter((card) => card.card_type !== "hero")
                  .map((card) => (
                    <article key={card.id} className={`recap-highlight-card recap-highlight-card--${card.visual_hint ?? "default"}`}>
                      <p className="section-eyebrow">{card.card_type.replace(/_/g, " ")}</p>
                      <h5>{card.title}</h5>
                      {card.subtitle ? <strong>{card.subtitle}</strong> : null}
                      {card.primary_value ? <span className="recap-highlight-card__value">{card.primary_value}</span> : null}
                      {card.secondary_value ? <span className="recap-highlight-card__secondary">{card.secondary_value}</span> : null}
                      {card.supporting_text ? <p>{card.supporting_text}</p> : null}
                    </article>
                  ))}
              </div>
            </section>

            <section className="surface-panel">
              <div className="surface-panel__header">
                <div>
                  <p className="section-eyebrow">Reflection</p>
                  <h4>Optional recap narrative</h4>
                </div>
                <button className="secondary-button" type="button" onClick={() => void onGenerateNarrative(activePeriod)}>
                  {isGeneratingNarrative
                    ? "Generating..."
                    : narrative?.generation_status === "generated"
                      ? "Regenerate"
                      : "Generate"}
                </button>
              </div>
              <div className="recap-narrative">
                <div className="chip-row">
                  <span className="meta-chip">{narrativeStatusLabel(narrative)}</span>
                  {narrative?.generated_at ? <span className="meta-chip">{`Updated ${formatDate(narrative.generated_at)}`}</span> : null}
                </div>
                {narrative?.generation_status === "generated" && narrative.narrative_text ? (
                  <p className="recap-narrative__body">{narrative.narrative_text}</p>
                ) : null}
                {narrative?.generation_status === "failed" ? (
                  <div className="recap-narrative__notice recap-narrative__notice--error">
                    <strong>Local narrative generation did not complete.</strong>
                    <p>{String(narrative.error_metadata.message ?? "The factual recap is still available below.")}</p>
                  </div>
                ) : null}
                {narrative?.generation_status === "disabled" ? (
                  <div className="recap-narrative__notice">
                    <strong>Narrative is off.</strong>
                    <p>Turn on a local provider in Settings when you want a short reflective layer.</p>
                  </div>
                ) : null}
                {!narrative || narrative.generation_status === "not_generated" ? (
                  <div className="recap-narrative__notice">
                    <strong>Add reflection on demand.</strong>
                    <p>The recap cards already stand on their own. This only adds a short grounded readback.</p>
                  </div>
                ) : null}
              </div>
            </section>

            <section className="surface-panel">
              <div className="surface-panel__header surface-panel__header--stack">
                <div>
                  <p className="section-eyebrow">Project Themes</p>
                  <h4>What kept moving</h4>
                </div>
              </div>
              <div className="project-list">
                {recap.project_summaries.slice(0, 3).map((item) => (
                  <article key={item.id} className="project-card recap-project-card">
                    <div>
                      <strong>{item.project_name}</strong>
                      <p>{item.completed_task_count} completed tasks</p>
                    </div>
                    <div className="chip-row">
                      <span className="meta-chip">{item.xp_gained} XP</span>
                      <span className="meta-chip">{Math.round(item.completion_share * 100)}%</span>
                    </div>
                  </article>
                ))}
                {recap.project_summaries.length === 0 ? <p className="empty-state">No project theme stood out in this slice yet.</p> : null}
              </div>
              {topProjectNames.length > 0 ? <p className="muted-copy">{`Top themes: ${topProjectNames.join(", ")}`}</p> : null}
            </section>

            <section className="surface-panel">
              <div className="surface-panel__header surface-panel__header--stack">
                <div>
                  <p className="section-eyebrow">Streaks</p>
                  <h4>Consistency and comeback</h4>
                </div>
              </div>
              <div className="recap-streak-block">
                <div>
                  <strong>{recap.streak_summary?.period_best_streak_days ?? 0}</strong>
                  <span>best streak in period</span>
                </div>
                <div>
                  <strong>{recap.streak_summary?.longest_streak_days ?? 0}</strong>
                  <span>longest overall streak</span>
                </div>
                <div>
                  <strong>{recap.streak_summary?.current_streak_days ?? 0}</strong>
                  <span>current streak</span>
                </div>
              </div>
            </section>
          </section>

          <section className="screen-grid recap-screen-grid">
            <section className="surface-panel">
              <div className="surface-panel__header surface-panel__header--stack">
                <div>
                  <p className="section-eyebrow">Milestones</p>
                  <h4>Moments worth remembering</h4>
                </div>
              </div>
              <div className="recap-milestone-list">
                {recap.milestones.map((item) => (
                  <article key={item.id} className="recap-milestone-card">
                    <strong>{item.title}</strong>
                    <p>{item.description}</p>
                  </article>
                ))}
                {recap.milestones.length === 0 ? <p className="empty-state">No big threshold landed this time, but the progress still counts.</p> : null}
              </div>
            </section>

            <section className="surface-panel">
              <div className="surface-panel__header surface-panel__header--stack">
                <div>
                  <p className="section-eyebrow">Garden Summary</p>
                  <h4>From work to visible restoration</h4>
                </div>
              </div>
              <div className="recap-garden-summary">
                <div className="chip-row">
                  <span className="meta-chip">{`XP +${metricNumber(metrics, "xp_gained") ?? 0}`}</span>
                  <span className="meta-chip">{`${metricNumber(metrics, "unlocks_earned") ?? 0} unlocks`}</span>
                  <span className="meta-chip">{`${metricNumber(metrics, "overdue_recovered_count") ?? 0} overdue recoveries`}</span>
                </div>
                <p className="muted-copy">{stageChangeLabel(metricText(metrics, "garden_stage_change"))}</p>
                <p className="muted-copy">{`Biggest completed win: ${metricText(metrics, "biggest_completed_task") ?? "No completed task title available."}`}</p>
              </div>
            </section>
          </section>
        </>
      ) : null}
    </section>
  );
}
