# Asset Sourcing and License Checklist

## Purpose

This document defines how Task Garden should source, review, track, and integrate visual assets for the garden renderer and related UI without creating licensing confusion later.

The goal is to keep the project:
- legally clean
- easy to maintain
- easy to credit when needed
- flexible enough to swap placeholder art for better art later

This is a practical workflow document, not legal advice.

---

## Core policy

Prefer asset sources in this order:

1. **CC0 / public-domain assets first**
2. **Attribution licenses second**, only if the art is clearly worth it
3. **Share-alike or custom licenses only with deliberate review**
4. **Do not import assets with unclear or missing license terms**

For Task Garden, the ideal outcome is to use a clean set of free assets that can ship in a public repo and a future app build without complicated obligations.

---

## Recommended source priority

### 1. Kenney — first choice
Use Kenney first whenever the style is close enough.

Why:
- Kenney states that all game assets on its asset pages are licensed **CC0 / public domain**
- commercial use is allowed
- attribution is not required
- the catalog includes useful isometric and nature/desert-adjacent categories

This makes Kenney the safest and easiest starting point for placeholder or even production-ready early assets.

### 2. OpenGameArt — second choice, filtered carefully
Use OpenGameArt when Kenney does not cover what we need.

Why:
- OpenGameArt has a large catalog
- it includes clearly labeled free/open licenses such as CC0, OGA-BY, CC-BY, and CC-BY-SA
- however, obligations vary by asset, so every pack must be checked individually

Use OpenGameArt only when:
- the license is clearly acceptable
- attribution/share-alike implications are understood
- the pack is visually consistent with the product

### 3. itch.io — selective use only
Use itch.io only after verifying the individual asset pack’s own license terms.

Why:
- itch.io is a platform, not a single-license asset source
- publishers retain ownership and are responsible for having the rights to distribute their content
- this means there is no one default “itch.io license” you can rely on

Treat itch.io packs as opt-in exceptions that require manual review.

---

## License preference order

### Preferred
- **CC0 / Public Domain**

Best for this project because:
- lowest friction
- no attribution requirement
- easiest future packaging and commercialization path

### Acceptable with tracking
- **CC-BY**
- **OGA-BY**

These are workable if:
- we are willing to maintain a credits file
- we preserve attribution correctly
- we note changes where required

### Use only deliberately
- **CC-BY-SA**
- custom creator licenses
- GPL/LGPL-style asset licenses

These may be usable, but they can create more obligations and confusion than this project needs right now.

Default rule:
if a pack is not clearly better than the best CC0 alternative, skip it.

---

## What the main licenses mean for this project

### CC0
CC0 is Creative Commons’ “No Rights Reserved” tool. Creative Commons says it allows creators to waive copyright/database interests as completely as possible so others can reuse the work for any purpose without restriction under copyright or database law. For this project, that makes CC0 the cleanest option. :contentReference[oaicite:0]{index=0}

### CC-BY
CC-BY requires attribution. Creative Commons’ summary notes that you should carefully review the full license terms and that attribution typically includes the creator name and other notices if supplied; it also requires indicating changes in the material in the situations described by the license version. :contentReference[oaicite:1]{index=1}

### OGA-BY
OpenGameArt describes OGA-BY 3.0 as a license based on CC-BY 3.0 that removes CC-BY’s restriction on technical measures preventing redistribution, and notes that Creative Commons does not endorse OGA-BY. Treat it as attribution-requiring and track it carefully. :contentReference[oaicite:2]{index=2}

### itch.io packs
itch.io’s terms make clear that publishers are responsible for the content they upload and must have the rights and permissions necessary to distribute it. In practice, that means you must inspect each asset pack’s own license rather than assuming the platform provides a universal one. :contentReference[oaicite:3]{index=3}

---

## Project rules for selecting packs

Only import a pack if all of these are true:

- the license is clearly stated on the asset page or included files
- the source URL is saved
- the creator name is saved
- the pack is visually coherent with Task Garden
- the pack fits the current renderer contract or can be adapted cleanly
- the file format is workable
- the asset does not create avoidable attribution/share-alike complexity unless the value is clearly worth it

Reject a pack if any of these are true:

- no clear license
- conflicting license statements
- unclear authorship
- the visual style fights the rest of the garden
- attribution requirements are unclear
- the pack includes mixed-license files without clear separation
- the pack would force a large visual rework for marginal benefit

---

## Required intake workflow for every asset pack

For each asset pack we consider, record:

- pack name
- creator
- source site
- source URL
- asset page date reviewed
- license type
- whether attribution is required
- whether share-alike applies
- whether modifications are planned
- whether redistribution in repo/app build is allowed
- where the files will live in the repo
- visual fit notes
- approval status

Do not skip this step, even for CC0 packs.

---

## Repo tracking files to add

Keep a dedicated asset ledger in the repo.

Recommended files:

- `docs/ASSET_SOURCING_AND_LICENSE_CHECKLIST.md`
- `docs/ASSET_LEDGER.md`
- `assets/ATTRIBUTION.md`
- `assets/LICENSES/` for copied license texts when needed

### `docs/ASSET_LEDGER.md`
This should contain one entry per imported pack with:
- pack name
- creator
- URL
- license
- files used
- attribution text to display if required
- modification notes

### `assets/ATTRIBUTION.md`
This is the human-readable credits file for assets that require attribution.

### `assets/LICENSES/`
Store license texts here for packs that require them or where keeping the original text is prudent.

---

## Minimal asset ledger template

Use a structure like this:

```md
## Pack
- Name:
- Creator:
- Source:
- URL:
- Date reviewed:
- License:
- Attribution required:
- Share-alike:
- Repo path:
- Files used:
- Modified:
- Notes:
- Approved for use by: