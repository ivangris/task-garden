# Garden Asset Plan

## Current status

The first real garden art pass now uses a curated subset of Kenney CC0 packs through the frontend asset manifest.

Current conventions:
- vendor assets live under `apps/web/public/assets/vendor/kenney/`
- semantic state-to-file mapping stays in `apps/web/src/features/garden/asset-manifest.json`
- the DOM/CSS garden renderer consumes manifest data and remains replaceable

## Ongoing guidance

- keep art assets replaceable
- keep garden rendering isolated from task persistence
- avoid hardcoding concrete asset paths in renderer components
- prefer terrain, greenery, water, rock, and natural props over settlement visuals
