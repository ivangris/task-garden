import type { CSSProperties, JSX } from "react";
import { useState } from "react";

import { buildGardenSceneModel, gardenSceneStyle } from "./renderer-model";
import type { GardenAssetSprite } from "./asset-manifest";
import type { GardenOverview, GardenTilesPayload } from "../../lib/types";

type GardenRendererProps = {
  overview: GardenOverview;
  tilesPayload: GardenTilesPayload;
};

function tileStyle(left: number, top: number, zIndex: number): CSSProperties {
  return {
    left: `${left}px`,
    top: `${top}px`,
    zIndex,
  };
}

function labelStyle(left: number, top: number): CSSProperties {
  return {
    left: `${left}px`,
    top: `${top}px`,
  };
}

function spriteStyle(asset: GardenAssetSprite): CSSProperties {
  return {
    width: `${asset.width}px`,
    height: `${asset.height}px`,
    marginLeft: `${asset.offsetX ?? 0}px`,
    marginTop: `${asset.offsetY ?? 0}px`,
  };
}

type GardenSpriteProps = {
  asset: GardenAssetSprite | null;
  className: string;
  alt: string;
  fallback: JSX.Element | null;
};

function GardenSprite({ asset, className, alt, fallback }: GardenSpriteProps): JSX.Element | null {
  const [loadFailed, setLoadFailed] = useState(false);

  if (!asset || loadFailed) {
    return fallback;
  }

  return (
    <img
      className={className}
      src={asset.src}
      alt={alt}
      width={asset.width}
      height={asset.height}
      style={spriteStyle(asset)}
      onError={() => setLoadFailed(true)}
    />
  );
}

export function GardenRenderer({ overview, tilesPayload }: GardenRendererProps): JSX.Element {
  const scene = buildGardenSceneModel(overview, tilesPayload);

  if (!scene) {
    return (
      <div className="garden-renderer garden-renderer--empty">
        <p className="empty-state">Garden scene data is not available yet.</p>
      </div>
    );
  }

  return (
    <section className={`garden-renderer garden-renderer--${scene.atmosphereKey}`}>
      <div className="garden-renderer__sky" />
      <div className="garden-renderer__haze" />
      <div className="garden-renderer__meta">
        <span className="meta-chip">{scene.stageKey.replace(/_/g, " ")}</span>
        <span className="meta-chip">health {scene.healthScore}%</span>
        <span className="meta-chip">{scene.fountainState === "restored" ? "fountain restored" : "fountain broken"}</span>
      </div>

      <div className="garden-scene" style={gardenSceneStyle(scene)} aria-label="Garden scene">
        <div className="garden-scene__shadow" />
        {scene.zoneLabels.map((zone) => (
          <div key={zone.id} className="garden-zone-label" style={labelStyle(zone.left, zone.top)}>
            <span>{zone.name}</span>
          </div>
        ))}

        {scene.tiles.map((tile) => (
          <article
            key={tile.id}
            className={`garden-tile ${tile.terrainClassName}`}
            style={tileStyle(tile.screenX, tile.screenY, tile.zIndex)}
            aria-label={`${tile.zoneName} tile ${tile.tileIndex + 1}: ${tile.terrainLabel}`}
          >
            <div className="garden-tile__diamond">
              <div className="garden-tile__fallback">
                <div className="garden-tile__surface" />
                <div className="garden-tile__edge garden-tile__edge--left" />
                <div className="garden-tile__edge garden-tile__edge--right" />
              </div>
              <GardenSprite
                asset={tile.terrainAsset}
                className="garden-tile__terrain-image"
                alt={tile.terrainLabel}
                fallback={null}
              />
              {tile.decoration ? (
                <div className="garden-decoration" aria-hidden="true">
                  <GardenSprite
                    asset={tile.decoration.asset}
                    className={`garden-sprite ${tile.decoration.className}`}
                    alt={tile.decoration.label}
                    fallback={
                      <span className={`garden-sprite__fallback ${tile.decoration.className}`}>{tile.decoration.icon}</span>
                    }
                  />
                </div>
              ) : null}
              {tile.plant ? (
                <div className="garden-plant" aria-hidden="true">
                  <GardenSprite
                    asset={tile.plant.asset}
                    className={`garden-sprite ${tile.plant.className}`}
                    alt={tile.plant.label}
                    fallback={<span className={`garden-sprite__fallback ${tile.plant.className}`}>{tile.plant.icon}</span>}
                  />
                </div>
              ) : null}
              {tile.decayPoints > 0 ? <div className="garden-tile__stress" aria-hidden="true" /> : null}
            </div>
          </article>
        ))}
      </div>

      <div className="garden-renderer__footer">
        <p className="muted-copy">
          Visible decay only appears when active work is overdue. Recovery comes from completed tasks and remains stronger than decay.
        </p>
      </div>
    </section>
  );
}
