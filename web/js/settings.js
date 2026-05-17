const FONT_KEY = "gtnh-font-size";

const FONT_SIZES = {
  small:  "12px",
  medium: "13px",
  large:  "15px",
};

export function getFontSize() {
  const v = localStorage.getItem(FONT_KEY) ?? "medium";
  return FONT_SIZES[v] ? v : "medium";
}

export function setFontSize(size) {
  if (!FONT_SIZES[size]) return;
  localStorage.setItem(FONT_KEY, size);
  applyFontSize(size);
}

export function applyFontSize(size) {
  document.documentElement.style.setProperty("--font-size", FONT_SIZES[size ?? getFontSize()]);
}
