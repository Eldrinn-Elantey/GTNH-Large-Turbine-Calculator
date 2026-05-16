import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk

CARD_BG = "#111827"
RESULT_LABEL_COLOR = "#6b7280"
GREEN = "#4ade80"
YELLOW = "#facc15"
PURPLE = "#c084fc"
ORANGE = "#fb923c"
CYAN = "#00d4ff"


class ResultRow(ctk.CTkFrame):
    """One label=value row inside a turbine card."""
    def __init__(self, master, label: str, value_color: str = GREEN, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._label = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=11),
                                   text_color=RESULT_LABEL_COLOR, anchor="w")
        self._label.pack(side="left", padx=(0, 8))
        self._value = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=11, weight="bold"),
                                   text_color=value_color, anchor="e")
        self._value.pack(side="right")

    def set(self, text: str):
        self._value.configure(text=text)


class ToggleButton(ctk.CTkFrame):
    """Two-option toggle (e.g. Tight/Loose, Optimal/Manual)."""
    def __init__(self, master, options: list[str], command=None, **kwargs):
        super().__init__(master, fg_color="#1f2937", corner_radius=6, **kwargs)
        self._choices = options
        self._command = command
        self._selected = options[0]
        self._buttons: dict[str, ctk.CTkButton] = {}
        for opt in options:
            btn = ctk.CTkButton(
                self, text=opt, width=64, height=26,
                font=ctk.CTkFont(size=10),
                fg_color="transparent", hover_color="#374151",
                text_color="#6b7280", corner_radius=4,
                command=lambda o=opt: self._select(o),
            )
            btn.pack(side="left", padx=2, pady=2)
            self._buttons[opt] = btn
        self._select(options[0], notify=False)

    def _select(self, opt: str, notify: bool = True):
        self._selected = opt
        for o, btn in self._buttons.items():
            if o == opt:
                btn.configure(fg_color="#1e40af", text_color="#93c5fd")
            else:
                btn.configure(fg_color="transparent", text_color="#6b7280")
        if notify and self._command:
            self._command(opt)

    def get(self) -> str:
        return self._selected

    def set(self, opt: str):
        self._select(opt, notify=False)


class LabeledDropdown(ctk.CTkFrame):
    """Label + CTkComboBox stacked vertically."""
    def __init__(self, master, label: str, values: list[str], command=None, width=160, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=9),
                     text_color="#9ca3af").pack(anchor="w")
        self._combo = ctk.CTkComboBox(
            self, values=values, width=width, height=28,
            font=ctk.CTkFont(size=10),
            fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937",
            text_color=CYAN,
            command=command,
        )
        self._combo.pack(anchor="w", pady=(2, 0))
        if values:
            self._combo.set(values[0])

    def get(self) -> str:
        return self._combo.get()

    def set(self, val: str):
        self._combo.set(val)


class TurbineCard(ctk.CTkFrame):
    """Card for one turbine with inputs and result rows."""
    def __init__(self, master, title: str, accent_color: str, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, **kwargs)
        self.configure(border_width=0)
        self._strip = ctk.CTkFrame(self, height=3, fg_color=accent_color, corner_radius=0)
        self._strip.pack(fill="x")
        self._title = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=11, weight="bold"),
                                    text_color=accent_color, anchor="w")
        self._title.pack(anchor="w", padx=10, pady=(8, 4))
        self._inputs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._inputs_frame.pack(fill="x", padx=10, pady=4)
        self._sep = ctk.CTkFrame(self, height=1, fg_color="#1f2937")
        self._sep.pack(fill="x", padx=10, pady=4)
        self._results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._results_frame.pack(fill="x", padx=10, pady=(0, 10))

    @property
    def inputs(self) -> ctk.CTkFrame:
        return self._inputs_frame

    @property
    def results(self) -> ctk.CTkFrame:
        return self._results_frame


class SearchableTable(ctk.CTkFrame):
    """Searchable table backed by ttk.Treeview for fast rendering."""

    _STYLE_INIT = False

    def __init__(self, master, columns: list[tuple[str, int]], **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._columns = columns
        self._all_rows: list[list[str]] = []
        self._init_style()

        # Search bar
        search_bar = ctk.CTkFrame(self, fg_color="#111827")
        search_bar.pack(fill="x", padx=0, pady=(0, 1))
        ctk.CTkLabel(search_bar, text="🔍", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 4))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        entry = ctk.CTkEntry(search_bar, textvariable=self._search_var,
                             placeholder_text="Search...", height=32,
                             fg_color="#1f2937", border_color="#374151",
                             font=ctk.CTkFont(size=11))
        entry.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        # Treeview
        col_ids = [str(i) for i in range(len(columns))]
        self._tree = ttk.Treeview(self, columns=col_ids, show="headings",
                                  style="Dark.Treeview", selectmode="none")
        for i, (col_name, col_width) in enumerate(columns):
            self._tree.heading(str(i), text=col_name, anchor="w")
            self._tree.column(str(i), width=col_width, minwidth=40, stretch=False, anchor="w")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview,
                            style="Dark.Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

    @classmethod
    def _init_style(cls):
        if cls._STYLE_INIT:
            return
        cls._STYLE_INIT = True
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                        background="#0d1117", foreground="#d1d5db",
                        fieldbackground="#0d1117", rowheight=24,
                        font=("", 10), borderwidth=0)
        style.configure("Dark.Treeview.Heading",
                        background="#1f2937", foreground="#9ca3af",
                        font=("", 10, "bold"), relief="flat")
        style.map("Dark.Treeview",
                  background=[("selected", "#1e40af")],
                  foreground=[("selected", "#93c5fd")])
        style.configure("Dark.Vertical.TScrollbar",
                        background="#1f2937", troughcolor="#0d1117",
                        arrowcolor="#6b7280", borderwidth=0)

    def load(self, rows: list[list[str]]):
        self._all_rows = rows
        self._filter()

    def _filter(self):
        query = self._search_var.get().lower()
        self._tree.delete(*self._tree.get_children())
        for row in self._all_rows:
            if not query or any(query in str(v).lower() for v in row):
                self._tree.insert("", "end", values=row)
