import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const output = path.join(root, "build", "visual-acceptance");
const dataDir = path.join(root, "build", "visual-acceptance-data");
const baseUrl = "http://127.0.0.1:8765";
await mkdir(output, { recursive: true });
await mkdir(dataDir, { recursive: true });

const log = [];
const record = (message) => {
  const line = new Date().toISOString() + " " + message;
  log.push(line);
  process.stdout.write(line + "\n");
};
let server;
let browser;
let failed = false;

async function waitForServer() {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    if (server.exitCode !== null) {
      throw new Error("FastAPI server exited before becoming healthy.");
    }
    try {
      const response = await fetch(baseUrl + "/api/health");
      if (response.ok) return;
    } catch {
      // The app is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error("FastAPI did not become healthy within 120 seconds.");
}

async function waitForEngine(request) {
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const response = await request.get(baseUrl + "/api/engine/status");
    const status = await response.json();
    if (response.ok && status.available === true) {
      record("Godot worker ready: " + status.engine_version);
      return status;
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  throw new Error("Pinned Godot worker did not become ready.");
}

try {
  process.env.CARTOON_STUDIO_DATA = dataDir;
  if (!process.env.CARTOON_STUDIO_GODOT_PATH) {
    throw new Error("CARTOON_STUDIO_GODOT_PATH is required for visual acceptance.");
  }
  server = spawn("uv", [
    "run", "--locked", "uvicorn", "app.main:app",
    "--host", "127.0.0.1", "--port", "8765",
  ], {
    cwd: root,
    env: process.env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  server.stdout.on("data", (chunk) => record("[uvicorn] " + chunk.toString().trim()));
  server.stderr.on("data", (chunk) => record("[uvicorn] " + chunk.toString().trim()));
  server.on("error", (error) => record("[uvicorn error] " + error.message));

  await waitForServer();
  record("FastAPI health endpoint ready.");
  browser = await chromium.launch({
    headless: true,
    args: [
      "--enable-webgl",
      "--ignore-gpu-blocklist",
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader",
    ],
  });
  const context = await browser.newContext({
    viewport: { width: 1600, height: 1100 },
    deviceScaleFactor: 1,
    acceptDownloads: true,
  });
  const page = await context.newPage();
  const browserErrors = [];
  page.on("pageerror", (error) => {
    browserErrors.push("pageerror: " + error.message);
    record("[browser error] " + error.message);
  });
  page.on("console", (message) => {
    if (message.type() === "error") {
      browserErrors.push("console: " + message.text());
      record("[console error] " + message.text());
    }
  });
  page.on("requestfailed", (request) => {
    const line = "request failed: " + request.url() + " " + request.failure()?.errorText;
    browserErrors.push(line);
    record("[request] " + line);
  });

  const request = context.request;
  await waitForEngine(request);
  const projectResponse = await request.post(baseUrl + "/api/projects", {
    data: {
      name: "Phase 2 Browser Acceptance",
      description: "Ephemeral Windows CI visual acceptance project.",
    },
  });
  if (!projectResponse.ok()) {
    throw new Error("Project creation failed: " + await projectResponse.text());
  }
  const project = await projectResponse.json();
  record("Created isolated project " + project.id);

  await page.goto(baseUrl + "/characters?project=" + encodeURIComponent(project.id), {
    waitUntil: "networkidle",
  });
  await page.locator("#project-select").waitFor({ state: "visible" });
  await page.waitForFunction(
    (id) => document.querySelector("#project-select")?.value === id,
    project.id,
  );
  await page.locator("#foundry-name").fill("CI Foundry Ali");
  await page.locator("#foundry-description").fill("Original male hero generated in browser CI.");
  await page.locator("#foundry-template").selectOption("cartoon-studio.stylized-adult.v1");
  await page.locator("#foundry-hair-style").selectOption("spiky");
  await page.locator("#foundry-hair-color").fill("#254c9b");
  await page.locator("#foundry-head-width").fill("0.35");
  await page.locator("#foundry-mouth-width").fill("0.25");
  await page.locator("#foundry-create").click();
  await page.waitForFunction(
    () => document.querySelector("#foundry-status")?.textContent?.includes("saved."),
    null,
    { timeout: 120_000 },
  );
  await page.locator("#model-preview").waitFor({ state: "visible", timeout: 30_000 });
  await page.waitForFunction(() => {
    const canvas = document.querySelector("#model-preview");
    return canvas && canvas.width > 0 && canvas.height > 0
      && getComputedStyle(canvas).display !== "none";
  });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(output, "01-male-foundry-preview.png"), fullPage: true });
  record("Male Foundry character created and Three.js preview canvas displayed.");

  let charactersResponse = await request.get(
    baseUrl + "/api/projects/" + project.id + "/characters",
  );
  let characters = await charactersResponse.json();
  let male = characters.find((item) => item.data?.name === "CI Foundry Ali");
  if (!male) throw new Error("Male Foundry profile was not persisted.");
  const maleAssetResponse = await request.get(
    baseUrl + "/api/projects/" + project.id + "/character-assets/"
      + male.data.asset.relative_path.split("/").at(-1).replace(/\.glb$/i, ""),
  );
  if (!maleAssetResponse.ok() || (await maleAssetResponse.body()).length < 1000) {
    throw new Error("Male Foundry GLB could not be downloaded.");
  }
  if (male.data.foundry_recipe?.hair_style !== "spiky"
      || male.data.foundry_recipe?.hair_color !== "#254c9b") {
    throw new Error("Male hairstyle settings were not persisted.");
  }

  await page.getByRole("button", { name: "Edit Foundry recipe" }).click();
  await page.locator("#foundry-head-width").waitFor();
  if (await page.locator("#foundry-head-width").inputValue() !== "0.35") {
    throw new Error("Saved Foundry morph did not restore when editing.");
  }
  await page.locator("#foundry-head-width").fill("0.6");
  await page.locator("#foundry-create").click();
  await page.waitForFunction(
    () => document.querySelector("#foundry-status")?.textContent?.includes("saved."),
    null,
    { timeout: 120_000 },
  );
  charactersResponse = await request.get(
    baseUrl + "/api/projects/" + project.id + "/characters",
  );
  characters = await charactersResponse.json();
  male = characters.find((item) => item.id === male.id);
  if (!male || male.revision !== 2 || male.data.foundry_recipe.parameters.head_width !== 0.6) {
    throw new Error("Foundry edit did not preserve character identity and revision.");
  }
  await page.screenshot({ path: path.join(output, "02-male-foundry-edited.png"), fullPage: true });
  record("Saved recipe reopened, edited and persisted under the same character ID.");

  await page.locator("#foundry-name").fill("CI Foundry Sana");
  await page.locator("#foundry-description").fill("Original female hero generated in browser CI.");
  await page.locator("#foundry-template").selectOption("cartoon-studio.stylized-adult-female.v1");
  await page.locator("#foundry-hair-style").selectOption("bob");
  await page.locator("#foundry-hair-color").fill("#9b3c70");
  await page.locator("#foundry-head-width").fill("-0.2");
  await page.locator("#foundry-create").click();
  await page.waitForFunction(
    () => document.querySelector("#foundry-status")?.textContent?.includes("saved."),
    null,
    { timeout: 120_000 },
  );
  await page.waitForTimeout(1200);
  await page.screenshot({ path: path.join(output, "03-female-foundry-preview.png"), fullPage: true });
  charactersResponse = await request.get(
    baseUrl + "/api/projects/" + project.id + "/characters",
  );
  characters = await charactersResponse.json();
  const female = characters.find((item) => item.data?.name === "CI Foundry Sana");
  if (!female
      || female.data.foundry_recipe?.master_template_id !== "cartoon-studio.stylized-adult-female.v1"
      || female.data.foundry_recipe?.hair_style !== "bob") {
    throw new Error("Female Foundry recipe or template was not persisted.");
  }
  const maleInspection = male.data.asset.engine_inspection;
  const femaleInspection = female.data.asset.engine_inspection;
  if (maleInspection.skeleton_count !== 1 || femaleInspection.skeleton_count !== 1
      || maleInspection.morph_target_count !== 10 || femaleInspection.morph_target_count !== 10) {
    throw new Error("Godot inspection did not confirm the expected rig and morph targets.");
  }
  record("Male and female GLBs both passed the live Godot import/inspection API.");

  await page.locator("#export-preview-png").click();
  await page.waitForFunction(
    () => document.querySelector("#preview-status")?.textContent?.includes("PNG exported"),
    null,
    { timeout: 30_000 },
  );
  await page.screenshot({ path: path.join(output, "04-preview-export-ready.png"), fullPage: true });
  await page.locator("#export-turnaround-png").click();
  await page.waitForFunction(
    () => document.querySelector("#preview-status")?.textContent?.includes("turnaround sheet exported"),
    null,
    { timeout: 30_000 },
  );
  record("Preview portrait and four-view turnaround export actions completed.");

  if (browserErrors.length) {
    throw new Error("Browser emitted errors:\n" + browserErrors.join("\n"));
  }
  record("VISUAL ACCEPTANCE PASSED.");
} catch (error) {
  failed = true;
  record("VISUAL ACCEPTANCE FAILED: " + error.stack);
  throw error;
} finally {
  if (browser) await browser.close();
  if (server && server.exitCode === null) {
    server.kill();
  }
  await writeFile(path.join(output, "browser-acceptance.log"), log.join("\n") + "\n", "utf8");
  if (failed) {
    record("Diagnostics saved to " + output);
    await writeFile(path.join(output, "browser-acceptance.log"), log.join("\n") + "\n", "utf8");
  }
}
