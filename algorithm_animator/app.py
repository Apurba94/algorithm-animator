"""Algorithm Animator desktop program."""
import random
import tkinter as tk
from tkinter import messagebox, ttk

from . import algos as al
from . import appkit as ak
from .appkit import Entity, Field, entities

SCHEMA = entities(
    Entity("preset", "Saved input", "Saved inputs", "name", [
        Field("name", "Name", required=True, list_col=True, width=26),
        Field("algorithm", "Algorithm", "choice", [a.name for a in al.ALGOS], required=True, list_col=True, width=22),
        Field("data", "Input", "long", list_col=True, width=36),
        Field("notes", "Notes", "long"),
    ]),
    Entity("attempt", "Quiz result", "Quiz results", "algorithm", [
        Field("day", "Date", "date", list_col=True, width=11),
        Field("algorithm", "Algorithm", list_col=True, width=22),
        Field("correct", "Correct", "bool", list_col=True, width=8),
    ], "id DESC"),
)


def sample(store):
    store.insert("preset", name="Worst case for quick sort", algorithm="Quick sort", data="1 2 3 4 5 6 7 8 9 10",
                 notes="The last-element pivot splits badly on sorted input.")
    store.insert("preset", name="Nearly sorted", algorithm="Insertion sort", data="1 2 4 3 5 6 8 7 9")
    store.insert("preset", name="Small graph", algorithm="Dijkstra", data="0 1 4\n0 2 1\n2 1 2\n1 3 5\n2 3 8")
    for i in range(5):
        store.insert("attempt", day=ak.today(), algorithm="Merge sort" if i % 2 else "Quick sort", correct=1 if i != 2 else 0)


def build(algo, text, seed=1):
    """Run an algorithm on user text, or on generated input when the text is empty. Returns (Rec, input text)."""
    text = (text or "").strip()
    if algo.kind == "graph":
        directed = algo.name == "Topological sort"
        if text:
            return algo.run(al.parse_graph(text, directed)), text
        g = al.random_graph(seed, 8, directed)
        if directed:
            g = al.G(g.n, [(min(u, v), max(u, v), w) for u, v, w in g.edges], True)
        return algo.run(g), "\n".join("%d %d %d" % e for e in g.edges)
    if algo.kind == "grid":
        grid = [list(r) for r in text.split()] if text else al.maze(seed)
        if len({len(r) for r in grid}) != 1:
            raise ValueError("all grid rows must have the same length")
        return algo.run(grid), "\n".join("".join(r) for r in grid)
    values = al.parse_numbers(text) if text else [random.Random(seed).randint(1, 40) for _ in range(12)]
    if not values:
        raise ValueError("enter some numbers")
    if len(values) > 200:
        raise ValueError("use at most 200 numbers")
    return algo.run(values), " ".join(map(str, values))


class Stage(tk.Canvas):
    """Draws one frame of any kind."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.colors["panel"], highlightthickness=0)
        self.app, self.frame_data = app, None
        self.bind("<Configure>", lambda e: self.show(self.frame_data))

    def show(self, f):
        self.frame_data = f
        self.delete("all")
        if f:
            getattr(self, "draw_" + f["kind"])(f, max(self.winfo_width(), 200), max(self.winfo_height(), 160))

    def draw_array(self, f, w, h):
        c, s = self.app.colors, self.app.scale
        v = f["values"]
        if not v:
            return
        top, low = 40 * s, h - 54 * s
        n = len(v)
        bw = (w - 30 * s) / n
        lo = min(0, min(v))
        span = (max(v) - lo) or 1
        col = {"compare": c["warning"], "swap": c["danger"], "key": c["accent"]}
        done = set(f.get("done", []))
        win = f.get("window")
        for i, x in enumerate(v):
            x0 = 15 * s + i * bw
            bh = (low - top) * (x - lo) / span
            fill = col.get(f["marks"].get(i), c["ok"] if i in done else c["track"] if win and not win[0] <= i <= win[1] else c["muted"])
            self.create_rectangle(x0 + 1, low - bh, x0 + bw - 1, low, fill=fill, outline="")
            if bw > 16 * s:
                self.create_text(x0 + bw / 2, low + 11 * s, text=str(x), fill=c["ink"], font=(ak.FONT, 9))
        pts = {}
        for name, i in f.get("pointers", {}).items():
            pts.setdefault(i, []).append(name)
        for i, names in pts.items():
            self.create_text(15 * s + (i + 0.5) * bw, low + 28 * s, text=",".join(names), fill=c["accent"], font=(ak.FONT, 9, "bold"))
        for key, label in (("deque", "deque"), ("out", "output"), ("counts", "counts")):
            if key in f:
                self.create_text(15 * s, 14 * s + (12 * s if key == "out" else 0), anchor="w", fill=c["muted"], text="%s: %s" % (label, f[key]), font=(ak.FONT, 9))

    def draw_tree(self, f, w, h):
        c, s = self.app.colors, self.app.scale
        nodes = f["nodes"]
        if not nodes:
            return
        xs = [n["x"] for n in nodes.values()]
        depth = max(n["y"] for n in nodes.values()) + 1
        x0, x1 = min(xs), max(xs)

        def pos(n):
            px = w / 2 if x1 == x0 else 30 * s + (n["x"] - x0) / (x1 - x0) * (w - 60 * s)
            return px, 30 * s + n["y"] * (h - 60 * s) / max(1, depth)
        for n in nodes.values():
            if n["parent"] is not None and n["parent"] in nodes:
                self.create_line(*pos(n), *pos(nodes[n["parent"]]), fill=c["muted"])
        r = 15 * s
        for key, n in nodes.items():
            px, py = pos(n)
            on = key == f.get("mark")
            self.create_oval(px - r, py - r, px + r, py + r, fill=c["accent"] if on else c["sel"], outline=c["accent"])
            self.create_text(px, py, text=str(n["value"]), fill=c["accent_ink"] if on else c["sel_ink"], font=(ak.FONT, 9))

    def draw_graph(self, f, w, h):
        c, s = self.app.colors, self.app.scale
        pos = [(x * w, y * h) for x, y in al.layout_circle(f["n"])]
        tree = {tuple(sorted(e)) for e in f.get("tree", [])}
        active = tuple(sorted(f["active"])) if f.get("active") else None
        for u, v, wt in f["edges"]:
            key = tuple(sorted((u, v)))
            col, width = (c["danger"], 3 * s) if key == active else (c["ok"], 3 * s) if key in tree else (c["line"], 1.5 * s)
            self.create_line(*pos[u], *pos[v], fill=col, width=width, arrow="last" if f["directed"] else "none")
            mx, my = (pos[u][0] + pos[v][0]) / 2, (pos[u][1] + pos[v][1]) / 2
            self.create_text(mx, my, text=str(wt), fill=c["muted"], font=(ak.FONT, 9))
        r = 16 * s
        seen, frontier = f.get("seen", {}), set(f.get("frontier", []))
        labels = f.get("labels", f.get("seen", {}))
        for i, (x, y) in enumerate(pos):
            fill = c["accent"] if i == f.get("current") else c["ok"] if i in seen else c["warning"] if i in frontier else c["panel"]
            self.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline=c["muted"], width=1.5)
            self.create_text(x, y, text=str(i), fill=c["ink"] if fill == c["panel"] else "#ffffff", font=(ak.FONT, 10, "bold"))
            if i in labels:
                self.create_text(x, y + r + 9 * s, text=str(labels[i]), fill=c["ink"], font=(ak.FONT, 9))

    def draw_grid(self, f, w, h):
        c = self.app.colors
        g = f["grid"]
        rows, cols = len(g), len(g[0])
        cell = min(w / cols, h / rows)
        closed, opened, path = set(f["closed"]), set(f["open"]), set(f["path"])
        for i, row in enumerate(g):
            for j, ch in enumerate(row):
                p = (i, j)
                fill = c["ink"] if ch == "#" else c["warning"] if p in path else c["sel"] if p in closed else c["track"] if p in opened else c["panel"]
                if p == f["start"] or p == f["goal"]:
                    fill = c["accent"]
                self.create_rectangle(j * cell, i * cell, (j + 1) * cell, (i + 1) * cell, fill=fill, outline=c["line"])


class Player(ttk.Frame):
    title = "Player"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        top = ttk.Frame(self)
        top.pack(fill="x")
        self.group, self.name = tk.StringVar(value="Sorting"), tk.StringVar(value="Quick sort")
        groups = []
        for a in al.ALGOS:
            if a.group not in groups:
                groups.append(a.group)
        ak.labeled_combo(top, "Group", self.group, groups, 12, self.pick_group).pack(side="left", padx=(0, 8))
        self.name_box = ak.labeled_combo(top, "Algorithm", self.name, [], 24, self.run)
        self.name_box.pack(side="left", padx=(0, 8))
        self.entry = tk.StringVar()
        ttk.Button(top, text="New random input", command=self.randomize).pack(side="right", anchor="s")
        ttk.Button(top, text="Run my input", style="Accent.TButton", command=self.run_text).pack(side="right", anchor="s", padx=6)
        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, pady=6)
        left, right = ttk.Frame(pane), ak.panel(pane, "Pseudocode")
        pane.add(left, weight=4)
        pane.add(right, weight=2)
        pane.bind("<Map>", lambda e: pane.after_idle(lambda: pane.sashpos(0, int(pane.winfo_width() * 0.68))))
        self.stage = Stage(left, app)
        self.stage.pack(fill="both", expand=True)
        self.note = ttk.Label(left, text="", style="Muted.TLabel")
        self.note.pack(anchor="w", pady=3)
        self.code = tk.Text(right, height=9, wrap="word", relief="flat", bg=app.colors["panel"], fg=app.colors["ink"], font=(ak.MONO, 10),
                            highlightthickness=0, state="disabled")
        self.code.pack(fill="both", expand=True)
        self.code.tag_configure("cur", background=app.colors["sel"], foreground=app.colors["sel_ink"])
        self.facts = ttk.Label(right, text="", style="PanelMuted.TLabel", wraplength=int(300 * app.scale), justify="left")
        self.facts.pack(anchor="w", pady=(6, 0))
        frame, self.input = ak.make_text(right, app.colors, height=4, mono=True)
        frame.pack(fill="x", pady=(6, 0))
        bar = ttk.Frame(self)
        bar.pack(fill="x")
        for text, cmd in (("|<", self.first), ("<", self.back), ("Play", self.toggle), (">", self.forward), (">|", self.last)):
            b = ttk.Button(bar, text=text, command=cmd, width=5)
            b.pack(side="left", padx=(0, 3))
            if text == "Play":
                self.play_btn = b
        self.pos = tk.IntVar()
        self.scale_w = ttk.Scale(bar, from_=0, to=1, orient="horizontal", command=lambda v: self.seek(int(float(v))))
        self.scale_w.pack(side="left", fill="x", expand=True, padx=8)
        self.count = ttk.Label(bar, text="", style="Muted.TLabel", width=30)
        self.count.pack(side="left")
        self.speed = tk.StringVar(value="Normal")
        ttk.Combobox(bar, textvariable=self.speed, values=["Slow", "Normal", "Fast", "Very fast"], state="readonly", width=9).pack(side="left")
        self.rec, self.i, self.playing, self.seed, self._seeking = None, 0, False, 1, False
        self.pick_group()

    def pick_group(self):
        names = [a.name for a in al.ALGOS if a.group == self.group.get()]
        self.name_box.box.configure(values=names)
        if self.name.get() not in names:
            self.name.set(names[0])
        self.run()

    def run(self):
        self.load(None)

    def randomize(self):
        self.seed = random.randrange(10 ** 6)
        self.load(None)

    def run_text(self):
        self.load(ak.get_text(self.input))

    def load(self, text):
        algo = al.BY_NAME[self.name.get()]
        try:
            self.rec, used = build(algo, text, self.seed)
        except ValueError as exc:
            messagebox.showerror("Input", str(exc), parent=self)
            return
        ak.set_text(self.input, used)
        self.stop()
        ak.set_text(self.code, "\n".join("%2d  %s" % (i + 1, l) for i, l in enumerate(algo.pseudo)), readonly=True)
        self.facts.configure(text="Time: %s\nSpace: %s\n%s" % (algo.time, algo.space, algo.note))
        self.scale_w.configure(to=max(1, len(self.rec.frames) - 1))
        self.seek(0)

    def seek(self, i):
        if not self.rec or self._seeking:           # setting the slider calls this command again
            return
        self.i = max(0, min(i, len(self.rec.frames) - 1))
        f = self.rec.frames[self.i]
        self.stage.show(f)
        self.note.configure(text=f["note"])
        self.count.configure(text="Step %d of %d   compares %d   moves %d" % (self.i + 1, len(self.rec.frames), f["comps"], f["moves"]))
        self.code.tag_remove("cur", "1.0", "end")
        self.code.tag_add("cur", "%d.0" % (f["line"] + 1), "%d.0" % (f["line"] + 2))
        self._seeking = True
        self.scale_w.set(self.i)
        self._seeking = False

    def first(self):
        self.seek(0)

    def last(self):
        self.seek(len(self.rec.frames) - 1)

    def back(self):
        self.seek(self.i - 1)

    def forward(self):
        self.seek(self.i + 1)

    def toggle(self):
        self.playing = not self.playing
        self.play_btn.configure(text="Pause" if self.playing else "Play")
        if self.playing:
            if self.i >= len(self.rec.frames) - 1:
                self.seek(0)
            self.tick()

    def stop(self):
        self.playing = False
        self.play_btn.configure(text="Play")

    def tick(self):
        if not self.playing or not self.winfo_exists():
            return
        if self.i >= len(self.rec.frames) - 1:
            self.stop()
            return
        self.seek(self.i + 1)
        self.after({"Slow": 900, "Normal": 350, "Fast": 120, "Very fast": 30}[self.speed.get()], self.tick)

    def refresh(self):
        if not self.rec:
            self.run()

    def commit(self):
        self.stop()
        return True

    def open_preset(self, row):
        algo = al.BY_NAME[row["algorithm"]]
        self.group.set(algo.group)
        self.name_box.box.configure(values=[a.name for a in al.ALGOS if a.group == algo.group])
        self.name.set(algo.name)
        self.load(row["data"])


class Compare(ttk.Frame):
    title = "Compare"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        top = ttk.Frame(self)
        top.pack(fill="x")
        self.n, self.shape = tk.StringVar(value="64"), tk.StringVar(value="random")
        ak.labeled_entry(top, "Items", self.n, 8).pack(side="left", padx=(0, 8))
        ak.labeled_combo(top, "Input shape", self.shape, ["random", "sorted", "reversed", "nearly sorted", "few unique"], 14, self.go).pack(side="left")
        ttk.Button(top, text="Race the sorts", style="Accent.TButton", command=self.go).pack(side="left", padx=10, anchor="s")
        self.table = ak.Table(self, app, [("name", "Algorithm", 20), ("comps", "Comparisons", 12), ("moves", "Moves", 10), ("total", "Total work", 12)], height=8)
        self.table.pack(fill="x", pady=6)
        self.chart = tk.Canvas(self, bg=app.colors["panel"], highlightthickness=0)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", lambda e: self.draw())
        self.lines = {}

    def go(self):
        try:
            n = int(self.n.get())
        except ValueError:
            messagebox.showerror("Compare", "Items must be a whole number.", parent=self)
            return
        if not 2 <= n <= 2000:
            messagebox.showerror("Compare", "Use 2 to 2000 items.", parent=self)
            return
        rng = random.Random(1)
        rows = al.race(al.shaped(rng, n, self.shape.get()))
        rows.sort(key=lambda r: r["comps"] + r["moves"])
        self.table.fill([(r["name"], r["comps"], r["moves"], r["comps"] + r["moves"]) for r in rows])
        sizes = [max(2, n * k // 8) for k in range(1, 9)]
        self.lines = {r["name"]: al.growth(r["name"], sizes, 2, self.shape.get()) for r in rows}
        self.draw()

    def draw(self):
        c, col, s = self.chart, self.app.colors, self.app.scale
        c.delete("all")
        if not self.lines:
            return
        w, h = max(c.winfo_width(), 300), max(c.winfo_height(), 150)
        top = max(v for line in self.lines.values() for _, v in line) or 1
        xmax = max(n for line in self.lines.values() for n, _ in line)
        palette = ["#2f5fd0", "#d9480f", "#2b8a3e", "#ae3ec9", "#e67700", "#0c8599", "#868e96"]
        for k, (name, line) in enumerate(self.lines.items()):
            pts = []
            for n, v in line:
                pts += [50 * s + n / xmax * (w - 230 * s), h - 24 * s - v / top * (h - 44 * s)]
            c.create_line(*pts, fill=palette[k % 7], width=2 * s)
            c.create_text(w - 170 * s, 14 * s + k * 16 * s, anchor="w", text=name, fill=palette[k % 7], font=(ak.FONT, 9))
        c.create_text(50 * s, h - 10 * s, anchor="w", text="work against input size", fill=col["muted"], font=(ak.FONT, 9))

    def refresh(self):
        if not self.lines:
            self.go()


class Quiz(ttk.Frame):
    title = "Quiz"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        p = ak.panel(self, "After this step, what does the list look like?")
        p.pack(fill="x")
        self.q = ttk.Label(p, text="", style="Panel.TLabel", wraplength=int(800 * app.scale), justify="left", font=(ak.MONO, 11))
        self.q.pack(anchor="w")
        self.choice = tk.IntVar(value=-1)
        self.options = ttk.Frame(p, style="Panel.TFrame")
        self.options.pack(anchor="w", pady=8)
        row = ttk.Frame(p, style="Panel.TFrame")
        row.pack(anchor="w")
        ttk.Button(row, text="Check", style="Accent.TButton", command=self.check).pack(side="left")
        ttk.Button(row, text="Next question", command=self.ask).pack(side="left", padx=6)
        self.result = ttk.Label(p, text="", style="Panel.TLabel")
        self.result.pack(anchor="w", pady=6)
        self.score = ttk.Label(self, text="", style="Muted.TLabel")
        self.score.pack(anchor="w", pady=8)
        self.answer, self.algo, self.answered = None, None, False

    def ask(self, rng=None):
        rng = rng or random.Random()
        self.q_data = make_question(rng)
        algo, before, opts, answer = self.q_data
        self.algo, self.answer, self.answered = algo, answer, False
        self.q.configure(text="%s\nCurrent list: %s" % (algo, " ".join(map(str, before))))
        self.choice.set(-1)
        for w in self.options.winfo_children():
            w.destroy()
        for i, o in enumerate(opts):
            ttk.Radiobutton(self.options, text=" ".join(map(str, o)), value=i, variable=self.choice).pack(anchor="w")
        self.result.configure(text="")

    def check(self):
        if self.answered or self.choice.get() < 0:
            return
        self.answered = True
        ok = self.choice.get() == self.answer
        self.result.configure(text="Correct." if ok else "Not quite: the answer is option %d." % (self.answer + 1))
        self.app.store.insert("attempt", day=ak.today(), algorithm=self.algo, correct=1 if ok else 0)
        self.show_score()

    def show_score(self):
        rows = self.app.store.list("attempt")
        good = sum(r["correct"] for r in rows)
        self.score.configure(text="%d correct out of %d" % (good, len(rows)) if rows else "No answers yet")

    def refresh(self):
        if self.answer is None:
            self.ask()
        self.show_score()


def make_question(rng):
    """(algorithm, list before a move, four distinct options, index of the true next list)."""
    name = rng.choice(["Bubble sort", "Insertion sort", "Selection sort", "Heap sort", "Quick sort"])
    values = rng.sample(range(1, 30), 7)
    states = []
    for f in al.BY_NAME[name].run(values).frames:
        whole = sorted(f["values"]) == sorted(values)       # skip mid-shift states that hold a duplicate
        if whole and (not states or f["values"] != states[-1]):
            states.append(f["values"])
    k = rng.randrange(0, max(1, len(states) - 1))
    before, after = states[k], states[min(k + 1, len(states) - 1)]
    opts = [after]
    tries = 0
    while len(opts) < 4 and tries < 200:
        tries += 1
        cand = before[:]
        i, j = rng.sample(range(len(cand)), 2)
        cand[i], cand[j] = cand[j], cand[i]
        if cand not in opts:
            opts.append(cand)
    rng.shuffle(opts)
    return name, before, opts, opts.index(after)


class Presets(ttk.Frame):
    title = "Saved inputs"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.view = ak.EntityView(self, app, "preset", buttons=[("Open in player", self.open)])
        self.view.pack(fill="both", expand=True)
        self.refresh, self.commit = self.view.refresh, self.view.commit

    def open(self):
        if self.view.current:
            row = self.app.store.get("preset", self.view.current)
            self.app.navigate("Player")
            self.app.views["Player"].open_preset(row)


class Reference(ttk.Frame):
    title = "Reference"

    def __init__(self, parent, app):
        super().__init__(parent)
        t = ak.Table(self, app, [("name", "Algorithm", 24), ("group", "Group", 10), ("time", "Time", 28), ("space", "Space", 10), ("note", "When to use it", 60)])
        t.pack(fill="both", expand=True)
        t.fill([(a.name, a.group, a.time, a.space, a.note) for a in al.ALGOS])

    def refresh(self):
        pass


class APP(ak.BaseApp):
    APP_NAME, ACCENT = "Algorithm Animator", "#7c3aed"
    SCHEMA, SAMPLE = SCHEMA, staticmethod(sample)
    VIEWS = [Player, Compare, Quiz, Presets, Reference, ak.DataView]


def main(argv=None):
    return ak.main(APP, argv)
