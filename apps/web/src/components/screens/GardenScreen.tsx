import { GardenRenderer } from "../../features/garden/GardenRenderer";
import { formatDate } from "../../features/tasks/task-utils";
import type { GardenOverview, GardenTilesPayload } from "../../lib/types";

type GardenScreenProps = {
  overview: GardenOverview | null;
  tilesPayload: GardenTilesPayload | null;
  onRecompute: () => Promise<void>;
};

export function GardenScreen({ overview, tilesPayload, onRecompute }: GardenScreenProps): JSX.Element {
  if (!overview || !tilesPayload) {
    return (
      <section className="workspace">
        <section className="surface-panel surface-panel--empty-state">
          <p className="section-eyebrow">Garden</p>
          <h4>The garden is catching up.</h4>
          <p className="empty-state">Your latest work and decay signals are being folded into the scene.</p>
        </section>
      </section>
    );
  }

  return (
    <section className="workspace">
      <div className="hero-card hero-card--compact">
        <div>
          <p className="section-eyebrow">Garden</p>
          <h3>A calm visual read of momentum, repair, and neglect.</h3>
        </div>
        <div className="hero-card__stats">
          <span className="stat-pill">{overview.state.stage_key.replace(/_/g, " ")}</span>
          <span className="stat-pill">level {overview.state.current_level}</span>
        </div>
      </div>

      <section className="screen-grid screen-grid--garden">
        <section className="surface-panel surface-panel--wide">
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Garden View</p>
              <h4>The plot shifts toward an oasis as care accumulates.</h4>
            </div>
            <button className="secondary-button" type="button" onClick={() => void onRecompute()}>
              Recompute
            </button>
          </div>
          <GardenRenderer overview={overview} tilesPayload={tilesPayload} />
        </section>
      </section>

      <section className="planning-strip">
        <article className="surface-panel planning-card planning-card--wide">
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">State</p>
              <h4>Current garden health</h4>
            </div>
          </div>
          <div className="chip-row">
            <span className="meta-chip">xp {overview.state.total_xp}</span>
            <span className="meta-chip">health {overview.state.health_score}%</span>
            <span className="meta-chip">restored {overview.state.restored_tile_count}</span>
            <span className="meta-chip">healthy {overview.state.healthy_tile_count}</span>
            <span className="meta-chip">lush {overview.state.lush_tile_count}</span>
            <span className="meta-chip">overdue {overview.state.overdue_task_count}</span>
          </div>
          <p className="muted-copy">Last recomputed {formatDate(overview.state.last_recomputed_at)}</p>
        </article>

        <article className="surface-panel planning-card">
          <div className="planning-card__meta">
            <span className="section-eyebrow">Unlocks</span>
            <span className="meta-chip">{overview.unlocks.length}</span>
          </div>
          <h4>Unlocked items</h4>
          <div className="chip-row">
            {overview.unlocks.length === 0 ? <span className="meta-chip">No unlocks yet</span> : null}
            {overview.unlocks.map((item) => (
              <span key={item.id} className="meta-chip">
                {item.unlock_key}
              </span>
            ))}
          </div>
        </article>

        <article className="surface-panel planning-card planning-card--warning">
          <div className="planning-card__meta">
            <span className="section-eyebrow">Pressure</span>
            <span className="meta-chip">{overview.recent_decay_events.length} decay events</span>
          </div>
          <h4>Recent decay vs recovery</h4>
          <p className="muted-copy">
            Overdue active work adds pressure. Finishing things repairs the space again.
          </p>
        </article>
      </section>

      <section className="screen-grid">
        <section className="surface-panel">
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Zones</p>
              <h4>Baseline layout</h4>
            </div>
          </div>
          <div className="project-list">
            {overview.zones.map((zone) => {
              const zoneTiles = tilesPayload.tiles.filter((tile) => tile.zone_id === zone.id);
              return (
                <article key={zone.id} className="project-card">
                  <div>
                    <strong>{zone.name}</strong>
                    <p>{zone.zone_key.replace(/_/g, " ")}</p>
                  </div>
                  <div className="chip-row">
                    <span className="meta-chip">{zone.tile_count} tiles</span>
                    <span className="meta-chip">
                      {zoneTiles.filter((tile) => tile.tile_state !== "desert").length} restored
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="surface-panel">
          <div className="surface-panel__header">
            <div>
              <p className="section-eyebrow">Events</p>
              <h4>Most recent signals</h4>
            </div>
          </div>
          <div className="project-list">
            {overview.recent_recovery_events.map((item) => (
              <article key={item.id} className="project-card">
                <div>
                  <strong>{item.task_title}</strong>
                  <p>{`Recovery +${item.recovery_points} / XP +${item.xp_amount}`}</p>
                </div>
              </article>
            ))}
            {overview.recent_decay_events.map((item) => (
              <article key={item.id} className="project-card">
                <div>
                  <strong>{item.task_title}</strong>
                  <p>{`Decay ${item.decay_points} / ${item.days_overdue} days overdue`}</p>
                </div>
              </article>
            ))}
            {overview.recent_recovery_events.length === 0 && overview.recent_decay_events.length === 0 ? (
              <p className="empty-state">Quiet for now. The first recoveries and repairs will start to show up here.</p>
            ) : null}
          </div>
        </section>
      </section>
    </section>
  );
}
