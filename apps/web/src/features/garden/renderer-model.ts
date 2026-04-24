import type { CSSProperties } from "react";

import {
  decorationManifest,
  plantManifest,
  terrainManifest,
  type DecorationVisualKey,
  type GardenAssetSprite,
  type PlantVisualKey,
} from "./asset-manifest";
import type { GardenOverview, GardenTile, GardenTilesPayload } from "../../lib/types";

const TILE_WIDTH = 112;
const TILE_HEIGHT = 60;
const TILE_DEPTH = 28;
const SCENE_PADDING_X = 72;
const SCENE_PADDING_Y = 72;

type TileState = GardenTile["tile_state"];

export type GardenRenderableTile = {
  id: string;
  zoneId: string;
  zoneName: string;
  zoneKey: string;
  tileIndex: number;
  tileState: TileState;
  growthUnits: number;
  decayPoints: number;
  screenX: number;
  screenY: number;
  zIndex: number;
  terrainClassName: string;
  terrainLabel: string;
  terrainAsset: GardenAssetSprite | null;
  plant: {
    label: string;
    icon: string;
    className: string;
    asset: GardenAssetSprite | null;
  } | null;
  decoration: {
    label: string;
    icon: string;
    className: string;
    asset: GardenAssetSprite | null;
  } | null;
};

export type GardenZoneLabel = {
  id: string;
  name: string;
  zoneKey: string;
  left: number;
  top: number;
};

export type GardenSceneModel = {
  width: number;
  height: number;
  stageKey: string;
  healthScore: number;
  activeTaskCount: number;
  overdueTaskCount: number;
  fountainState: "broken" | "restored";
  atmosphereKey: "desert" | "recovering" | "healthy" | "lush";
  tiles: GardenRenderableTile[];
  zoneLabels: GardenZoneLabel[];
};

function buildRenderPosition(coordX: number, coordY: number): Pick<GardenRenderableTile, "screenX" | "screenY" | "zIndex"> {
  const screenX = SCENE_PADDING_X + (coordX - coordY) * (TILE_WIDTH / 2) + coordY * 28;
  const screenY = SCENE_PADDING_Y + (coordX + coordY) * (TILE_HEIGHT / 2);
  return {
    screenX,
    screenY,
    zIndex: coordX + coordY,
  };
}

function coercePlantVisualKey(value: string): PlantVisualKey | null {
  return value in plantManifest ? (value as PlantVisualKey) : null;
}

function coerceDecorationVisualKey(value: string): DecorationVisualKey | null {
  return value in decorationManifest ? (value as DecorationVisualKey) : null;
}

function atmosphereForStage(stageKey: string): GardenSceneModel["atmosphereKey"] {
  if (stageKey === "lush_oasis") {
    return "lush";
  }
  if (stageKey === "healthy_garden") {
    return "healthy";
  }
  if (stageKey === "recovering_plot") {
    return "recovering";
  }
  return "desert";
}

function zoneLabelPosition(tiles: GardenRenderableTile[]): { left: number; top: number } {
  if (tiles.length === 0) {
    return { left: 0, top: 0 };
  }

  const sorted = [...tiles].sort((a, b) => a.screenX - b.screenX);
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  return {
    left: ((first.screenX + last.screenX) / 2) + 10,
    top: Math.min(...tiles.map((tile) => tile.screenY)) - 30,
  };
}

export function buildGardenSceneModel(
  overview: GardenOverview | null,
  tilesPayload: GardenTilesPayload | null,
): GardenSceneModel | null {
  if (!overview || !tilesPayload) {
    return null;
  }

  const zoneMap = new Map(tilesPayload.zones.map((zone) => [zone.id, zone]));
  const plantsByTile = new Map(tilesPayload.plants.map((plant) => [plant.garden_tile_id, plant]));
  const decorationsByTile = new Map(tilesPayload.decorations.map((decoration) => [decoration.garden_tile_id, decoration]));

  const tiles: GardenRenderableTile[] = tilesPayload.tiles.map((tile) => {
    const zone = zoneMap.get(tile.zone_id);
    const position = buildRenderPosition(tile.coord_x, tile.coord_y);
    const plant = plantsByTile.get(tile.id);
    const decoration = decorationsByTile.get(tile.id);
    const terrain = terrainManifest[tile.tile_state];
    const plantVisual = plant ? coercePlantVisualKey(plant.plant_key) : null;
    const decorationVisual = decoration ? coerceDecorationVisualKey(decoration.decoration_key) : null;

    return {
      id: tile.id,
      zoneId: tile.zone_id,
      zoneName: zone?.name ?? "Unknown zone",
      zoneKey: zone?.zone_key ?? "unknown_zone",
      tileIndex: tile.tile_index,
      tileState: tile.tile_state,
      growthUnits: tile.growth_units,
      decayPoints: tile.decay_points,
      screenX: position.screenX,
      screenY: position.screenY,
      zIndex: position.zIndex,
      terrainClassName: terrain.accentClass,
      terrainLabel: terrain.label,
      terrainAsset: terrain.asset ?? null,
      plant: plantVisual
        ? {
            label: plantManifest[plantVisual].label,
            icon: plantManifest[plantVisual].icon,
            className: plantManifest[plantVisual].className,
            asset: plantManifest[plantVisual].asset ?? null,
          }
        : null,
      decoration: decorationVisual
        ? {
            label: decorationManifest[decorationVisual].label,
            icon: decorationManifest[decorationVisual].icon,
            className: decorationManifest[decorationVisual].className,
            asset: decorationManifest[decorationVisual].asset ?? null,
          }
        : null,
    };
  });

  const zoneLabels = tilesPayload.zones.map((zone) => {
    const zoneTiles = tiles.filter((tile) => tile.zoneId === zone.id);
    const position = zoneLabelPosition(zoneTiles);
    return {
      id: zone.id,
      name: zone.name,
      zoneKey: zone.zone_key,
      left: position.left,
      top: position.top,
    };
  });

  const maxX = tiles.length === 0 ? 520 : Math.max(...tiles.map((tile) => tile.screenX)) + TILE_WIDTH + SCENE_PADDING_X;
  const maxY = tiles.length === 0 ? 340 : Math.max(...tiles.map((tile) => tile.screenY)) + TILE_HEIGHT + TILE_DEPTH + SCENE_PADDING_Y;
  const fountainState = tilesPayload.decorations.some((item) => item.decoration_key === "fountain_core") ? "restored" : "broken";

  return {
    width: maxX,
    height: maxY,
    stageKey: overview.state.stage_key,
    healthScore: overview.state.health_score,
    activeTaskCount: overview.state.active_task_count,
    overdueTaskCount: overview.state.overdue_task_count,
    fountainState,
    atmosphereKey: atmosphereForStage(overview.state.stage_key),
    tiles: tiles.sort((a, b) => a.zIndex - b.zIndex || a.tileIndex - b.tileIndex),
    zoneLabels,
  };
}

export function gardenSceneStyle(scene: GardenSceneModel): CSSProperties {
  return {
    width: `${scene.width}px`,
    height: `${scene.height}px`,
  };
}
