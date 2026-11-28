(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const projectSelect = $("project-select");
  const jobSelect = $("job-select");
  const loadButton = $("load-journal");
  const refreshButton = $("refresh-diagnostics");
  const status = $("diagnostics-status");
  const journalStatus = $("journal-status");
  const dependencyList = $("dependency-list");
  const journal = $("journal");
  if (!projectSelect || !dependencyList) return;

  function line(label, value, detail) {
    const item = document.createElement("li");
    const strong = document.createElement("strong");
    strong.textContent = `${label}: `;
    const state = document.createElement("span");
    state.textContent = value;
    item.append(strong, state);
    if (detail) {
      const note = document.createElement("small");
      note.textContent = ` ${detail}`;
      item.append(note);
    }
    return item;
  }

  async function refreshDiagnostics() {
    status.textContent = "Reading diagnostics…";
    try {
      const response = await fetch("/api/diagnostics");
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Diagnostics failed.");
      const rows = [];
      rows.push(line("Application", `${data.version} · ${data.data_dir}`));
      rows.push(
        line(
          "Godot runtime",
          data.godot.available ? "available" : "not installed",
          data.godot.executable
        )
      );
      rows.push(
        line(
          "FFmpeg",
          data.ffmpeg.available
            ? `${data.ffmpeg.video_codec}`
            : "not available",
          data.ffmpeg.available ? data.ffmpeg.executable : data.ffmpeg.error
        )
      );
      rows.push(
        line(
          "Speech engine",
          data.voice.available ? "installed" : "not installed",
          data.voice.available ? data.voice.voices.join(", ") : data.voice.error
        )
      );
      rows.push(
        line(
          "Background worker",
          data.worker.running ? "running" : "idle",
          data.worker.worker_id
        )
      );
      rows.push(line("Database schema", String(data.database.schema_version)));
      const jobCounts = Object.entries(data.database.jobs || {})
        .map(([state, count]) => `${count} ${state}`)
        .join(", ");
      rows.push(line("Jobs", jobCounts || "none recorded"));
      dependencyList.replaceChildren(...rows);
      status.textContent = "Diagnostics updated.";
    } catch (error) {
      status.textContent = error.message;
    }
  }

  async function refreshJobs() {
    const projectId = projectSelect.value;
    if (!projectId) return;
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/jobs?limit=50`
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not list jobs.");
      jobSelect.replaceChildren(
        new Option("Choose a job…", ""),
        ...(data.jobs || []).map(
          (job) =>
            new Option(
              `${job.operation} · ${job.state} · ${job.updated_at}`,
              job.job_id
            )
        )
      );
      loadButton.disabled = false;
    } catch (error) {
      journalStatus.textContent = error.message;
    }
  }

  function renderJournal(job) {
    const heading = document.createElement("p");
    heading.className = "helper";
    heading.textContent = `${job.operation} · ${job.state} · ${job.progress}/${job.total} units`;
    const list = document.createElement("ol");
    list.className = "journal-list";
    for (const event of job.events || []) {
      const item = document.createElement("li");
      const text = document.createElement("code");
      text.textContent = `${event.created_at} · ${event.event_type}`;
      item.append(text);
      const detail = event.detail || {};
      if (Object.keys(detail).length) {
        const note = document.createElement("small");
        note.textContent = ` ${JSON.stringify(detail)}`;
        item.append(note);
      }
      list.append(item);
    }
    return [heading, list];
  }

  async function loadJournal() {
    const projectId = projectSelect.value;
    const jobId = jobSelect.value;
    if (!projectId || !jobId) return;
    journalStatus.textContent = "Reading the job journal…";
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/jobs/` +
          encodeURIComponent(jobId)
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not read the job.");
      journal.replaceChildren(...renderJournal(data));
      journalStatus.textContent = `Job ${data.state}.`;
    } catch (error) {
      journalStatus.textContent = error.message;
    }
  }

  async function loadProjects() {
    try {
      const response = await fetch("/api/projects");
      const projects = await response.json();
      if (!response.ok) throw new Error("Could not load projects.");
      const params = new URLSearchParams(window.location.search);
      const preferred = params.get("project");
      projectSelect.replaceChildren(
        ...projects.map((project) => new Option(project.name, project.id))
      );
      if (projects.length) {
        projectSelect.value = projects.some((p) => p.id === preferred)
          ? preferred
          : projects[0].id;
        await refreshJobs();
      }
    } catch (error) {
      status.textContent = error.message;
    }
  }

  projectSelect.addEventListener("change", refreshJobs);
  loadButton.addEventListener("click", loadJournal);
  refreshButton.addEventListener("click", refreshDiagnostics);
  refreshDiagnostics();
  loadProjects();
})();
