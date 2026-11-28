(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const projectSelect = $("project-select");
  const queueButton = $("queue-render");
  const refreshButton = $("refresh-jobs");
  const queueStatus = $("queue-status");
  const jobsStatus = $("jobs-status");
  const jobList = $("job-list");
  if (!projectSelect || !jobList) return;

  let timer = null;

  const setQueueStatus = (text) => {
    queueStatus.textContent = text;
  };
  const setJobsStatus = (text) => {
    jobsStatus.textContent = text;
  };

  function describeState(state) {
    return {
      queued: "Queued",
      running: "Rendering",
      completed: "Completed",
      failed: "Failed",
      cancelled: "Cancelled",
    }[state] || state;
  }

  function renderJob(job) {
    const article = document.createElement("article");
    article.className = "job-card";

    const heading = document.createElement("div");
    heading.className = "job-heading";
    const title = document.createElement("strong");
    title.textContent = `${describeState(job.state)} · ${job.operation}`;
    const updated = document.createElement("small");
    updated.textContent = `updated ${job.updated_at}`;
    heading.append(title, updated);

    const total = Number(job.total) || 0;
    const progress = Number(job.progress) || 0;
    const bar = document.createElement("progress");
    bar.max = Math.max(1, total);
    bar.value = Math.min(progress, Math.max(1, total));
    bar.textContent = `${progress}/${total}`;

    const detail = document.createElement("p");
    detail.className = "helper";
    detail.textContent =
      job.error
        ? `${progress}/${total} units · ${job.error}`
        : `${progress}/${total} units · attempt ${job.attempts}`;

    const actions = document.createElement("div");
    actions.className = "button-row";

    if (job.state === "queued" || job.state === "running") {
      const cancel = document.createElement("button");
      cancel.className = "secondary";
      cancel.textContent = "Cancel";
      cancel.addEventListener("click", async () => {
        cancel.disabled = true;
        try {
          await fetch(
            `/api/projects/${encodeURIComponent(projectSelect.value)}/jobs/` +
              `${encodeURIComponent(job.job_id)}/cancel`,
            { method: "POST" }
          );
          await refreshJobs();
        } catch (error) {
          setJobsStatus(error.message);
        }
      });
      actions.append(cancel);
    }

    if (job.state === "completed" && job.operation === "episode_render") {
      const link = document.createElement("a");
      link.className = "back-link";
      link.textContent = "Open render details →";
      link.href =
        `/story?project=${encodeURIComponent(projectSelect.value)}`;
      actions.append(link);
    }

    article.append(heading, bar, detail);
    if (actions.childElementCount) article.append(actions);
    return article;
  }

  async function refreshJobs() {
    const projectId = projectSelect.value;
    if (!projectId) return;
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/jobs?limit=20`
      );
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not list jobs.");
      const jobs = (data.jobs || []).filter(
        (job) => job.operation === "episode_render"
      );
      if (!jobs.length) {
        jobList.replaceChildren();
        const empty = document.createElement("p");
        empty.className = "helper";
        empty.textContent = "No render jobs yet. Queue one to start.";
        jobList.append(empty);
        return;
      }
      jobList.replaceChildren(...jobs.map(renderJob));
      const active = jobs.some(
        (job) => job.state === "queued" || job.state === "running"
      );
      setJobsStatus(active ? "Updating while a render is active." : "");
    } catch (error) {
      setJobsStatus(error.message);
    }
  }

  async function queueRender() {
    const projectId = projectSelect.value;
    if (!projectId) return;
    queueButton.disabled = true;
    setQueueStatus("Queueing the episode render…");
    try {
      const response = await fetch(
        `/api/projects/${encodeURIComponent(projectId)}/story/render/jobs`,
        { method: "POST" }
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Could not queue the render.");
      }
      setQueueStatus(`Queued job ${data.job_id}.`);
      await refreshJobs();
    } catch (error) {
      setQueueStatus(error.message);
    } finally {
      queueButton.disabled = false;
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
        queueButton.disabled = false;
        await refreshJobs();
        timer = window.setInterval(refreshJobs, 3000);
      } else {
        setQueueStatus("Create a project on the dashboard first.");
      }
    } catch (error) {
      setQueueStatus(error.message);
    }
  }

  projectSelect.addEventListener("change", refreshJobs);
  queueButton.addEventListener("click", queueRender);
  refreshButton.addEventListener("click", refreshJobs);
  loadProjects();
})();
