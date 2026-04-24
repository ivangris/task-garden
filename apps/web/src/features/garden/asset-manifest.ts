import manifestData from "./asset-manifest.json";

export type GardenAssetSprite = {
  src: string;
  width: number;
  height: number;
  offsetX?: number;
  offsetY?: number;
};

export type TerrainVisualKey = keyof typeof manifestData.terrain;
export type PlantVisualKey = keyof typeof manifestData.plants;
export type DecorationVisualKey = keyof typeof manifestData.decorations;

export type TerrainVisual = {
  label: string;
  accentClass: string;
  asset?: GardenAssetSprite;
};

export type PlantVisual = {
  label: string;
  icon: string;
  className: string;
  asset?: GardenAssetSprite;
};

export type DecorationVisual = {
  label: string;
  icon: string;
  className: string;
  asset?: GardenAssetSprite;
};

export const terrainManifest: Record<TerrainVisualKey, TerrainVisual> = manifestData.terrain;
export const plantManifest: Record<PlantVisualKey, PlantVisual> = manifestData.plants;
export const decorationManifest: Record<DecorationVisualKey, DecorationVisual> = manifestData.decorations;
