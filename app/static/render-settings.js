(function () {
  "use strict";

  const projectSelect = document.getElementById("project-select");
  const presetSelect = document.getElementById("quality-preset");
  const status = document.getElementById("quality-status");
  if (!projectSelect || !presetSelect || !status) return;

  const setStatus = (text) => {
    status.textContent = text;
  };
  const describe = (profile) =>
    `${profile.label} — ${profile.fps} fps, ${profile.width}×${profile.height}`;

  let presetsLoaded = false;

  async function loadPresets() {
    try {
      const response = await fetch("/api/quality-presets");
      if (!response.ok) throw new Error("Could not load the render quality presets.");
      const presets = await response.json();
      presetSelect.replaceChildren(
        ...presets.map(
          (profile) =>
            new Option(describe(profile), profile.name, false, Boolean(profile.default))
        )
      );
      presetSelect.disabled = false;
      presetsLoaded = true;
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function loadSettings() {
    const projectId = projectSelect.value;
    if (!projectId) {
      setStatus("Choose a project to set its render quality.");
      return;
    }
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/settings`
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not load the project settings.");
      }
      presetSelect.value = data.settings?.quality_preset || data.quality?.name || "";
      setStatus(`Saved preset: ${describe(data.quality)}.`);
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function savePreset() {
    const projectId = projectSelect.value;
    if (!projectId || !presetSelect.value) return;
    presetSelect.disabled = true;
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/settings`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ quality_preset: presetSelect.value }),
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not save the render quality.");
      }
      setStatus(`Render quality saved: ${describe(data.quality)}.`);
    } catch (error) {
      setStatus(error.message);
    } finally {
      presetSelect.disabled = false;
    }
  }

  presetSelect.addEventListener("change", savePreset);
  projectSelect.addEventListener("change", () => {
    if (presetsLoaded) loadSettings();
  });
  loadPresets().then(loadSettings);
})();
