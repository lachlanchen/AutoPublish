export const DEFAULT_PLATFORMS = {
  xhs: false,
  douyin: false,
  bilibili: false,
  shipinhao: false,
  y2b: false,
  instagram: false,
};

export function normalizeBaseUrl(value) {
  if (!value) {
    return window.location.origin;
  }
  return value.replace(/\/+$/, "");
}

export function getStoredBaseUrl() {
  const stored = window.localStorage.getItem("autopublish_base_url");
  return normalizeBaseUrl(stored || window.location.origin);
}

export function storeBaseUrl(url) {
  window.localStorage.setItem("autopublish_base_url", url);
}
