# Algorithm Animator

Watch 19 algorithms run one step at a time. Each animation is a recording of the real algorithm, so it cannot
disagree with what the code does.

* **Sorting:** bubble, insertion, selection, merge, quick, heap, counting
* **Searching:** binary search, sliding window maximum with a monotonic deque
* **Trees:** binary search tree, binary heap, union-find
* **Graphs:** BFS, DFS, Dijkstra, Kruskal, topological sort
* **Grids:** Dijkstra and A* on a maze

Each step shows the state, the matching pseudocode line, what just happened, and running comparison and move
counts. Play, pause, step, drag the slider and change the speed, or type your own input.

**Compare** races the sorts on random, sorted, reversed, nearly sorted or few-unique inputs, and plots work
against size. **Quiz** shows a state and asks what comes next. **Saved inputs** keeps interesting cases, such as
the input that makes quick sort quadratic. **Reference** lists complexities and when to use each one.

`--demo` opens a temporary database with sample data.

## Download

Windows: get the `.exe` from [Releases](https://github.com/Apurba94/algorithm-animator/releases/latest) and double-click it. No installation or Python is needed.
Windows may show a SmartScreen warning the first time because the program is not code-signed: choose *More info*, then *Run anyway*.

## From source

```bash
python -m algorithm_animator
python -m unittest discover -s tests -t .
python build_exe.py
```

## License

MIT
