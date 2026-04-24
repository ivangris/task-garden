import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const manifestPath = path.join(root, "src", "features", "garden", "asset-manifest.json");
const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));

const requiredTerrain = ["desert", "recovering", "healthy", "lush"];
const requiredPlants = ["desert_sprout", "sage_clump", "rare_bloom"];
const requiredDecorations = ["moss_path", "fountain_core", "sun_arch"];

function assertKeys(sectionName, section, requiredKeys) {
  for (const key of requiredKeys) {
    if (!(key in section)) {
      throw new Error(`${sectionName} is missing required key "${key}".`);
    }
  }
}

function assertAssets(sectionName, section) {
  for (const [key, entry] of Object.entries(section)) {
    if (entry.asset?.src) {
      const assetPath = path.join(root, "public", entry.asset.src.replace(/^\//, ""));
      if (!existsSync(assetPath)) {
        throw new Error(`${sectionName}.${key} points to a missing asset: ${entry.asset.src}`);
      }
    } else if (!entry.icon && !entry.accentClass) {
      throw new Error(`${sectionName}.${key} has neither an asset nor a fallback visual.`);
    }
  }
}

assertKeys("terrain", manifest.terrain, requiredTerrain);
assertKeys("plants", manifest.plants, requiredPlants);
assertKeys("decorations", manifest.decorations, requiredDecorations);

assertAssets("terrain", manifest.terrain);
assertAssets("plants", manifest.plants);
assertAssets("decorations", manifest.decorations);

console.log("Garden asset manifest looks consistent.");
