import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { mkdir, stat, writeFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const output = path.join(root, "build", "browser-acceptance");
const dataDir = path.join(root, "build", "browser-acceptance-data");
const baseUrl = "http://127.0.0.1:8765";
await mkdir(output, { recursive: true });
await mkdir(dataDir, { recursive: true });

const log = [];
// A Foundry save generates a full skinned master character and then imports it with
// Godot before responding. Generation alone takes about a minute on a shared runner,
// and the Godot inspection that follows is allowed up to the engine's 180-second
// budget, so the browser waits long enough for both stages to finish.
const FOUNDRY_SAVE_TIMEOUT_MS = 420_000;
const record = (message) => {
  const line = new Date().toISOString() + " " + message;
  log.push(line);
  process.stdout.write(line + "\n");
};
let server;
let browser;
let failed = false;

async function setInputValue(page, selector, value) {
  await page.locator(selector).evaluate((element, nextValue) => {
    element.value = String(nextValue);
    element.dispatchEvent(new Event("input", { bubbles: true }));
    element.dispatchEvent(new Event("change", { bubbles: true }));
  }, String(value));
}


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
    throw new Error("CARTOON_STUDIO_GODOT_PATH is required for functional browser acceptance.");
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
      description: "Ephemeral Windows CI functional browser acceptance project.",
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
  const femaleOnly = process.env.FOUNDRY_ACCEPTANCE_TARGET === "female";
  // Keep the state shared across both acceptance paths. The female-only path
  // intentionally has no male record, while the full path validates both.
  let charactersResponse;
  let characters;
  let male;
  if (!femaleOnly) {
    await page.locator("#foundry-name").fill("CI Foundry Ali");
    await page.locator("#foundry-description").fill("Original male hero generated in browser CI.");
    await page.locator("#foundry-template").selectOption("cartoon-studio.stylized-adult.v1");
    await page.locator("#foundry-hair-style").selectOption("spiky");
    await setInputValue(page, "#foundry-hair-color", "#254c9b");
    await setInputValue(page, "#foundry-head-width", "0.35");
    await setInputValue(page, "#foundry-mouth-width", "0.25");
    await page.locator("#foundry-create").click();
    await page.waitForFunction(
      () => document.querySelector("#foundry-status")?.textContent?.includes("saved."),
      null,
      { timeout: FOUNDRY_SAVE_TIMEOUT_MS },
    );
    await page.locator("#model-preview").waitFor({ state: "visible", timeout: 30_000 });
    await page.waitForFunction(() => {
      const canvas = document.querySelector("#model-preview");
      return canvas && canvas.width > 0 && canvas.height > 0
        && getComputedStyle(canvas).display !== "none";
    });
    await page.waitForTimeout(1200);
    record("Male Foundry character created and Three.js preview canvas displayed.");

    charactersResponse = await request.get(
      baseUrl + "/api/projects/" + project.id + "/characters",
    );
    characters = await charactersResponse.json();
    male = characters.find((item) => item.data?.name === "CI Foundry Ali");
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

    const foundryRequests = [];
    page.on("request", (request) => {
      if (request.url().includes("/foundry-characters")) {
        foundryRequests.push({ method: request.method(), url: request.url() });
        record("[browser request] " + request.method() + " " + request.url());
      }
    });
    await page.getByRole("button", { name: "Edit Foundry recipe" }).click();
    await page.waitForFunction(
      () => document.querySelector("#foundry-create")?.textContent?.trim() === "Save Foundry changes",
      null,
      { timeout: 10_000 },
    ).catch(async () => {
      const state = await page.evaluate(() => ({
        buttonText: document.querySelector("#foundry-create")?.textContent?.trim(),
        buttonDisabled: document.querySelector("#foundry-create")?.disabled,
        project: document.querySelector("#project-select")?.value,
        name: document.querySelector("#foundry-name")?.value,
        status: document.querySelector("#foundry-status")?.textContent,
        morph: document.querySelector("#foundry-head-width")?.value,
      }));
      throw new Error("Edit Foundry recipe did not activate edit mode within 10 seconds: " + JSON.stringify(state));
    });
    const editModeState = await page.evaluate(() => ({
      buttonText: document.querySelector("#foundry-create")?.textContent?.trim(),
      buttonDisabled: document.querySelector("#foundry-create")?.disabled,
      project: document.querySelector("#project-select")?.value,
      name: document.querySelector("#foundry-name")?.value,
      status: document.querySelector("#foundry-status")?.textContent,
      morph: document.querySelector("#foundry-head-width")?.value,
    }));
    if (editModeState.buttonDisabled || editModeState.name !== "CI Foundry Ali"
        || !editModeState.project || !editModeState.status?.startsWith("Editing CI Foundry Ali")
        || editModeState.morph !== "0.35") {
      throw new Error("Foundry edit mode state is inconsistent: " + JSON.stringify(editModeState));
    }
    record("Foundry edit mode verified: " + JSON.stringify(editModeState));
    await setInputValue(page, "#foundry-head-width", "0.6");
    await page.locator("#foundry-create").click();
    // A Windows CI regeneration can take just over two minutes through Godot inspection.
    // Keep the browser alive long enough to receive the save response before checking preview parsing.
    await page.waitForFunction(
      () => document.querySelector("#foundry-status")?.textContent?.includes("saved.")
        || document.querySelector("#foundry-status")?.textContent?.includes("could not"),
      null,
      { timeout: FOUNDRY_SAVE_TIMEOUT_MS },
    );
    await page.waitForFunction(
      () => {
        const status = document.querySelector("#preview-status")?.textContent || "";
        return status.startsWith("CI Foundry Ali ·") || status.startsWith("Preview unavailable:");
      },
      null,
      { timeout: 60_000 },
    );
    const editStatus = await page.locator("#foundry-status").textContent();
    const previewStatus = await page.locator("#preview-status").textContent();
    record("Foundry edit result: " + editStatus);
    record("Foundry preview result: " + previewStatus);
    if (!editStatus?.includes("saved.") || previewStatus?.startsWith("Preview unavailable:")) {
      throw new Error("Foundry edit/preview did not finish successfully: " + editStatus
        + " | preview: " + previewStatus);
    }
    charactersResponse = await request.get(
      baseUrl + "/api/projects/" + project.id + "/characters",
    );
    characters = await charactersResponse.json();
    male = characters.find((item) => item.id === male.id);
    if (!male || male.revision !== 2 || male.data.foundry_recipe.parameters.head_width !== 0.6) {
      throw new Error("Foundry edit did not preserve character identity and revision.");
    }
    record("Saved recipe reopened, edited and persisted under the same character ID.");
  } else {
    record("Female-only acceptance mode: skipping already-passed male create/edit workflow.");
  }

  await page.locator("#foundry-name").fill("CI Foundry Sana");
  await page.locator("#foundry-description").fill("Original female hero generated in browser CI.");
  await page.locator("#foundry-template").selectOption("cartoon-studio.stylized-adult-female.v1");
  await page.locator("#foundry-hair-style").selectOption("bob");
  await setInputValue(page, "#foundry-hair-color", "#9b3c70");
  await setInputValue(page, "#foundry-head-width", "-0.2");
  await page.waitForFunction(() => {
    const button = document.querySelector("#foundry-create");
    return button && !button.disabled;
  }, null, { timeout: 30_000 });
  // The live WebGL preview continuously repaints and can prevent Playwright's
  // stability heuristic from settling even when the form button is enabled.
  await page.locator("#foundry-create").click({ force: true });
  await page.waitForFunction(
    () => document.querySelector("#foundry-status")?.textContent?.includes("saved."),
    null,
    { timeout: FOUNDRY_SAVE_TIMEOUT_MS },
  );
  await page.waitForTimeout(1200);
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
  const maleInspection = male?.data?.asset?.engine_inspection;
  const femaleInspection = female.data.asset.engine_inspection;
  if (femaleInspection.skeleton_count !== 1 || femaleInspection.morph_target_count !== 10
      || (!femaleOnly && (!maleInspection || maleInspection.skeleton_count !== 1
        || maleInspection.morph_target_count !== 10))) {
    throw new Error("Godot inspection did not confirm the expected rig and morph targets.");
  }
  record(femaleOnly
    ? "Female GLB passed the live Godot import/inspection API."
    : "Male and female GLBs both passed the live Godot import/inspection API.");

  const portraitDownloadPromise = page.waitForEvent("download", { timeout: 30_000 });
  await page.locator("#export-preview-png").click({ force: true });
  await page.waitForFunction(
    () => {
      const status = document.querySelector("#preview-status")?.textContent || "";
      return status.includes("PNG exported") || status.includes("PNG export failed");
    },
    null,
    { timeout: 30_000 },
  );
  const portraitStatus = await page.locator("#preview-status").textContent();
  if (!portraitStatus.includes("PNG exported")) {
    throw new Error("Portrait PNG export failed in the browser: " + portraitStatus);
  }
  const portraitDownload = await portraitDownloadPromise;
  const portraitPath = path.join(output, "character-portrait.png");
  await portraitDownload.saveAs(portraitPath);
  if ((await stat(portraitPath)).size < 1024) {
    throw new Error("Portrait PNG export is unexpectedly small.");
  }
  await page.waitForFunction(
    () => document.querySelector("#preview-status")?.textContent?.includes("PNG exported"),
    null,
    { timeout: 30_000 },
  );
  const turnaroundDownloadPromise = page.waitForEvent("download", { timeout: 30_000 });
  await page.locator("#export-turnaround-png").click({ force: true });
  await page.waitForFunction(
    () => {
      const status = document.querySelector("#preview-status")?.textContent || "";
      return status.includes("turnaround sheet exported") || status.includes("Turnaround export failed");
    },
    null,
    { timeout: 30_000 },
  );
  const turnaroundStatus = await page.locator("#preview-status").textContent();
  if (!turnaroundStatus.includes("turnaround sheet exported")) {
    throw new Error("Turnaround PNG export failed in the browser: " + turnaroundStatus);
  }
  const turnaroundDownload = await turnaroundDownloadPromise;
  const turnaroundPath = path.join(output, "character-turnaround.png");
  await turnaroundDownload.saveAs(turnaroundPath);
  if ((await stat(turnaroundPath)).size < 1024) {
    throw new Error("Turnaround PNG export is unexpectedly small.");
  }
  await page.waitForFunction(
    () => document.querySelector("#preview-status")?.textContent?.includes("turnaround sheet exported"),
    null,
    { timeout: 30_000 },
  );
  record("Preview portrait and four-view turnaround export actions completed.");

  if (browserErrors.length) {
    throw new Error("Browser emitted errors:\n" + browserErrors.join("\n"));
  }
  record("FUNCTIONAL BROWSER ACCEPTANCE PASSED.");
} catch (error) {
  failed = true;
  record("FUNCTIONAL BROWSER ACCEPTANCE FAILED: " + error.stack);
  throw error;
} finally {
  // Bound cleanup so a successful acceptance run cannot hang the CI job.
  const withTimeout = async (label, operation, timeoutMs = 10_000) => {
    let timer;
    try {
      await Promise.race([
        operation(),
        new Promise((_, reject) => {
          timer = setTimeout(() => reject(new Error(label + " timed out after " + timeoutMs + "ms")), timeoutMs);
          timer.unref?.();
        }),
      ]);
      record(label + " completed.");
    } catch (error) {
      record("[cleanup warning] " + label + ": " + error.message);
    } finally {
      if (timer) clearTimeout(timer);
    }
  };

  if (browser) {
    await withTimeout("Chromium shutdown", () => browser.close());
  }
  if (server && server.exitCode === null) {
    if (process.platform === "win32" && server.pid) {
      // uv launches Python as a child; terminate the complete process tree or
      // descendants can keep inherited stdout/stderr handles open indefinitely.
      const killer = spawn("taskkill", ["/PID", String(server.pid), "/T", "/F"], {
        windowsHide: true,
        stdio: "ignore",
      });
      await withTimeout("FastAPI process-tree shutdown", () => new Promise((resolve, reject) => {
        killer.once("error", reject);
        killer.once("close", (code) => code === 0 ? resolve() : reject(new Error("taskkill exited with code " + code)));
      }));
    } else {
      server.kill("SIGTERM");
      await withTimeout("FastAPI shutdown", () => new Promise((resolve) => {
        if (server.exitCode !== null || server.signalCode !== null) return resolve();
        server.once("close", resolve);
      }), 5_000);
      if (server.exitCode === null && server.signalCode === null) {
        server.kill("SIGKILL");
      }
    }
    server.stdout?.destroy();
    server.stderr?.destroy();
  }
  await writeFile(path.join(output, "browser-acceptance.log"), log.join("\n") + "\n", "utf8");
  if (failed) {
    record("Diagnostics saved to " + output);
    await writeFile(path.join(output, "browser-acceptance.log"), log.join("\n") + "\n", "utf8");
  }
}
