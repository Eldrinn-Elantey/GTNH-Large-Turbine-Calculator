/**
 * SortableTable — renders a searchable, sortable HTML table into a container element.
 *
 * Usage:
 *   const t = new SortableTable(containerEl, columns, rows);
 *   t.render();
 *
 * columns: Array of { key: string, label: string, numeric: boolean, width?: string }
 * rows: Array of objects with keys matching column.key values
 */
export class SortableTable {
  constructor(container, columns, rows) {
    this._container = container;
    this._columns = columns;
    this._rows = rows;
    this._filtered = [...rows];
    this._sortCol = null;
    this._sortAsc = true;
    this._query = "";
  }

  render() {
    this._container.innerHTML = "";

    // Search bar
    const searchWrap = document.createElement("div");
    searchWrap.className = "search-wrap";
    searchWrap.innerHTML = `<span style="color:#6b7280">🔍</span>`;
    const input = document.createElement("input");
    input.type = "text";
    input.className = "search-input";
    input.placeholder = "Search...";
    input.value = this._query;
    input.addEventListener("input", e => {
      this._query = e.target.value.toLowerCase();
      this._applyFilter();
      this._renderBody();
    });
    searchWrap.appendChild(input);
    this._container.appendChild(searchWrap);

    // Table wrap
    const wrap = document.createElement("div");
    wrap.className = "table-wrap";
    const table = document.createElement("table");
    table.className = "data-table";

    // Header
    const thead = document.createElement("thead");
    const hrow = document.createElement("tr");
    for (const col of this._columns) {
      const th = document.createElement("th");
      th.textContent = col.label;
      if (col.numeric) th.classList.add("numeric");
      if (col.width) th.style.width = col.width;
      const arrow = document.createElement("span");
      arrow.className = "sort-arrow";
      arrow.textContent = "↕";
      th.appendChild(arrow);
      th.addEventListener("click", () => this._sort(col.key, col.numeric, th, arrow));
      hrow.appendChild(th);
    }
    thead.appendChild(hrow);
    table.appendChild(thead);

    this._tbody = document.createElement("tbody");
    table.appendChild(this._tbody);
    wrap.appendChild(table);
    this._container.appendChild(wrap);

    this._applyFilter();
    this._renderBody();
  }

  _applyFilter() {
    if (!this._query) {
      this._filtered = [...this._rows];
    } else {
      this._filtered = this._rows.filter(row =>
        this._columns.some(col => {
          const val = row[col.key];
          return val != null && String(val).toLowerCase().includes(this._query);
        })
      );
    }
    if (this._sortCol) this._doSort();
  }

  _sort(key, numeric, th, arrow) {
    if (this._sortCol === key) {
      this._sortAsc = !this._sortAsc;
    } else {
      this._sortCol = key;
      this._sortAsc = true;
    }

    // Update header styles
    this._container.querySelectorAll("th").forEach(h => {
      h.classList.remove("sorted");
      h.querySelector(".sort-arrow").textContent = "↕";
    });
    th.classList.add("sorted");
    arrow.textContent = this._sortAsc ? "↑" : "↓";

    this._doSort();
    this._renderBody();
  }

  _doSort() {
    const key = this._sortCol;
    const asc = this._sortAsc;
    this._filtered.sort((a, b) => {
      let av = a[key], bv = b[key];
      const an = parseFloat(String(av).replace(/,/g, ""));
      const bn = parseFloat(String(bv).replace(/,/g, ""));
      if (!isNaN(an) && !isNaN(bn)) {
        av = an; bv = bn;
      }
      if (av < bv) return asc ? -1 : 1;
      if (av > bv) return asc ? 1 : -1;
      return 0;
    });
  }

  /** Replace rows and re-render the body (keeps search/sort state). */
  update(rows) {
    this._rows = rows;
    this._applyFilter();
    if (this._sortCol) this._doSort();
    this._renderBody();
  }

  _renderBody() {
    this._tbody.innerHTML = "";
    for (const row of this._filtered) {
      const tr = document.createElement("tr");
      for (const col of this._columns) {
        const td = document.createElement("td");
        if (col.numeric) td.classList.add("numeric");
        td.textContent = row[col.key] ?? "—";
        tr.appendChild(td);
      }
      this._tbody.appendChild(tr);
    }
  }
}
