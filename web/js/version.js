const STORAGE_KEY = "gtnh-version";

let _versions = null;

export async function loadVersions() {
  if (_versions) return _versions;
  const res = await fetch("data/versions.json");
  _versions = await res.json();
  return _versions;
}

export function getVersion() {
  return localStorage.getItem(STORAGE_KEY) ?? null;
}

export function setVersion(id) {
  localStorage.setItem(STORAGE_KEY, id);
}

// Returns the version id to use — falls back to first available version.
export async function resolveVersion() {
  const versions = await loadVersions();
  const saved = getVersion();
  if (saved && versions.find(v => v.id === saved)) return saved;
  const fallback = versions[0].id;
  setVersion(fallback);
  return fallback;
}
