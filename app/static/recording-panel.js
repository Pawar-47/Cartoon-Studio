(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const projectSelect = $("project-select");
  const planText = $("plan-json");
  const lineSelect = $("recording-line");
  const fileInput = $("recording-file");
  const uploadButton = $("upload-recording");
  const status = $("recording-status");
  const results = $("recording-results");
  if (!projectSelect || !lineSelect || !fileInput || !uploadButton) return;

  let lines = [];

  const setStatus = (text) => {
    status.textContent = text;
  };

  function readPlan() {
    try {
      const plan = JSON.parse(planText.value);
      return plan && Array.isArray(plan.scenes) ? plan : null;
    } catch (error) {
      return null;
    }
  }

  function fillLines() {
    const plan = readPlan();
    if (!plan) {
      lines = [];
      lineSelect.replaceChildren(new Option("Save an episode plan first", ""));
      lineSelect.disabled = true;
      fileInput.disabled = true;
      uploadButton.disabled = true;
      return;
    }
    lines = [];
    for (const [sceneIndex, scene] of plan.scenes.entries()) {
      for (const [lineIndex, line] of (scene.dialogue || []).entries()) {
        lines.push({
          sceneId: scene.id,
          sceneIndex: sceneIndex + 1,
          lineIndex: lineIndex + 1,
          text: line.text,
          characterId: line.character_id,
        });
      }
    }
    lineSelect.replaceChildren(
      ...lines.map(
        (line, index) =>
          new Option(
            `${line.sceneId} · line ${line.lineIndex} · ${line.characterId}: ` +
              `${line.text.slice(0, 40)}`,
            String(index)
          )
      )
    );
    lineSelect.disabled = lines.length === 0;
    fileInput.disabled = lines.length === 0;
    uploadButton.disabled = lines.length === 0;
    if (!lines.length) setStatus("The plan has no dialogue lines to record.");
  }

  async function refreshRecorded() {
    const projectId = projectSelect.value;
    if (!projectId) return;
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/story/audio/recordings`
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not list recordings.");
      results.replaceChildren(
        ...(data.recordings || []).map((recording) => {
          const item = document.createElement("p");
          item.className = "helper";
          item.textContent =
            `${recording.scene_id} · line ${recording.line_index} · ` +
            `${recording.size_bytes} bytes`;
          return item;
        })
      );
      if (!(data.recordings || []).length) {
        const empty = document.createElement("p");
        empty.className = "helper";
        empty.textContent = "No recorded lines yet; TTS is used where available.";
        results.replaceChildren(empty);
      }
    } catch (error) {
      setStatus(error.message);
    }
  }

  async function uploadRecording() {
    const projectId = projectSelect.value;
    const selected = lines[Number(lineSelect.value)];
    const file = fileInput.files && fileInput.files[0];
    if (!projectId || !selected || !file) {
      setStatus("Choose a dialogue line and a WAV file first.");
      return;
    }
    uploadButton.disabled = true;
    setStatus("Uploading the recorded line…");
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/story/audio/lines/` +
          `${encodeURIComponent(selected.sceneId)}/${selected.lineIndex}`,
        {
          method: "PUT",
          headers: { "Content-Type": "audio/wav" },
          body: file,
        }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "The recorded line was rejected.");
      }
      setStatus(
        `Stored ${data.duration_seconds}s for ${data.scene_id} line ${data.line_index}.`
      );
      await refreshRecorded();
    } catch (error) {
      setStatus(error.message);
    } finally {
      uploadButton.disabled = false;
    }
  }

  planText.addEventListener("input", fillLines);
  projectSelect.addEventListener("change", refreshRecorded);
  uploadButton.addEventListener("click", uploadRecording);
  fillLines();
  refreshRecorded();
})();
