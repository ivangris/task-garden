import { useState, type JSX, type KeyboardEvent } from "react";

import { GardenCenterpiece, GardenDecorationGlyph, GardenPlantGlyph } from "./GardenGlyphs";
import {
  GARDEN_TILE_DEPTH,
  GARDEN_TILE_HEIGHT,
  GARDEN_TILE_WIDTH,
  buildGardenSceneModel,
  type GardenRenderableTile,
} from "./renderer-model";
import type { GardenOverview, GardenTilesPayload } from "../../lib/types";

type GardenRendererProps = {
  overview: GardenOverview;
  tilesPayload: GardenTilesPayload;
};

function stageLabel(stageKey: string): string {
  return stageKey.replace(/_/g, " ");
}

function tilePolygons(tile: GardenRenderableTile): {
  surface: string;
  leftEdge: string;
  rightEdge: string;
} {
  const halfWidth = GARDEN_TILE_WIDTH / 2;
  const halfHeight = GARDEN_TILE_HEIGHT / 2;
  const { screenX: x, screenY: y } = tile;

  return {
    surface: `${x},${y - halfHeight} ${x + halfWidth},${y} ${x},${y + halfHeight} ${x - halfWidth},${y}`,
    leftEdge: `${x - halfWidth},${y} ${x},${y + halfHeight} ${x},${y + halfHeight + GARDEN_TILE_DEPTH} ${x - halfWidth},${y + GARDEN_TILE_DEPTH}`,
    rightEdge: `${x + halfWidth},${y} ${x},${y + halfHeight} ${x},${y + halfHeight + GARDEN_TILE_DEPTH} ${x + halfWidth},${y + GARDEN_TILE_DEPTH}`,
  };
}

function GardenDefinitions(): JSX.Element {
  return (
    <defs>
      <linearGradient id="garden-desert-surface" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#e6b76e" />
        <stop offset="55%" stopColor="#c98748" />
        <stop offset="100%" stopColor="#a96337" />
      </linearGradient>
      <linearGradient id="garden-recovering-surface" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#c8c66f" />
        <stop offset="48%" stopColor="#8ea357" />
        <stop offset="100%" stopColor="#587341" />
      </linearGradient>
      <linearGradient id="garden-healthy-surface" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#93d67d" />
        <stop offset="50%" stopColor="#55a963" />
        <stop offset="100%" stopColor="#28744f" />
      </linearGradient>
      <linearGradient id="garden-lush-surface" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#9ce97b" />
        <stop offset="44%" stopColor="#39b76b" />
        <stop offset="100%" stopColor="#126d4e" />
      </linearGradient>
      <radialGradient id="garden-scene-glow" cx="38%" cy="40%" r="64%">
        <stop offset="0%" stopColor="#c8f5aa" stopOpacity=".26" />
        <stop offset="58%" stopColor="#5cc59d" stopOpacity=".08" />
        <stop offset="100%" stopColor="#071b1b" stopOpacity="0" />
      </radialGradient>
      <radialGradient id="garden-sand-glow" cx="42%" cy="36%" r="68%">
        <stop offset="0%" stopColor="#ffd98b" stopOpacity=".24" />
        <stop offset="100%" stopColor="#321f12" stopOpacity="0" />
      </radialGradient>
      <filter id="garden-soft-shadow" x="-30%" y="-30%" width="160%" height="180%">
        <feDropShadow dx="0" dy="18" stdDeviation="16" floodColor="#06100e" floodOpacity=".42" />
      </filter>
      <filter id="garden-tile-shadow" x="-20%" y="-30%" width="140%" height="170%">
        <feDropShadow dx="0" dy="6" stdDeviation="5" floodColor="#07120f" floodOpacity=".34" />
      </filter>
    </defs>
  );
}

function handleTileKeyDown(event: KeyboardEvent<SVGGElement>, onSelect: () => void): void {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    onSelect();
  }
}

export function GardenRenderer({ overview, tilesPayload }: GardenRendererProps): JSX.Element {
  const scene = buildGardenSceneModel(overview, tilesPayload);
  const [selectedTileId, setSelectedTileId] = useState<string | null>(null);

  if (!scene || scene.tiles.length === 0) {
    return (
      <div className="garden-renderer garden-renderer--empty">
        <p className="empty-state">The garden is still taking shape.</p>
      </div>
    );
  }

  const selectedTile =
    scene.tiles.find((tile) => tile.id === selectedTileId) ??
    [...scene.tiles].sort((a, b) => b.growthUnits - a.growthUnits || a.tileIndex - b.tileIndex)[0];
  const centerpieceIsRestored = scene.fountainState === "restored";

  return (
    <section
      className={`garden-renderer garden-renderer--${scene.atmosphereKey}`}
      aria-label={`${stageLabel(scene.stageKey)}, ${scene.healthScore}% healthy`}
    >
      <div className="garden-renderer__orb garden-renderer__orb--sun" aria-hidden="true" />
      <div className="garden-renderer__orb garden-renderer__orb--mist" aria-hidden="true" />
      <div className="garden-renderer__health">
        <span className="garden-renderer__health-ring" style={{ "--garden-health": `${scene.healthScore * 3.6}deg` } as React.CSSProperties}>
          <strong>{scene.healthScore}</strong>
          <small>%</small>
        </span>
        <span>garden health</span>
      </div>

      <svg
        className="garden-scene"
        viewBox={`0 0 ${scene.width} ${scene.height}`}
        role="img"
        aria-label="Interactive garden map"
        preserveAspectRatio="xMidYMid meet"
      >
        <GardenDefinitions />
        <rect width={scene.width} height={scene.height} rx="36" className="garden-scene__backdrop" />
        <ellipse cx="410" cy="330" rx="410" ry="190" className="garden-scene__aura" />
        <ellipse cx="410" cy="455" rx="350" ry="58" className="garden-scene__ground-shadow" />
        <path
          d="M78 292 C95 176 245 90 409 92 C602 96 799 219 824 360 C847 486 711 501 501 490 C302 480 55 444 78 292Z"
          className="garden-scene__island"
          filter="url(#garden-soft-shadow)"
        />
        <path
          d="M111 304 C133 206 261 128 414 129 C584 132 755 230 786 350 C807 430 697 457 510 451 C323 445 91 413 111 304Z"
          className="garden-scene__island-highlight"
        />

        <g className="garden-scene__atmosphere" aria-hidden="true">
          <circle cx="164" cy="183" r="4" />
          <circle cx="226" cy="126" r="3" />
          <circle cx="732" cy="285" r="3.5" />
          <circle cx="792" cy="336" r="2.5" />
          <path d="M132 387 C228 409 307 403 385 390" />
          <path d="M568 134 C647 149 717 191 758 244" />
        </g>

        <g className="garden-scene__tiles">
          {scene.tiles.map((tile) => {
            const polygons = tilePolygons(tile);
            const isSelected = selectedTile.id === tile.id;
            const selectTile = () => setSelectedTileId(tile.id);
            return (
              <g
                key={tile.id}
                className={`garden-v2-tile ${tile.terrainClassName}${isSelected ? " garden-v2-tile--selected" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={`${tile.zoneName} tile ${tile.tileIndex + 1}, ${tile.terrainLabel}, ${tile.growthUnits} growth`}
                aria-pressed={isSelected}
                onClick={selectTile}
                onFocus={selectTile}
                onKeyDown={(event) => handleTileKeyDown(event, selectTile)}
              >
                <polygon points={polygons.leftEdge} className="garden-v2-tile__edge garden-v2-tile__edge--left" />
                <polygon points={polygons.rightEdge} className="garden-v2-tile__edge garden-v2-tile__edge--right" />
                <polygon points={polygons.surface} className="garden-v2-tile__surface" filter="url(#garden-tile-shadow)" />
                <ellipse
                  cx={tile.screenX - 20}
                  cy={tile.screenY - 4}
                  rx="31"
                  ry="12"
                  className="garden-v2-tile__soft-patch"
                />
                {tile.tileState === "desert" || tile.decayPoints > 0 ? (
                  <path
                    d={`M${tile.screenX - 27} ${tile.screenY - 5} l15 7 l9 -12 l16 7 l13 -9`}
                    className="garden-v2-tile__crack"
                  />
                ) : null}
                {tile.tileState === "lush" ? (
                  <g className="garden-v2-tile__blooms" aria-hidden="true">
                    <circle cx={tile.screenX + 30} cy={tile.screenY - 10} r="3" />
                    <circle cx={tile.screenX + 42} cy={tile.screenY + 1} r="2.4" />
                    <circle cx={tile.screenX + 20} cy={tile.screenY + 8} r="2.2" />
                  </g>
                ) : null}
                {tile.decoration ? (
                  <GardenDecorationGlyph
                    visualKey={tile.decoration.visualKey}
                    x={tile.screenX}
                    y={tile.screenY - 8}
                  />
                ) : null}
                {tile.plant ? (
                  <GardenPlantGlyph visualKey={tile.plant.visualKey} x={tile.screenX} y={tile.screenY - 10} />
                ) : null}
              </g>
            );
          })}
        </g>

        {scene.zoneLabels.map((zone) => (
          <g key={zone.id} className="garden-zone-marker" transform={`translate(${zone.left} ${zone.top})`}>
            <line x1="0" y1="10" x2="0" y2="29" />
            <text textAnchor="middle">{zone.name}</text>
          </g>
        ))}

        <GardenCenterpiece
          x={scene.centerpieceX}
          y={scene.centerpieceY}
          restored={centerpieceIsRestored}
        />
      </svg>

      <aside className="garden-inspector" aria-live="polite">
        <span className="section-eyebrow">{selectedTile.zoneName}</span>
        <strong>{selectedTile.terrainLabel}</strong>
        <div className="garden-inspector__growth" aria-label={`${selectedTile.growthUnits} of 3 growth stages`}>
          {[1, 2, 3].map((unit) => (
            <i key={unit} className={unit <= selectedTile.growthUnits ? "is-filled" : ""} />
          ))}
        </div>
        <p>
          {selectedTile.decayPoints > 0
            ? `${selectedTile.decayPoints} repair point${selectedTile.decayPoints === 1 ? "" : "s"} waiting`
            : selectedTile.growthUnits === 0
              ? "Ready for its first growth"
              : `${selectedTile.growthUnits} growth ${selectedTile.growthUnits === 1 ? "stage" : "stages"} restored`}
        </p>
        {selectedTile.plant ? <span className="garden-inspector__feature">{selectedTile.plant.label}</span> : null}
        {selectedTile.decoration && selectedTile.decoration.visualKey !== "fountain_core" ? (
          <span className="garden-inspector__feature">{selectedTile.decoration.label}</span>
        ) : null}
      </aside>

      <div className="garden-renderer__status">
        <span>
          <i className={`garden-status-dot garden-status-dot--${scene.atmosphereKey}`} />
          {stageLabel(scene.stageKey)}
        </span>
        <span>{centerpieceIsRestored ? "water flowing" : "fountain resting"}</span>
        {scene.overdueTaskCount > 0 ? <span>{scene.overdueTaskCount} areas need care</span> : <span>garden settled</span>}
      </div>
    </section>
  );
}
