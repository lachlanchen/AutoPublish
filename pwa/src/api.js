export async function fetchQueue(baseUrl) {
  const response = await fetch(`${baseUrl}/publish/queue`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Queue request failed (${response.status})`);
  }
  return response.json();
}

export async function publishZip(baseUrl, file, options) {
  const params = new URLSearchParams({ filename: file.name });
  Object.entries(options.platforms).forEach(([key, enabled]) => {
    if (enabled) {
      params.set(`publish_${key}`, "true");
    }
  });
  if (options.testMode) {
    params.set("test", "true");
  }

  const response = await fetch(`${baseUrl}/publish?${params.toString()}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/octet-stream",
    },
    body: file,
  });

  if (!response.ok) {
    const payload = await response.text();
    throw new Error(payload || `Publish failed (${response.status})`);
  }

  return response.json();
}
