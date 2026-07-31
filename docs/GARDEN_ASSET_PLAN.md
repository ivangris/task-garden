# Garden Asset Plan

## Current status

Garden V2 uses a responsive SVG scene for its primary terrain, atmosphere, vegetation glyphs, and centerpiece. This creates one coherent oasis footprint while keeping every visible state deterministic from the garden API.

Current conventions:
- vendor assets live under `apps/web/public/assets/vendor/kenney/`
- semantic state-to-file mapping stays in `apps/web/src/features/garden/asset-manifest.json`
- the renderer model consumes the manifest for terrain, plant, and decoration semantics
- the curated Kenney assets remain validated and available for future sprite or fallback modes
- the renderer stays replaceable and does not compute garden rules

## Ongoing guidance

- keep art assets replaceable
- keep garden rendering isolated from task persistence
- avoid hardcoding concrete asset paths in renderer components
- prefer terrain, greenery, water, rock, and natural props over settlement visuals
- keep the 3-zone / 12-tile API footprint stable unless a later domain phase explicitly changes it
