export function renderQueue(container, jobs) {
  container.innerHTML = "";
  if (!jobs || jobs.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Queue is empty.";
    container.appendChild(empty);
    return;
  }
  jobs.forEach((job) => {
    const card = document.createElement("div");
    card.className = "queue-card";

    const title = document.createElement("div");
    title.className = "queue-title";
    title.textContent = job.filename || job.id;

    const meta = document.createElement("div");
    meta.className = "queue-meta";
    meta.textContent = `${job.status || "queued"} · ${job.platforms?.join(", ") || "no targets"}`;

    const timestamp = document.createElement("div");
    timestamp.className = "queue-meta";
    timestamp.textContent = job.created_at || "";

    card.append(title, meta, timestamp);
    container.appendChild(card);
  });
}

export function renderMetadata(container, metadata) {
  container.innerHTML = "";
  if (!metadata) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "Load a ZIP to inspect metadata JSON.";
    container.appendChild(empty);
    return;
  }

  const fields = [
    ["Title", metadata.title],
    ["Brief", metadata.brief_description],
    ["Middle", metadata.middle_description],
    ["Long", metadata.long_description],
    ["Tags", Array.isArray(metadata.tags) ? metadata.tags.join(", ") : ""],
    ["Video", metadata.video_filename],
    ["Cover", metadata.cover_filename],
  ];

  fields.forEach(([label, value]) => {
    if (!value) {
      return;
    }
    const item = document.createElement("div");
    item.className = "metadata-item";
    const title = document.createElement("strong");
    title.textContent = label;
    const body = document.createElement("div");
    body.textContent = value;
    item.append(title, body);
    container.appendChild(item);
  });
}

export function setStatus(element, text, variant = "") {
  element.textContent = text;
  element.classList.toggle("warn", variant === "warn");
}

export function showToast(toast, message, tone = "") {
  toast.textContent = message;
  toast.style.background = tone === "error" ? "#b0382d" : "#13202a";
  toast.classList.add("show");
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.classList.remove("show");
  }, 2800);
}
