import {
  decorationManifest,
  plantManifest,
  terrainManifest,
  type DecorationVisualKey,
  type PlantVisualKey,
} from "./asset-manifest";
import type { GardenOverview, GardenTile, GardenTilesPayload } from "../../lib/types";

export const GARDEN_VIEWBOX_WIDTH = 1100;
export const GARDEN_VIEWBOX_HEIGHT = 560;
export const GARDEN_TILE_WIDTH = 170;
export const GARDEN_TILE_HEIGHT = 88;
export const GARDEN_TILE_DEPTH = 14;

const GARDEN_ORIGIN_X = 270;
const GARDEN_ORIGIN_Y = 150;

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
  plant: {
    visualKey: PlantVisualKey;
    label: string;
    className: string;
  } | null;
  decoration: {
    visualKey: DecorationVisualKey;
    label: string;
    className: string;
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
  centerpieceX: number;
  centerpieceY: number;
  tiles: GardenRenderableTile[];
  zoneLabels: GardenZoneLabel[];
};

function buildRenderPosition(coordX: number, coordY: number): Pick<GardenRenderableTile, "screenX" | "screenY" | "zIndex"> {
  return {
    screenX: GARDEN_ORIGIN_X + (coordX - coordY) * (GARDEN_TILE_WIDTH / 2),
    screenY: GARDEN_ORIGIN_Y + (coordX + coordY) * (GARDEN_TILE_HEIGHT / 2),
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

  return {
    left: tiles.reduce((sum, tile) => sum + tile.screenX, 0) / tiles.length,
    top: 82,
  };
}

function centerpiecePosition(tiles: GardenRenderableTile[]): { x: number; y: number } {
  const centerTiles = tiles.filter((tile) => tile.zoneKey === "fountain_court");
  if (centerTiles.length === 0) {
    return { x: 482, y: 280 };
  }

  return {
    x: centerTiles.reduce((sum, tile) => sum + tile.screenX, 0) / centerTiles.length,
    y: centerTiles.reduce((sum, tile) => sum + tile.screenY, 0) / centerTiles.length,
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
      plant: plantVisual
        ? {
            visualKey: plantVisual,
            label: plantManifest[plantVisual].label,
            className: plantManifest[plantVisual].className,
          }
        : null,
      decoration: decorationVisual
        ? {
            visualKey: decorationVisual,
            label: decorationManifest[decorationVisual].label,
            className: decorationManifest[decorationVisual].className,
          }
        : null,
    };
  });

  const sortedTiles = tiles.sort((a, b) => a.zIndex - b.zIndex || a.tileIndex - b.tileIndex);
  const zoneLabels = tilesPayload.zones.map((zone) => {
    const zoneTiles = sortedTiles.filter((tile) => tile.zoneId === zone.id);
    const position = zoneLabelPosition(zoneTiles);
    return {
      id: zone.id,
      name: zone.name,
      zoneKey: zone.zone_key,
      left: position.left,
      top: position.top,
    };
  });
  const centerpiece = centerpiecePosition(sortedTiles);
  const fountainState = tilesPayload.decorations.some((item) => item.decoration_key === "fountain_core")
    ? "restored"
    : "broken";

  return {
    width: GARDEN_VIEWBOX_WIDTH,
    height: GARDEN_VIEWBOX_HEIGHT,
    stageKey: overview.state.stage_key,
    healthScore: overview.state.health_score,
    activeTaskCount: overview.state.active_task_count,
    overdueTaskCount: overview.state.overdue_task_count,
    fountainState,
    atmosphereKey: atmosphereForStage(overview.state.stage_key),
    centerpieceX: centerpiece.x,
    centerpieceY: centerpiece.y,
    tiles: sortedTiles,
    zoneLabels,
  };
}
