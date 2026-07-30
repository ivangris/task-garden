import { useMemo, useState, type JSX } from "react";

import { metricMap, metricNumber, metricText, stageChangeLabel } from "../../features/recaps/recap-utils";
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
const hiddenHighlightTypes = new Set(["garden", "biggest_win"]);

const recapIconByType: Record<string, JSX.Element> = {
  active_days: (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M8 36h32" />
      <path d="M14 36c0-10 4-18 10-24 6 6 10 14 10 24" />
      <path d="M24 13v23" />
      <path d="M17 24h14" />
    </svg>
  ),
  top_project: (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M10 34h28" />
      <path d="M14 34V18h20v16" />
      <path d="M19 18c1-5 9-5 10 0" />
      <path d="M18 25h12" />
    </svg>
  ),
  streak: (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M16 38c-3-4-4-9-1-14 2-4 6-6 7-12 7 5 13 12 10 22" />
      <path d="M24 39c-3-3-3-7 0-11 3 3 5 7 3 11" />
    </svg>
  ),
  milestone: (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M12 35h24" />
      <path d="M18 35V16h12v19" />
      <path d="M18 16l6-6 6 6" />
      <path d="M15 24h18" />
    </svg>
  ),
  project_focus: (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M12 34h24" />
      <path d="M16 34V18h16v16" />
      <path d="M20 23h8" />
      <path d="M20 28h8" />
    </svg>
  ),
  default: (
    <svg viewBox="0 0 48 48" aria-hidden="true">
      <path d="M9 36h30" />
      <path d="M15 36c0-9 4-16 9-21 5 5 9 12 9 21" />
      <path d="M24 36V15" />
    </svg>
  ),
};

function recapIcon(type: string): JSX.Element {
  return recapIconByType[type] ?? recapIconByType.default;
}

function highlightLabel(cardType: string): string {
  const labels: Record<string, string> = {
    active_days: "Active Days",
    top_project: "Top Project",
    streak: "Streak",
    milestone: "Milestone",
    project_focus: "Project",
  };
  return labels[cardType] ?? cardType.replace(/_/g, " ");
}

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
  const narrative = recap?.narrative ?? null;

  return (
    <section className="workspace">
      <div className="hero-card recap-hero">
        <div className="recap-hero__copy">
          <p className="section-eyebrow">Recaps</p>
          <h3>{heroCard?.title ?? "Look back at what moved."}</h3>
          <p className="muted-copy">
            {heroCard?.supporting_text ?? "A clean snapshot of what you finished, where momentum showed up, and how the garden changed."}
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

      {!recap && !isLoading ? (
        <section className="surface-panel surface-panel--empty-state">
          <p className="section-eyebrow">Recap</p>
          <h4>This view is ready whenever you want to look back.</h4>
          <p className="empty-state">Generate a {activePeriod} recap when you want a simple look back.</p>
        </section>
      ) : null}

      {recap ? (
        <>
          <section className="recap-metrics-grid">
            <article className="surface-panel recap-stat-card recap-stat-card--hero">
              <span className="recap-icon">{recapIcon("active_days")}</span>
              <p className="section-eyebrow">Completed</p>
              <strong>{metricNumber(metrics, "total_tasks_completed") ?? 0}</strong>
            </article>
            <article className="surface-panel recap-stat-card">
              <span className="recap-icon">{recapIcon("streak")}</span>
              <p className="section-eyebrow">Best Streak</p>
              <strong>{recap.streak_summary?.period_best_streak_days ?? 0}</strong>
            </article>
            <article className="surface-panel recap-stat-card">
              <span className="recap-icon">{recapIcon("streak")}</span>
              <p className="section-eyebrow">Longest</p>
              <strong>{recap.streak_summary?.longest_streak_days ?? 0}</strong>
            </article>
            <article className="surface-panel recap-stat-card">
              <span className="recap-icon">{recapIcon("streak")}</span>
              <p className="section-eyebrow">Current</p>
              <strong>{recap.streak_summary?.current_streak_days ?? 0}</strong>
            </article>
            <article className="surface-panel recap-stat-card">
              <span className="recap-icon">{recapIcon("milestone")}</span>
              <p className="section-eyebrow">XP</p>
              <strong>{metricNumber(metrics, "xp_gained") ?? 0}</strong>
            </article>
            <article className="surface-panel recap-stat-card">
              <span className="recap-icon">{recapIcon("default")}</span>
              <p className="section-eyebrow">Garden</p>
              <strong>{`${metricNumber(metrics, "garden_health_delta") ?? 0 > -1 ? "+" : ""}${metricNumber(metrics, "garden_health_delta") ?? 0}`}</strong>
              <span>{stageChangeLabel(metricText(metrics, "garden_stage_change"))}</span>
            </article>
          </section>

          <section className="recap-screen-grid">
            <section className="surface-panel">
              <div className="surface-panel__header surface-panel__header--stack">
                <div>
                  <p className="section-eyebrow">Highlights</p>
                </div>
                <button className="primary-button primary-button--small" type="button" onClick={() => void onGenerate(activePeriod)}>
                  {isLoading ? "Refreshing..." : `Refresh ${activePeriod}`}
                </button>
              </div>
              <div className="recap-card-grid">
                {recap.cards
                  .filter((card) => card.card_type !== "hero" && !hiddenHighlightTypes.has(card.card_type))
                  .map((card) => (
                    <article key={card.id} className={`recap-highlight-card recap-highlight-card--${card.visual_hint ?? "default"}`}>
                      <span className="recap-icon recap-icon--large">{recapIcon(card.card_type)}</span>
                      <p className="section-eyebrow">{highlightLabel(card.card_type)}</p>
                      {card.subtitle && card.card_type === "top_project" ? <strong>{card.subtitle}</strong> : null}
                      {card.card_type === "milestone" ? <h5>{card.title}</h5> : null}
                      {card.primary_value ? <span className="recap-highlight-card__value">{card.primary_value}</span> : null}
                    </article>
                  ))}
              </div>
            </section>

            <section className="surface-panel">
              <div className="surface-panel__header">
                <div>
                  <p className="section-eyebrow">Reflection</p>
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
                    <p>Add a short readback when you want the recap to feel more reflective.</p>
                  </div>
                ) : null}
              </div>
            </section>
          </section>
        </>
      ) : null}
    </section>
  );
}
