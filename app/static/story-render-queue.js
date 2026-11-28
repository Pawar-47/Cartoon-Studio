(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const projectSelect = $("project-select");
  const planText = $("plan-json");
  const subtitleSelect = $("subtitle-mode");
  const subtitleStatus = $("subtitle-status");
  const queueButton = $("queue-render");
  const renderStatus = $("render-status");
  if (!projectSelect || !planText || !subtitleSelect || !queueButton) return;
  if (!subtitleStatus || !renderStatus) return;

  const SUBTITLE_MODES = ["urdu", "roman_urdu", "english", "none"];

  const setRenderStatus = (text) => {
    renderStatus.textContent = text;
  };
  const setSubtitleStatus = (text) => {
    subtitleStatus.textContent = text;
  };

  function readPlan() {
    try {
      const plan = JSON.parse(planText.value);
      return plan && Array.isArray(plan.scenes) ? plan : null;
    } catch (error) {
      return null;
    }
  }

  function syncSubtitleMode() {
    const plan = readPlan();
    if (!plan) {
      subtitleSelect.disabled = true;
      setSubtitleStatus("");
      return;
    }
    subtitleSelect.disabled = false;
    const stored = SUBTITLE_MODES.includes(plan.subtitle_mode)
      ? plan.subtitle_mode
      : "urdu";
    subtitleSelect.value = stored;
    setSubtitleStatus(
      plan.subtitle_mode
        ? ""
        : "The plan has no subtitle_mode; urdu dialogue text is used."
    );
  }

  function writeSubtitleMode() {
    const plan = readPlan();
    if (!plan) {
      setSubtitleStatus("Paste and validate a plan before choosing subtitles.");
      return;
    }
    plan.subtitle_mode = subtitleSelect.value;
    planText.value = JSON.stringify(plan, null, 2);
    // story.js only re-reads the textarea, so the cached validated plan has to
    // be invalidated by the same input event a paste would raise.
    planText.dispatchEvent(new Event("input", { bubbles: true }));
    setSubtitleStatus(
      subtitleSelect.value === "none"
        ? "Saved: no subtitles. Regenerate dialogue audio, then render again."
        : `Saved subtitle mode ${subtitleSelect.value}. ` +
          "Regenerate dialogue audio so the subtitle file matches, then render."
    );
  }

  function syncQueueButton() {
    queueButton.disabled = !projectSelect.value;
  }

  async function queueRender() {
    const projectId = projectSelect.value;
    if (!projectId) {
      setRenderStatus("Choose a project first.");
      return;
    }
    queueButton.disabled = true;
    setRenderStatus("Queueing the episode render…");
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/story/render/jobs`,
        { method: "POST" }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not queue the render.");
      }
      setRenderStatus(`Queued job ${data.job_id}. Opening the Episode Renderer…`);
      window.location.assign(
        `/renderer?project=${encodeURIComponent(projectId)}`
      );
    } catch (error) {
      setRenderStatus(error.message);
      queueButton.disabled = false;
    }
  }

  planText.addEventListener("input", syncSubtitleMode);
  subtitleSelect.addEventListener("change", writeSubtitleMode);
  projectSelect.addEventListener("change", syncQueueButton);
  queueButton.addEventListener("click", queueRender);

  syncSubtitleMode();
  syncQueueButton();
})();
