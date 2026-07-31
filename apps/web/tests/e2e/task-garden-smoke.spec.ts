import { expect, test, type APIRequestContext } from "@playwright/test";

test.describe.configure({ mode: "serial" });

const runId = Date.now().toString(36);
const apiBaseUrl = "http://127.0.0.1:18000";
const names = {
  alphaProject: `QA Alpha ${runId}`,
  betaProject: `QA Beta ${runId}`,
  keepProject: `QA Keep ${runId}`,
  deleteProject: `QA Delete ${runId}`,
  createdProject: `QA Created ${runId}`,
  editedProject: `QA Edited ${runId}`,
  typedNote: `Email Sam about the QA smoke run and draft the Atlas plan ${runId}`,
  manualTask: `Manual quick add ${runId}`,
  todayTask: `Today focus ${runId}`,
  weekTask: `Week focus ${runId}`,
  overdueTask: `Overdue follow-up ${runId}`,
  completedTask: `Completed proof ${runId}`,
  alphaTask: `Alpha project task ${runId}`,
  betaTask: `Beta project task ${runId}`,
  keepTask: `Keep task ${runId}`,
  deleteTask: `Delete task ${runId}`,
  backupMarkerTask: `Backup marker ${runId}`,
};

type ProjectPayload = {
  id: string;
  name: string;
};

async function createProject(request: APIRequestContext, name: string): Promise<ProjectPayload> {
  const response = await request.post(`${apiBaseUrl}/projects`, {
    data: { name, description: `${name} description` },
  });
  expect(response.ok()).toBeTruthy();
  return response.json() as Promise<ProjectPayload>;
}

async function createTask(
  request: APIRequestContext,
  title: string,
  options: { projectId?: string; dueInDays?: number; status?: string } = {},
): Promise<{ id: string; project_id: string | null }> {
  const dueDate =
    typeof options.dueInDays === "number"
      ? (() => {
          const date = new Date();
          date.setHours(12, 0, 0, 0);
          date.setDate(date.getDate() + options.dueInDays);
          return date.toISOString();
        })()
      : undefined;
  const response = await request.post(`${apiBaseUrl}/tasks`, {
    data: {
      title,
      project_id: options.projectId,
      due_date: dueDate,
      status: options.status ?? "inbox",
      priority: "medium",
      effort: "small",
      energy: "medium",
    },
  });
  expect(response.ok()).toBeTruthy();
  return response.json() as Promise<{ id: string; project_id: string | null }>;
}

test("core local workflow smoke test", async ({ page, request }) => {
  const alpha = await createProject(request, names.alphaProject);
  const beta = await createProject(request, names.betaProject);
  const keepProject = await createProject(request, names.keepProject);
  const deleteProject = await createProject(request, names.deleteProject);

  await createTask(request, names.todayTask, { dueInDays: 0 });
  await createTask(request, names.weekTask, { dueInDays: 3 });
  await createTask(request, names.overdueTask, { dueInDays: -3 });
  await createTask(request, names.alphaTask, { projectId: alpha.id, dueInDays: 1 });
  await createTask(request, names.betaTask, { projectId: beta.id, dueInDays: 1 });
  await createTask(request, names.keepTask, { projectId: keepProject.id });
  const deleteTask = await createTask(request, names.deleteTask, { projectId: deleteProject.id });
  const completedTask = await createTask(request, names.completedTask, { dueInDays: -1 });
  await request.post(`${apiBaseUrl}/tasks/${completedTask.id}/complete`);
  await request.post(`${apiBaseUrl}/garden/recompute`);

  await page.goto("/");
  await expect(page.getByRole("button", { name: /^Capture/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Tasks/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Today/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^This Week/ })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Completed/ })).toHaveCount(0);

  await page.getByPlaceholder("Speak naturally, or write a quick note.").fill(names.typedNote);
  await page.getByRole("button", { name: "Extract tasks" }).click();
  await expect(page.getByRole("heading", { name: "Suggested tasks" })).toBeVisible();
  await page.getByRole("button", { name: "Add Tasks" }).click();
  await expect(page.getByText(/added to Inbox/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Add manually" })).toBeVisible();

  await page.getByRole("button", { name: "Add manually" }).click();
  await page.getByLabel("Title").fill(names.manualTask);
  await page.getByRole("button", { name: "Create Task" }).click();
  await expect(page.getByText(names.manualTask)).toBeVisible();

  await page.getByRole("button", { name: /^Tasks/ }).click();
  const dateFilter = page.getByLabel("Date").first();
  await dateFilter.selectOption("all_active");
  await page.getByLabel("Status").first().selectOption("all");
  await expect(page.getByText(names.todayTask)).toBeVisible();
  await expect(page.getByText(names.completedTask)).toHaveCount(0);

  await dateFilter.selectOption("today");
  await expect(page.getByText(names.todayTask)).toBeVisible();

  await dateFilter.selectOption("this_week");
  await expect(page.getByText(names.weekTask)).toBeVisible();

  await dateFilter.selectOption("all_active");
  await page.getByLabel("Status").first().selectOption("overdue");
  await expect(page.getByText(names.overdueTask)).toBeVisible();

  await page.getByLabel("Status").first().selectOption("completed");
  await expect(page.getByText(names.completedTask)).toBeVisible();

  await dateFilter.selectOption("all_active");
  await page.getByLabel("Status").first().selectOption("all");
  await page.getByLabel("Project").first().selectOption({ label: names.alphaProject });
  await expect(page.getByText(names.alphaTask)).toBeVisible();
  await expect(page.getByText(names.betaTask)).toHaveCount(0);

  await page.getByRole("button", { name: /^Projects/ }).click();
  await page.getByLabel("Name").first().fill(names.createdProject);
  await page.getByLabel("Description").first().fill("Created by the smoke test.");
  await page.getByRole("button", { name: "Save Project" }).click();
  await expect(page.getByText(names.createdProject)).toBeVisible();

  const createdCard = page.locator(".project-card").filter({ hasText: names.createdProject });
  await createdCard.getByRole("button", { name: "Edit" }).click();
  const editForm = page.locator(".project-edit-form");
  await editForm.locator("input").first().fill(names.editedProject);
  await editForm.locator("textarea").first().fill("Edited by the smoke test.");
  await editForm.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText(names.editedProject)).toBeVisible();

  const keepCard = page.locator(".project-card").filter({ hasText: names.keepProject });
  await keepCard.getByRole("button", { name: "Delete" }).click();
  await keepCard.getByRole("button", { name: "Delete project" }).click();
  await expect(keepCard).toHaveCount(0);
  const keptTasks = await (await request.get(`${apiBaseUrl}/tasks`)).json();
  expect(keptTasks.items.find((task: { title: string }) => task.title === names.keepTask)?.project_id).toBeNull();

  const deleteCard = page.locator(".project-card").filter({ hasText: names.deleteProject });
  await deleteCard.getByRole("button", { name: "Delete" }).click();
  await deleteCard.getByLabel("Delete option").selectOption("delete");
  page.once("dialog", (dialog) => dialog.accept());
  await deleteCard.getByRole("button", { name: "Delete tasks too" }).click();
  await expect(deleteCard).toHaveCount(0);
  const remainingTasks = await (await request.get(`${apiBaseUrl}/tasks`)).json();
  expect(remainingTasks.items.some((task: { id: string }) => task.id === deleteTask.id)).toBe(false);

  await page.getByRole("button", { name: /^Garden/ }).click();
  await expect(page.locator(".garden-renderer")).toBeVisible();

  await page.getByRole("button", { name: /^Recaps/ }).click();
  await expect(page.getByText("Completed").first()).toBeVisible();
  await page.getByRole("button", { name: /Refresh yearly/ }).click();
  await expect(page.getByText("Garden").first()).toBeVisible();

  await page.getByRole("button", { name: /^Settings/ }).click();
  await expect(page.getByLabel("Extraction provider")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Sync readiness" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Local backups" })).toBeVisible();

  await page.getByRole("button", { name: "Create backup" }).click();
  await expect(page.getByText(/Backup created/)).toBeVisible();
  const selectedBackupName = await page.getByLabel("Available backups").inputValue();
  expect(selectedBackupName).toMatch(/^task-garden-manual-.*\.db$/);

  const backupMarker = await createTask(request, names.backupMarkerTask);
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Restore selected" }).click();
  await expect(page.getByText(/pre-restore safety backup was kept/)).toBeVisible();
  const tasksAfterRestore = await (await request.get(`${apiBaseUrl}/tasks`)).json();
  expect(tasksAfterRestore.items.some((task: { id: string }) => task.id === backupMarker.id)).toBe(false);
});
