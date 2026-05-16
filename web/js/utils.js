export const DYNAMO_TIERS = [
  ["LV",       32],
  ["MV",       128],
  ["HV",       512],
  ["EV",       2048],
  ["IV",       8192],
  ["LuV",      32768],
  ["ZPM",      131072],
  ["UV",       524288],
  ["UHV",      2097152],
  ["UEV",      8388608],
  ["UIV",      33554432],
  ["UMV",      134217728],
  ["UXV",      536870912],
  ["MAX",      2147483648],
  ["MAX+",     8589934592],
  ["MAX++",    34359738368],
  ["MAX+++",   137438953472],
  ["MAX++++",  549755813888],
];

/**
 * Return the minimum dynamo tier name that can output >= euPerT EU/t at 1 amp.
 * @param {number} euPerT
 * @returns {string}
 */
export function findDynamoTier(euPerT) {
  for (const [name, voltage] of DYNAMO_TIERS) {
    if (voltage > euPerT) return name;
  }
  return "MAX++++";
}

/**
 * Format a number with thousands separators: 1234567 -> "1,234,567".
 * Floats are rounded to 2 decimal places if fractional.
 * @param {number} n
 * @returns {string}
 */
export function formatNumber(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  const rounded = Number.isInteger(n) ? n : Math.round(n * 100) / 100;
  return rounded.toLocaleString("en-US");
}

/**
 * Populate a <select> element with options from an array.
 * @param {HTMLSelectElement} sel
 * @param {string[]} items - option text values
 * @param {string} [selected] - which value to select by default
 */
export function populateSelect(sel, items, selected = null) {
  sel.innerHTML = "";
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item;
    opt.textContent = item;
    if (item === selected) opt.selected = true;
    sel.appendChild(opt);
  }
}
