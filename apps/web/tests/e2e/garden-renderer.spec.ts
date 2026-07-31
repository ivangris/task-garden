import { expect, test } from "@playwright/test";

const now = "2026-07-30T18:00:00Z";
const zones = [
  { id: "zone-west", name: "West Patch", zone_key: "west_patch", sort_order: 1, tile_count: 4, unlocked_at: now },
  { id: "zone-center", name: "Fountain Court", zone_key: "fountain_court", sort_order: 2, tile_count: 4, unlocked_at: now },
  { id: "zone-east", name: "East Grove", zone_key: "east_grove", sort_order: 3, tile_count: 4, unlocked_at: now },
];
const tileStates = ["desert", "recovering", "healthy", "lush"] as const;
const coordinates = [
  [0, 0], [1, 0], [0, 1], [1, 1],
  [2, 0], [3, 0], [2, 1], [3, 1],
  [4, 0], [5, 0], [4, 1], [5, 1],
] as const;

const state = {
  id: "garden-primary",
  baseline_key: "neglected_desert_plot",
  stage_key: "lush_oasis",
  total_xp: 540,
  current_level: 6,
  total_growth_units: 18,
  total_decay_points: 1,
  active_task_count: 4,
  overdue_task_count: 1,
  restored_tile_count: 9,
  healthy_tile_count: 6,
  lush_tile_count: 3,
  health_score: 72,
  last_recomputed_at: now,
};

const tiles = coordinates.map(([coordX, coordY], index) => {
  const zone = zones[Math.floor(index / 4)];
  const tileState = tileStates[index % tileStates.length];
  return {
    id: `${zone.id}-tile-${index % 4}`,
    zone_id: zone.id,
    tile_index: index % 4,
    coord_x: coordX,
    coord_y: coordY,
    tile_state: tileState,
    growth_units: tileStates.indexOf(tileState),
    decay_points: tileState === "desert" ? 1 : 0,
    last_changed_at: now,
  };
});

test("garden renderer handles every terrain state and missing optional objects", async ({ page }) => {
  const overview = {
    state,
    zones,
    unlocks: [],
    recent_decay_events: [],
    recent_recovery_events: [],
  };
  const payload = {
    state,
    zones,
    tiles,
    plants: [],
    decorations: [],
  };

  await page.route("**/garden/state", (route) => route.fulfill({ json: overview }));
  await page.route("**/garden/recompute", (route) => route.fulfill({ json: overview }));
  await page.route("**/garden/tiles", (route) => route.fulfill({ json: payload }));

  await page.goto("/");
  await page.getByRole("button", { name: /^Garden/ }).click();

  await expect(page.locator(".garden-renderer--lush")).toBeVisible();
  await expect(page.locator(".garden-v2-tile")).toHaveCount(12);
  await expect(page.locator(".garden-tile--desert")).toHaveCount(3);
  await expect(page.locator(".garden-tile--recovering")).toHaveCount(3);
  await expect(page.locator(".garden-tile--healthy")).toHaveCount(3);
  await expect(page.locator(".garden-tile--lush")).toHaveCount(3);

  const eastTile = page.locator('[role="button"][aria-label^="East Grove tile 4,"]');
  await eastTile.click();
  await expect(page.locator(".garden-inspector")).toContainText("East Grove");
  await expect(page.locator(".garden-inspector")).toContainText("Lush growth");
});

test("garden renderer keeps an intentional empty state when tiles are unavailable", async ({ page }) => {
  const overview = {
    state,
    zones,
    unlocks: [],
    recent_decay_events: [],
    recent_recovery_events: [],
  };
  const payload = {
    state,
    zones,
    tiles: [],
    plants: [],
    decorations: [],
  };

  await page.route("**/garden/state", (route) => route.fulfill({ json: overview }));
  await page.route("**/garden/recompute", (route) => route.fulfill({ json: overview }));
  await page.route("**/garden/tiles", (route) => route.fulfill({ json: payload }));

  await page.goto("/");
  await page.getByRole("button", { name: /^Garden/ }).click();

  await expect(page.getByText("The garden is still taking shape.")).toBeVisible();
});
