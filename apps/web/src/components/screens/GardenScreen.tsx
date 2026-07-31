import { useState, type JSX } from "react";
import { Droplets, Leaf, LockKeyhole, RefreshCw, Sparkles, Sprout } from "lucide-react";

import { GardenRenderer } from "../../features/garden/GardenRenderer";
import { formatDate } from "../../features/tasks/task-utils";
import type { GardenOverview, GardenTilesPayload } from "../../lib/types";

type GardenScreenProps = {
  overview: GardenOverview | null;
  tilesPayload: GardenTilesPayload | null;
  onRecompute: () => Promise<void>;
};

const stagePresentation: Record<string, { eyebrow: string; title: string; copy: string }> = {
  neglected_desert: {
    eyebrow: "Quiet beginnings",
    title: "A new oasis starts here.",
    copy: "Completed work will bring the first signs of green.",
  },
  recovering_plot: {
    eyebrow: "New growth",
    title: "The garden is waking up.",
    copy: "Early restoration is spreading across the west patch.",
  },
  healthy_garden: {
    eyebrow: "Taking root",
    title: "Your oasis is finding its rhythm.",
    copy: "Steady follow-through is turning dry ground into lasting growth.",
  },
  lush_oasis: {
    eyebrow: "In full bloom",
    title: "The garden is thriving.",
    copy: "Your accumulated work has restored the whole landscape.",
  },
};

function humanize(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function GardenScreen({ overview, tilesPayload, onRecompute }: GardenScreenProps): JSX.Element {
  const [isRefreshing, setIsRefreshing] = useState(false);

  if (!overview || !tilesPayload) {
    return (
      <section className="workspace garden-workspace">
        <section className="garden-loading">
          <Sprout aria-hidden="true" />
          <span>The garden is catching up.</span>
        </section>
      </section>
    );
  }

  const stage = stagePresentation[overview.state.stage_key] ?? stagePresentation.neglected_desert;
  const totalTiles = tilesPayload.tiles.length;
  const restoredTiles = tilesPayload.tiles.filter((tile) => tile.tile_state !== "desert").length;
  const recentEvents = [
    ...overview.recent_recovery_events.map((event) => ({
      id: event.id,
      kind: "recovery" as const,
      title: event.task_title,
      detail: `+${event.xp_amount} XP`,
      date: event.recorded_at,
    })),
    ...overview.recent_decay_events.map((event) => ({
      id: event.id,
      kind: "decay" as const,
      title: event.task_title,
      detail: `${event.decay_points} repair points`,
      date: event.recorded_at,
    })),
  ]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5);

  async function refreshGarden(): Promise<void> {
    setIsRefreshing(true);
    try {
      await onRecompute();
    } finally {
      setIsRefreshing(false);
    }
  }

  return (
    <section className="workspace garden-workspace">
      <section className="garden-v2-stage">
        <header className="garden-v2-stage__header">
          <div>
            <p className="section-eyebrow">{stage.eyebrow}</p>
            <h3>{stage.title}</h3>
            <p>{stage.copy}</p>
          </div>
          <button
            className="garden-refresh-button"
            type="button"
            onClick={() => void refreshGarden()}
            disabled={isRefreshing}
          >
            <RefreshCw className={isRefreshing ? "is-spinning" : ""} aria-hidden="true" />
            {isRefreshing ? "Refreshing" : "Refresh garden"}
          </button>
        </header>
        <GardenRenderer overview={overview} tilesPayload={tilesPayload} />
      </section>

      <section className="garden-metric-row" aria-label="Garden progress">
        <article>
          <span className="garden-metric-row__icon garden-metric-row__icon--growth">
            <Sparkles aria-hidden="true" />
          </span>
          <div>
            <small>Total XP</small>
            <strong>{overview.state.total_xp}</strong>
          </div>
        </article>
        <article>
          <span className="garden-metric-row__icon garden-metric-row__icon--level">
            <Sprout aria-hidden="true" />
          </span>
          <div>
            <small>Garden level</small>
            <strong>{overview.state.current_level}</strong>
          </div>
        </article>
        <article>
          <span className="garden-metric-row__icon garden-metric-row__icon--water">
            <Droplets aria-hidden="true" />
          </span>
          <div>
            <small>Restored</small>
            <strong>{restoredTiles} / {totalTiles}</strong>
          </div>
        </article>
        <article>
          <span className="garden-metric-row__icon garden-metric-row__icon--unlock">
            <LockKeyhole aria-hidden="true" />
          </span>
          <div>
            <small>Unlocked</small>
            <strong>{overview.unlocks.length}</strong>
          </div>
        </article>
      </section>

      <section className="garden-detail-grid">
        <section className="surface-panel garden-zone-panel">
          <div className="garden-section-heading">
            <div>
              <p className="section-eyebrow">The grounds</p>
              <h4>Restoration by area</h4>
            </div>
            <span>Updated {formatDate(overview.state.last_recomputed_at)}</span>
          </div>
          <div className="garden-zone-list">
            {overview.zones.map((zone) => {
              const zoneTiles = tilesPayload.tiles.filter((tile) => tile.zone_id === zone.id);
              const restoredCount = zoneTiles.filter((tile) => tile.tile_state !== "desert").length;
              const progress = zoneTiles.length === 0 ? 0 : Math.round((restoredCount / zoneTiles.length) * 100);
              return (
                <article key={zone.id} className="garden-zone-card">
                  <div className="garden-zone-card__topline">
                    <span className="garden-zone-card__icon"><Leaf aria-hidden="true" /></span>
                    <div>
                      <strong>{zone.name}</strong>
                      <small>{restoredCount === zoneTiles.length ? "Fully restored" : `${restoredCount} of ${zoneTiles.length} growing`}</small>
                    </div>
                    <span>{progress}%</span>
                  </div>
                  <div className="garden-zone-card__progress" aria-label={`${zone.name} ${progress}% restored`}>
                    <i style={{ width: `${progress}%` }} />
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="surface-panel garden-activity-panel">
          <div className="garden-section-heading">
            <div>
              <p className="section-eyebrow">Recent growth</p>
              <h4>What changed</h4>
            </div>
            {overview.state.overdue_task_count > 0 ? (
              <span className="garden-care-state garden-care-state--attention">
                {overview.state.overdue_task_count} need care
              </span>
            ) : (
              <span className="garden-care-state">All clear</span>
            )}
          </div>
          <div className="garden-activity-list">
            {recentEvents.map((event) => (
              <article key={event.id}>
                <span className={`garden-activity-list__marker garden-activity-list__marker--${event.kind}`} />
                <div>
                  <strong>{event.title}</strong>
                  <small>{formatDate(event.date)}</small>
                </div>
                <span>{event.detail}</span>
              </article>
            ))}
            {recentEvents.length === 0 ? (
              <div className="garden-activity-empty">
                <Sprout aria-hidden="true" />
                <p>Your next completed task will appear here.</p>
              </div>
            ) : null}
          </div>
        </section>
      </section>

      {overview.unlocks.length > 0 ? (
        <section className="garden-unlock-strip" aria-label="Garden unlocks">
          <span>In your garden</span>
          {overview.unlocks.map((unlock) => (
            <span key={unlock.id}>{humanize(unlock.unlock_key)}</span>
          ))}
        </section>
      ) : null}
    </section>
  );
}
