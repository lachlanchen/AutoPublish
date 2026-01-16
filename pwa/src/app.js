import { DEFAULT_PLATFORMS, getStoredBaseUrl, normalizeBaseUrl, storeBaseUrl } from "./state.js";
import { fetchQueue, publishZip } from "./api.js";
import { renderQueue, renderMetadata, setStatus, showToast } from "./ui.js";

const elements = {
  apiBase: document.getElementById("api-base"),
  refreshQueue: document.getElementById("refresh-queue"),
  queueList: document.getElementById("queue-list"),
  queueStatus: document.getElementById("queue-status"),
  queueSize: document.getElementById("queue-size"),
  publishingFlag: document.getElementById("publishing-flag"),
  dropzone: document.getElementById("dropzone"),
  fileInput: document.getElementById("file-input"),
  openFile: document.getElementById("open-file"),
  coverImage: document.getElementById("cover-image"),
  coverFallback: document.getElementById("cover-fallback"),
  metadataFields: document.getElementById("metadata-fields"),
  zipStatus: document.getElementById("zip-status"),
  publishButton: document.getElementById("publish-btn"),
  clearPreview: document.getElementById("clear-preview"),
  toast: document.getElementById("toast"),
};

const state = {
  baseUrl: getStoredBaseUrl(),
  selectedFile: null,
  metadata: null,
  coverUrl: null,
  platforms: { ...DEFAULT_PLATFORMS },
  testMode: false,
};

function updateCover(url) {
  if (state.coverUrl) {
    URL.revokeObjectURL(state.coverUrl);
  }
  state.coverUrl = url;
  if (url) {
    elements.coverImage.src = url;
    elements.coverImage.classList.add("visible");
    elements.coverFallback.style.display = "none";
  } else {
    elements.coverImage.src = "";
    elements.coverImage.classList.remove("visible");
    elements.coverFallback.style.display = "block";
  }
}

function resetPreview() {
  state.selectedFile = null;
  state.metadata = null;
  updateCover(null);
  renderMetadata(elements.metadataFields, null);
  setStatus(elements.zipStatus, "No file loaded", "warn");
  elements.publishButton.disabled = true;
}

async function parseZip(file) {
  if (!window.JSZip) {
    throw new Error("JSZip is not loaded.");
  }
  const zip = await window.JSZip.loadAsync(file);
  const files = Object.values(zip.files).filter((entry) => !entry.dir);

  const metadataEntry = files.find((entry) => entry.name.endsWith("_metadata.json"))
    || files.find((entry) => entry.name.endsWith("_metadata_zh.json"))
    || files.find((entry) => entry.name.endsWith(".json"));

  if (!metadataEntry) {
    throw new Error("Metadata JSON not found in ZIP.");
  }

  const metadataText = await metadataEntry.async("string");
  const metadata = JSON.parse(metadataText);

  let coverEntry = null;
  if (metadata.cover_filename) {
    coverEntry = zip.file(metadata.cover_filename) || zip.file(metadata.cover_filename.replace(/^\.\//, ""));
  }

  if (!coverEntry) {
    coverEntry = files.find((entry) => entry.name.match(/\.(png|jpe?g)$/i));
  }

  let coverUrl = null;
  if (coverEntry) {
    const blob = await coverEntry.async("blob");
    coverUrl = URL.createObjectURL(blob);
  }

  return { metadata, coverUrl };
}

async function handleZipFile(file) {
  if (!file) {
    return;
  }
  state.selectedFile = file;
  setStatus(elements.zipStatus, "Reading ZIP", "warn");
  try {
    const { metadata, coverUrl } = await parseZip(file);
    state.metadata = metadata;
    updateCover(coverUrl);
    renderMetadata(elements.metadataFields, metadata);
    setStatus(elements.zipStatus, "Ready to publish");
    elements.publishButton.disabled = false;
    showToast(elements.toast, "ZIP loaded. Metadata ready.");
  } catch (error) {
    resetPreview();
    showToast(elements.toast, error.message || "Failed to parse ZIP.", "error");
  }
}

async function refreshQueue() {
  setStatus(elements.queueStatus, "Refreshing", "warn");
  try {
    const payload = await fetchQueue(state.baseUrl);
    renderQueue(elements.queueList, payload.jobs || []);
    elements.queueSize.textContent = payload.queue_size ?? 0;
    elements.publishingFlag.textContent = payload.is_publishing ? "Yes" : "No";
    setStatus(elements.queueStatus, payload.status || "Ready");
  } catch (error) {
    setStatus(elements.queueStatus, "Offline", "warn");
    showToast(elements.toast, error.message || "Failed to fetch queue.", "error");
  }
}

async function publishCurrentZip() {
  if (!state.selectedFile) {
    return;
  }
  elements.publishButton.disabled = true;
  setStatus(elements.zipStatus, "Publishing", "warn");
  try {
    const payload = await publishZip(state.baseUrl, state.selectedFile, {
      platforms: state.platforms,
      testMode: state.testMode,
    });
    showToast(elements.toast, payload.status || "Publish queued.");
    setStatus(elements.zipStatus, "Queued");
    refreshQueue();
  } catch (error) {
    showToast(elements.toast, error.message || "Publish failed.", "error");
    setStatus(elements.zipStatus, "Publish failed", "warn");
  } finally {
    elements.publishButton.disabled = false;
  }
}

function setupPlatformToggles() {
  document.querySelectorAll("[data-platform]").forEach((input) => {
    const key = input.dataset.platform;
    if (key === "test") {
      input.checked = state.testMode;
      input.addEventListener("change", () => {
        state.testMode = input.checked;
      });
      return;
    }
    input.checked = state.platforms[key];
    input.addEventListener("change", () => {
      state.platforms[key] = input.checked;
    });
  });
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(() => {
      showToast(elements.toast, "Service worker registration failed.", "error");
    });
  }
}

function bindEvents() {
  elements.refreshQueue.addEventListener("click", refreshQueue);
  elements.fileInput.addEventListener("change", (event) => {
    const file = event.target.files[0];
    handleZipFile(file);
  });
  elements.openFile.addEventListener("click", () => elements.fileInput.click());
  elements.clearPreview.addEventListener("click", resetPreview);
  elements.publishButton.addEventListener("click", publishCurrentZip);
  elements.apiBase.addEventListener("change", () => {
    state.baseUrl = normalizeBaseUrl(elements.apiBase.value);
    storeBaseUrl(state.baseUrl);
    refreshQueue();
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    elements.dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropzone.classList.add("dragover");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    elements.dropzone.addEventListener(eventName, (event) => {
      event.preventDefault();
      elements.dropzone.classList.remove("dragover");
    });
  });
  elements.dropzone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    handleZipFile(file);
  });
}

function init() {
  elements.apiBase.value = state.baseUrl;
  setupPlatformToggles();
  resetPreview();
  refreshQueue();
  bindEvents();
  registerServiceWorker();
}

init();
