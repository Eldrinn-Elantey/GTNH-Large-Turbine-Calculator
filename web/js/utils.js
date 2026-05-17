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
 * Format dynamo hatch count: "3x EV  (1.500 A)"
 * @param {number} euPerT
 * @param {string} tierName
 * @returns {string}
 */
export function formatDynamo(euPerT, tierName) {
  const entry = DYNAMO_TIERS.find(([name]) => name === tierName);
  const voltage = entry ? entry[1] : 1;
  if (euPerT <= 0) return "0x " + tierName;
  const count = Math.ceil(euPerT / voltage);
  const amps = (euPerT / voltage).toFixed(3);
  return `${count}x ${tierName}  (${amps} A)`;
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

/**
 * Custom styled combobox: text input + filtered dropdown.
 * @param {string[]} items - full list of option strings
 * @param {function(string)} onSelect - called with selected value
 * @param {object} [opts]
 * @param {string} [opts.width] - CSS width of input (default "220px")
 * @returns {{ el: HTMLElement, setValue(v: string): void, setItems(items: string[]): void }}
 */
export function makeCombobox(items, onSelect, { width = "220px" } = {}) {
  let allItems = items;
  let activeIdx = -1;

  const wrap = document.createElement("div");
  wrap.className = "combobox";
  wrap.style.width = width;

  const input = document.createElement("input");
  input.type = "text";
  input.className = "combobox-input";
  input.autocomplete = "off";
  input.spellcheck = false;

  const dropdown = document.createElement("div");
  dropdown.className = "combobox-dropdown";

  wrap.appendChild(input);
  wrap.appendChild(dropdown);

  function filtered() {
    const q = input.value.trim().toLowerCase();
    return q ? allItems.filter(it => it.toLowerCase().includes(q)) : allItems;
  }

  function renderDropdown(list) {
    dropdown.innerHTML = "";
    activeIdx = -1;
    list.forEach((item, i) => {
      const div = document.createElement("div");
      div.className = "combobox-option";
      div.textContent = item;
      div.addEventListener("mousedown", e => {
        e.preventDefault();
        select(item);
      });
      dropdown.appendChild(div);
    });
  }

  function openDropdown() {
    const list = filtered();
    renderDropdown(list);
    dropdown.classList.add("open");
  }

  function closeDropdown() {
    dropdown.classList.remove("open");
    activeIdx = -1;
  }

  function select(value) {
    input.value = value;
    closeDropdown();
    onSelect(value);
  }

  function setActive(idx) {
    const opts = dropdown.querySelectorAll(".combobox-option");
    opts.forEach(o => o.classList.remove("active"));
    if (idx >= 0 && idx < opts.length) {
      activeIdx = idx;
      opts[idx].classList.add("active");
      opts[idx].scrollIntoView({ block: "nearest" });
    }
  }

  input.addEventListener("focus", () => { renderDropdown(allItems); dropdown.classList.add("open"); });
  input.addEventListener("input", openDropdown);

  input.addEventListener("blur", () => {
    // Restore to last valid value if input doesn't match any item
    setTimeout(() => {
      closeDropdown();
      if (!allItems.includes(input.value)) {
        const match = allItems.find(it => it.toLowerCase() === input.value.toLowerCase());
        if (match) { select(match); } else { input.value = allItems[0] ?? ""; onSelect(input.value); }
      }
    }, 150);
  });

  input.addEventListener("keydown", e => {
    const opts = dropdown.querySelectorAll(".combobox-option");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive(Math.min(activeIdx + 1, opts.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive(Math.max(activeIdx - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (activeIdx >= 0 && opts[activeIdx]) select(opts[activeIdx].textContent);
      else if (opts.length > 0) select(opts[0].textContent);
    } else if (e.key === "Escape") {
      closeDropdown();
    }
  });

  return {
    el: wrap,
    setValue(v) { input.value = v; },
    setItems(newItems) {
      allItems = newItems;
      input.value = newItems[0] ?? "";
    },
  };
}
