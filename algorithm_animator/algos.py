"""Algorithms instrumented to record frames. Each one really runs: frames are snapshots of its live state, so the
animation can never disagree with the algorithm."""
import heapq
import math
import random
from collections import deque


class Rec:
    """Frame recorder. A frame is a dict with kind, the state to draw, the pseudocode line and a note."""

    def __init__(self, kind):
        self.kind, self.frames, self.comps, self.moves = kind, [], 0, 0

    def snap(self, line, note, **state):
        f = {"kind": self.kind, "line": line, "note": note, "comps": self.comps, "moves": self.moves}
        f.update(state)
        self.frames.append(f)


class Algo:
    def __init__(self, name, group, kind, pseudo, run, time_, space, note):
        self.name, self.group, self.kind, self.pseudo, self.run = name, group, kind, pseudo, run
        self.time, self.space, self.note = time_, space, note


# ---------------- sorting ----------------
def bubble(a):
    a, r = list(a), Rec("array")
    n = len(a)
    r.snap(0, "Start", values=a[:], marks={})
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            r.comps += 1
            r.snap(2, "Compare positions %d and %d" % (j, j + 1), values=a[:], marks={j: "compare", j + 1: "compare"},
                   done=list(range(n - i, n)))
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                r.moves += 1
                swapped = True
                r.snap(3, "Swap", values=a[:], marks={j: "swap", j + 1: "swap"}, done=list(range(n - i, n)))
        if not swapped:
            r.snap(4, "No swaps in this pass: the list is sorted", values=a[:], marks={}, done=list(range(n)))
            break
    r.snap(5, "Sorted", values=a[:], marks={}, done=list(range(n)))
    return r


def insertion(a):
    a, r = list(a), Rec("array")
    n = len(a)
    r.snap(0, "Start", values=a[:], marks={})
    for i in range(1, n):
        key, j = a[i], i - 1
        r.snap(1, "Take %s and insert it into the sorted prefix" % key, values=a[:], marks={i: "key"}, done=list(range(i)))
        while j >= 0:
            r.comps += 1
            r.snap(2, "Compare with position %d" % j, values=a[:], marks={j: "compare", j + 1: "key"}, done=list(range(i)))
            if a[j] <= key:
                break
            a[j + 1] = a[j]
            r.moves += 1
            r.snap(3, "Shift right", values=a[:], marks={j + 1: "swap"}, done=list(range(i)))
            j -= 1
        a[j + 1] = key
        r.moves += 1
        r.snap(4, "Place %s" % key, values=a[:], marks={j + 1: "key"}, done=list(range(i + 1)))
    r.snap(5, "Sorted", values=a[:], marks={}, done=list(range(n)))
    return r


def selection(a):
    a, r = list(a), Rec("array")
    n = len(a)
    r.snap(0, "Start", values=a[:], marks={})
    for i in range(n - 1):
        low = i
        for j in range(i + 1, n):
            r.comps += 1
            r.snap(2, "Is position %d smaller than the current minimum?" % j, values=a[:], marks={j: "compare", low: "key"},
                   done=list(range(i)))
            if a[j] < a[low]:
                low = j
        if low != i:
            a[i], a[low] = a[low], a[i]
            r.moves += 1
        r.snap(3, "Put the minimum at position %d" % i, values=a[:], marks={i: "swap", low: "swap"}, done=list(range(i + 1)))
    r.snap(4, "Sorted", values=a[:], marks={}, done=list(range(n)))
    return r


def merge_sort(a):
    a, r = list(a), Rec("array")
    r.snap(0, "Start", values=a[:], marks={})

    def go(lo, hi):
        if hi - lo < 2:
            return
        mid = (lo + hi) // 2
        r.snap(1, "Split [%d, %d) at %d" % (lo, hi, mid), values=a[:], marks={}, window=(lo, hi - 1))
        go(lo, mid)
        go(mid, hi)
        left, right = a[lo:mid], a[mid:hi]
        i = j = 0
        k = lo
        while i < len(left) and j < len(right):
            r.comps += 1
            if left[i] <= right[j]:
                a[k] = left[i]
                i += 1
            else:
                a[k] = right[j]
                j += 1
            r.moves += 1
            r.snap(3, "Merge: write the smaller head at position %d" % k, values=a[:], marks={k: "swap"}, window=(lo, hi - 1))
            k += 1
        for x in left[i:] + right[j:]:
            a[k] = x
            r.moves += 1
            k += 1
        r.snap(4, "Merged [%d, %d)" % (lo, hi), values=a[:], marks={}, window=(lo, hi - 1))
    go(0, len(a))
    r.snap(5, "Sorted", values=a[:], marks={}, done=list(range(len(a))))
    return r


def quick_sort(a):
    a, r = list(a), Rec("array")
    r.snap(0, "Start", values=a[:], marks={})
    settled = set()

    def go(lo, hi):
        if lo > hi:
            return
        if lo == hi:
            settled.add(lo)
            return
        pivot, store = a[hi], lo
        r.snap(1, "Pivot %s" % pivot, values=a[:], marks={hi: "key"}, window=(lo, hi), done=sorted(settled))
        for j in range(lo, hi):
            r.comps += 1
            r.snap(2, "Is %s < pivot?" % a[j], values=a[:], marks={j: "compare", hi: "key"}, window=(lo, hi), pointers={"s": store},
                   done=sorted(settled))
            if a[j] < pivot:
                a[store], a[j] = a[j], a[store]
                r.moves += 1
                r.snap(3, "Move it left of the boundary", values=a[:], marks={store: "swap", j: "swap", hi: "key"}, window=(lo, hi),
                       done=sorted(settled))
                store += 1
        a[store], a[hi] = a[hi], a[store]
        r.moves += 1
        settled.add(store)
        r.snap(4, "Pivot reaches its final place %d" % store, values=a[:], marks={store: "key"}, window=(lo, hi), done=sorted(settled))
        go(lo, store - 1)
        go(store + 1, hi)
    go(0, len(a) - 1)
    r.snap(5, "Sorted", values=a[:], marks={}, done=list(range(len(a))))
    return r


def heap_sort(a):
    a, r = list(a), Rec("array")
    n = len(a)
    r.snap(0, "Start", values=a[:], marks={})

    def sift(i, end):
        while True:
            child = 2 * i + 1
            if child >= end:
                return
            if child + 1 < end:
                r.comps += 1
                if a[child + 1] > a[child]:
                    child += 1
            r.comps += 1
            r.snap(2, "Compare node %d with its larger child %d" % (i, child), values=a[:], marks={i: "key", child: "compare"},
                   done=list(range(end, n)))
            if a[i] >= a[child]:
                return
            a[i], a[child] = a[child], a[i]
            r.moves += 1
            r.snap(3, "Sift down", values=a[:], marks={i: "swap", child: "swap"}, done=list(range(end, n)))
            i = child
    for i in range(n // 2 - 1, -1, -1):
        sift(i, n)
    r.snap(1, "The list is now a max-heap", values=a[:], marks={})
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        r.moves += 1
        r.snap(4, "Move the maximum to position %d" % end, values=a[:], marks={0: "swap", end: "swap"}, done=list(range(end, n)))
        sift(0, end)
    r.snap(5, "Sorted", values=a[:], marks={}, done=list(range(n)))
    return r


def counting(a):
    a, r = list(a), Rec("array")
    if not a:
        r.snap(0, "Empty", values=[], marks={})
        return r
    if min(a) < 0:
        raise ValueError("counting sort here needs non-negative numbers")
    counts = [0] * (max(a) + 1)
    r.snap(0, "Start", values=a[:], marks={}, counts=counts[:])
    for i, x in enumerate(a):
        counts[x] += 1
        r.moves += 1
        r.snap(1, "Count %d" % x, values=a[:], marks={i: "compare"}, counts=counts[:])
    k = 0
    for x, c in enumerate(counts):
        for _ in range(c):
            a[k] = x
            r.moves += 1
            r.snap(3, "Write %d back" % x, values=a[:], marks={k: "swap"}, counts=counts[:], done=list(range(k)))
            k += 1
    r.snap(4, "Sorted", values=a[:], marks={}, done=list(range(len(a))))
    return r


def binary_search(a, target=None):
    a, r = sorted(a), Rec("array")
    target = a[len(a) * 2 // 3] if target is None and a else target
    lo, hi = 0, len(a) - 1
    r.snap(0, "Search for %s in the sorted list" % target, values=a[:], marks={}, pointers={"lo": lo, "hi": hi})
    while lo <= hi:
        mid = (lo + hi) // 2
        r.comps += 1
        r.snap(2, "Look at the middle, position %d" % mid, values=a[:], marks={mid: "compare"}, pointers={"lo": lo, "hi": hi, "mid": mid},
               window=(lo, hi))
        if a[mid] == target:
            r.snap(3, "Found at position %d" % mid, values=a[:], marks={mid: "key"}, found=mid)
            return r
        if a[mid] < target:
            lo = mid + 1
            r.snap(4, "Too small: search the right half", values=a[:], marks={}, pointers={"lo": lo, "hi": hi}, window=(lo, hi))
        else:
            hi = mid - 1
            r.snap(5, "Too large: search the left half", values=a[:], marks={}, pointers={"lo": lo, "hi": hi}, window=(lo, hi))
    r.snap(6, "Not present", values=a[:], marks={}, found=-1)
    return r


def sliding_max(a, k=3):
    a, r = list(a), Rec("array")
    dq, out = deque(), []
    r.snap(0, "Window size %d; the deque keeps candidate positions" % k, values=a[:], marks={}, deque=[], out=[])
    for i, x in enumerate(a):
        while dq and a[dq[-1]] <= x:
            r.comps += 1
            dq.pop()
            r.moves += 1
            r.snap(1, "Drop a smaller value from the back", values=a[:], marks={i: "key"}, deque=list(dq), out=out[:], window=(max(0, i - k + 1), i))
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()
            r.snap(3, "The front left the window", values=a[:], marks={i: "key"}, deque=list(dq), out=out[:], window=(max(0, i - k + 1), i))
        if i >= k - 1:
            out.append(a[dq[0]])
            r.snap(4, "Window maximum is %s" % a[dq[0]], values=a[:], marks={dq[0]: "swap"}, deque=list(dq), out=out[:], window=(i - k + 1, i))
    r.snap(5, "Maxima: %s" % out, values=a[:], marks={}, deque=list(dq), out=out[:])
    return r


# ---------------- trees and sets ----------------
class _Node:
    def __init__(self, v):
        self.v, self.l, self.r = v, None, None


def _layout(root):
    """In-order x, depth y: {id: {'value', 'x', 'y', 'parent'}} plus the in-order list."""
    nodes, order = {}, []
    x = [0]

    def go(n, d, parent):
        if n is None:
            return
        go(n.l, d + 1, n)
        nodes[id(n)] = {"value": n.v, "x": x[0], "y": d, "parent": id(parent) if parent else None}
        order.append(n.v)
        x[0] += 1
        go(n.r, d + 1, n)
    go(root, 0, None)
    return nodes, order


def bst_insert(a):
    r = Rec("tree")
    root = None
    r.snap(0, "Empty tree", nodes={}, mark=None)
    for v in a:
        if root is None:
            root = _Node(v)
            nodes, _ = _layout(root)
            r.snap(1, "%s becomes the root" % v, nodes=nodes, mark=id(root))
            continue
        cur = root
        while True:
            r.comps += 1
            nodes, _ = _layout(root)
            r.snap(2, "Compare %s with %s" % (v, cur.v), nodes=nodes, mark=id(cur))
            if v == cur.v:
                r.snap(5, "%s is already in the tree" % v, nodes=nodes, mark=id(cur))
                break
            side = "l" if v < cur.v else "r"
            nxt = getattr(cur, side)
            if nxt is None:
                n = _Node(v)
                setattr(cur, side, n)
                r.moves += 1
                nodes, _ = _layout(root)
                r.snap(4, "Insert %s" % v, nodes=nodes, mark=id(n))
                break
            cur = nxt
    nodes, order = _layout(root)
    r.snap(6, "In-order walk gives %s" % order, nodes=nodes, mark=None, inorder=order)
    return r


def _heap_nodes(h):
    out = {}
    for i, v in enumerate(h):
        d = int(math.log2(i + 1))
        pos = i + 1 - 2 ** d
        out[i] = {"value": v, "x": (pos + 0.5) * 2 ** (5 - d), "y": d, "parent": (i - 1) // 2 if i else None}
    return out


def heap_ops(a):
    r = Rec("tree")
    h = []
    r.snap(0, "Empty min-heap", nodes={}, mark=None)
    for v in a:
        h.append(v)
        i = len(h) - 1
        r.moves += 1
        r.snap(1, "Add %s at the end" % v, nodes=_heap_nodes(h), mark=i)
        while i and h[(i - 1) // 2] > h[i]:
            r.comps += 1
            p = (i - 1) // 2
            h[i], h[p] = h[p], h[i]
            r.moves += 1
            r.snap(2, "Swap with the larger parent", nodes=_heap_nodes(h), mark=p)
            i = p
        r.comps += 1
    popped = []
    while h:
        popped.append(h[0])
        last = h.pop()
        if h:
            h[0] = last
            i = 0
            r.snap(4, "Remove the minimum %s, move the last leaf to the root" % popped[-1], nodes=_heap_nodes(h), mark=0)
            while True:
                c = 2 * i + 1
                if c >= len(h):
                    break
                if c + 1 < len(h) and h[c + 1] < h[c]:
                    c += 1
                r.comps += 1
                if h[i] <= h[c]:
                    break
                h[i], h[c] = h[c], h[i]
                r.moves += 1
                r.snap(5, "Sift down", nodes=_heap_nodes(h), mark=c)
                i = c
    r.snap(6, "Removed in order: %s" % popped, nodes={}, mark=None, popped=popped)
    return r


def union_find(n, pairs):
    r = Rec("tree")
    p = list(range(n))
    size = [1] * n

    def nodes(mark=None):
        kids = {i: [] for i in range(n)}
        roots = []
        for i in range(n):
            (roots if p[i] == i else kids[p[i]]).append(i)
        out, x = {}, [0]

        def go(u, d):
            first = x[0]
            for c in kids[u]:
                go(c, d + 1)
            mid = (first + x[0] - 1) / 2 if kids[u] else x[0]
            if not kids[u]:
                x[0] += 1
            out[u] = {"value": u, "x": mid, "y": d, "parent": p[u] if p[u] != u else None}
        for t in roots:
            go(t, 0)
        return out

    def find(x_):
        path = []
        while p[x_] != x_:
            path.append(x_)
            x_ = p[x_]
        for v in path:
            if p[v] != x_:
                p[v] = x_
                r.moves += 1
        return x_
    r.snap(0, "Every element starts as its own set", nodes=nodes(), mark=None, parents=p[:])
    for a, b in pairs:
        ra, rb = find(a), find(b)
        r.comps += 1
        r.snap(1, "Union %d and %d: roots %d and %d" % (a, b, ra, rb), nodes=nodes(), mark=a, parents=p[:])
        if ra != rb:
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            p[rb] = ra
            size[ra] += size[rb]
            r.moves += 1
            r.snap(3, "Attach the smaller tree under %d" % ra, nodes=nodes(), mark=ra, parents=p[:])
        else:
            r.snap(2, "Already in one set", nodes=nodes(), mark=ra, parents=p[:])
    r.snap(4, "%d set(s) remain" % len({find(i) for i in range(n)}), nodes=nodes(), mark=None, parents=p[:],
           sets=len({find(i) for i in range(n)}))
    return r


# ---------------- graphs ----------------
class G:
    def __init__(self, n, edges, directed=False):
        self.n, self.edges, self.directed = n, edges, directed
        self.adj = [[] for _ in range(n)]
        for u, v, w in edges:
            self.adj[u].append((v, w))
            if not directed:
                self.adj[v].append((u, w))
        for lst in self.adj:
            lst.sort()


def _gsnap(r, g, line, note, **st):
    r.snap(line, note, n=g.n, edges=g.edges, directed=g.directed, **st)


def bfs(g, s=0):
    r = Rec("graph")
    dist = {s: 0}
    q = deque([s])
    _gsnap(r, g, 0, "Start from %d" % s, seen=dict(dist), frontier=list(q), current=None, active=None)
    while q:
        u = q.popleft()
        _gsnap(r, g, 2, "Take %d from the queue" % u, seen=dict(dist), frontier=list(q), current=u, active=None)
        for v, _ in g.adj[u]:
            r.comps += 1
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
                r.moves += 1
                _gsnap(r, g, 4, "Discover %d at distance %d" % (v, dist[v]), seen=dict(dist), frontier=list(q), current=u, active=(u, v))
    _gsnap(r, g, 5, "Finished", seen=dict(dist), frontier=[], current=None, active=None, dist=dist)
    return r


def dfs(g, s=0):
    r = Rec("graph")
    seen, order = {}, []

    def go(u):
        seen[u] = len(seen)
        order.append(u)
        r.moves += 1
        _gsnap(r, g, 1, "Visit %d" % u, seen=dict(seen), frontier=[], current=u, active=None)
        for v, _ in g.adj[u]:
            r.comps += 1
            if v not in seen:
                _gsnap(r, g, 3, "Go deeper along %d-%d" % (u, v), seen=dict(seen), frontier=[], current=u, active=(u, v))
                go(v)
        _gsnap(r, g, 4, "Back from %d" % u, seen=dict(seen), frontier=[], current=u, active=None)
    go(s)
    _gsnap(r, g, 5, "Visit order: %s" % order, seen=dict(seen), frontier=[], current=None, active=None, order=order)
    return r


def dijkstra(g, s=0):
    r = Rec("graph")
    dist = {s: 0}
    done = {}
    h = [(0, s)]
    _gsnap(r, g, 0, "Distance to %d is 0" % s, seen={}, labels=dict(dist), frontier=[s], current=None, active=None)
    while h:
        d, u = heapq.heappop(h)
        if u in done:
            continue
        done[u] = d
        _gsnap(r, g, 2, "Settle %d at distance %d" % (u, d), seen=dict(done), labels=dict(dist), frontier=[x for _, x in h], current=u, active=None)
        for v, w in g.adj[u]:
            r.comps += 1
            if v not in dist or d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(h, (d + w, v))
                r.moves += 1
                _gsnap(r, g, 4, "Improve %d to %d" % (v, d + w), seen=dict(done), labels=dict(dist), frontier=[x for _, x in h], current=u, active=(u, v))
    _gsnap(r, g, 5, "Finished", seen=dict(done), labels=dict(dist), frontier=[], current=None, active=None, dist=dict(dist))
    return r


def kruskal(g):
    r = Rec("graph")
    p = list(range(g.n))

    def find(x):
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x
    chosen, total = [], 0
    _gsnap(r, g, 0, "Sort the edges by weight", seen={}, frontier=[], current=None, active=None, tree=[])
    for u, v, w in sorted(g.edges, key=lambda e: (e[2], e[0], e[1])):
        r.comps += 1
        _gsnap(r, g, 2, "Try edge %d-%d of weight %d" % (u, v, w), seen={}, frontier=[], current=None, active=(u, v), tree=chosen[:])
        ru, rv = find(u), find(v)
        if ru != rv:
            p[ru] = rv
            chosen.append((u, v))
            total += w
            r.moves += 1
            _gsnap(r, g, 3, "Accept it: total %d" % total, seen={}, frontier=[], current=None, active=(u, v), tree=chosen[:])
        else:
            _gsnap(r, g, 4, "Skip it: it would form a cycle", seen={}, frontier=[], current=None, active=(u, v), tree=chosen[:])
    _gsnap(r, g, 5, "Minimum spanning forest weighs %d" % total, seen={}, frontier=[], current=None, active=None, tree=chosen[:], total=total)
    return r


def topo_sort(g):
    r = Rec("graph")
    indeg = [0] * g.n
    for u, v, _ in g.edges:
        indeg[v] += 1
    q = deque(i for i in range(g.n) if indeg[i] == 0)
    order = []
    _gsnap(r, g, 0, "Queue the vertices with no incoming edges", seen={}, frontier=list(q), current=None, active=None)
    while q:
        u = q.popleft()
        order.append(u)
        r.moves += 1
        _gsnap(r, g, 2, "Output %d" % u, seen={x: i for i, x in enumerate(order)}, frontier=list(q), current=u, active=None)
        for v, _ in g.adj[u]:
            indeg[v] -= 1
            r.comps += 1
            if indeg[v] == 0:
                q.append(v)
                _gsnap(r, g, 4, "%d is now free" % v, seen={x: i for i, x in enumerate(order)}, frontier=list(q), current=u, active=(u, v))
    note = "Order: %s" % order if len(order) == g.n else "A cycle blocks %d vertices" % (g.n - len(order))
    _gsnap(r, g, 5, note, seen={x: i for i, x in enumerate(order)}, frontier=[], current=None, active=None, order=order)
    return r


# ---------------- grids ----------------
def maze(seed, h=13, w=21):
    rng = random.Random(seed)
    return [["#" if rng.random() < 0.27 else "." for _ in range(w)] for _ in range(h)]


def grid_search(grid, start=None, goal=None, astar=False):
    r = Rec("grid")
    h, w = len(grid), len(grid[0])
    start, goal = start or (0, 0), goal or (h - 1, w - 1)
    grid = [row[:] for row in grid]
    grid[start[0]][start[1]] = grid[goal[0]][goal[1]] = "."

    def est(c):
        return abs(c[0] - goal[0]) + abs(c[1] - goal[1]) if astar else 0
    came, cost = {start: None}, {start: 0}
    pq = [(est(start), 0, start)]
    closed = set()
    tie = 0
    r.snap(0, "Start at the top left", grid=grid, closed=[], open=[start], path=[], start=start, goal=goal)
    found = False
    while pq:
        _, _, c = heapq.heappop(pq)
        if c in closed:
            continue
        closed.add(c)
        r.moves += 1
        if len(closed) % 2 == 1 or c == goal:
            r.snap(2, "Expand cell %s" % (c,), grid=grid, closed=list(closed), open=[x[2] for x in pq], path=[], start=start, goal=goal)
        if c == goal:
            found = True
            break
        for d in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            n = (c[0] + d[0], c[1] + d[1])
            r.comps += 1
            if 0 <= n[0] < h and 0 <= n[1] < w and grid[n[0]][n[1]] == "." and (n not in cost or cost[c] + 1 < cost[n]):
                cost[n], came[n] = cost[c] + 1, c
                tie += 1
                heapq.heappush(pq, (cost[n] + est(n), tie, n))
    path = []
    if found:
        c = goal
        while c is not None:
            path.append(c)
            c = came[c]
        path.reverse()
    r.snap(5, "Path of %d steps" % (len(path) - 1) if found else "No path exists", grid=grid, closed=list(closed), open=[], path=path,
           start=start, goal=goal, length=len(path) - 1 if found else None)
    return r


def random_graph(seed, n=8, directed=False, extra=5):
    rng = random.Random(seed)
    edges, seen = [], set()
    for v in range(1, n):
        u = rng.randrange(v)
        seen.add((u, v))
        edges.append((u, v, rng.randint(1, 9)))
    tries = 0
    while extra and tries < 200:
        tries += 1
        u, v = sorted(rng.sample(range(n), 2))
        if (u, v) not in seen:
            seen.add((u, v))
            edges.append((u, v, rng.randint(1, 9)))
            extra -= 1
    return G(n, edges, directed)


def parse_numbers(text):
    return [int(x) for x in text.replace(",", " ").split()]


def parse_graph(text, directed=False):
    """Lines 'a b [weight]' with vertices from 0."""
    edges, top = [], 0
    for line in text.splitlines():
        parts = line.replace(",", " ").split()
        if not parts:
            continue
        if len(parts) < 2:
            raise ValueError("each line needs two vertices: %r" % line)
        a, b, w = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 1
        edges.append((a, b, w))
        top = max(top, a, b)
    if not edges:
        raise ValueError("enter at least one edge")
    return G(top + 1, edges, directed)


def pairs_for(n, seed=1):
    rng = random.Random(seed)
    return [(rng.randrange(n), rng.randrange(n)) for _ in range(n)]


P_SORT = ["start", "repeat passes", "  compare neighbours", "  swap if out of order", "stop when a pass has no swaps", "sorted"]
ALGOS = [
    Algo("Bubble sort", "Sorting", "array", P_SORT, bubble, "O(n^2)", "O(1)", "Stable. Very slow, but the early exit makes sorted input O(n)."),
    Algo("Insertion sort", "Sorting", "array",
         ["start", "for each element, take it as key", "  compare with the sorted prefix, right to left", "  shift larger items right", "  place the key", "sorted"],
         insertion, "O(n^2)", "O(1)", "Stable. Excellent on small or nearly sorted inputs."),
    Algo("Selection sort", "Sorting", "array",
         ["start", "for each position i", "  find the minimum of the rest", "  swap it into position i", "sorted"], selection, "O(n^2)", "O(1)",
         "Not stable. Few swaps, always many comparisons."),
    Algo("Merge sort", "Sorting", "array",
         ["start", "split into two halves", "sort each half", "merge by repeatedly taking the smaller head", "range merged", "sorted"],
         merge_sort, "O(n log n)", "O(n)", "Stable with a guaranteed bound. Also the base of inversion counting."),
    Algo("Quick sort", "Sorting", "array",
         ["start", "choose the last element as pivot", "  compare each element with the pivot", "  move smaller ones left", "put the pivot in place, recurse", "sorted"],
         quick_sort, "O(n log n) average, O(n^2) worst", "O(log n)", "Not stable. This last-element pivot degrades on sorted input."),
    Algo("Heap sort", "Sorting", "array",
         ["start", "build a max-heap", "  compare with the larger child", "  sift down", "swap the maximum to the end, shrink the heap", "sorted"],
         heap_sort, "O(n log n)", "O(1)", "Not stable. In place with a guaranteed bound."),
    Algo("Counting sort", "Sorting", "array", ["start", "count each value", "for each value in order", "  write it back count times", "sorted"], counting,
         "O(n + k)", "O(k)", "Fast when values are small. Uses no comparisons."),
    Algo("Binary search", "Searching", "array",
         ["sort, set lo and hi", "while lo <= hi", "  look at the middle", "  found it", "  too small: lo = mid + 1", "  too large: hi = mid - 1", "not present"],
         binary_search, "O(log n)", "O(1)", "Needs sorted input. Generalises to any monotone yes/no question."),
    Algo("Sliding window maximum", "Searching", "array",
         ["start", "while the back is smaller than the new value, pop it", "push the new position", "pop the front if it left the window", "the front is the maximum", "done"],
         sliding_max, "O(n)", "O(k)", "A monotonic deque: each position enters and leaves once."),
    Algo("BST insertion", "Trees", "tree",
         ["start", "empty tree: new root", "compare with the current node", "go left or right", "free spot: insert", "duplicate: ignore", "in-order is sorted"],
         bst_insert, "O(log n) average, O(n) worst", "O(n)", "Sorted input makes a path: this is why balanced trees exist."),
    Algo("Binary heap", "Trees", "tree",
         ["start", "append at the end", "bubble up while smaller than the parent", "remove the root", "move the last leaf to the root", "sift down", "done"],
         heap_ops, "O(log n) per operation", "O(n)", "A priority queue in an array: parent of i is (i-1)/2."),
    Algo("Union-find", "Trees", "tree",
         ["every element alone", "find both roots", "same root: nothing to do", "attach the smaller tree", "done"],
         lambda a: union_find(max(2, len(a)), pairs_for(max(2, len(a)))), "almost O(1) per operation", "O(n)",
         "Union by size plus path compression."),
    Algo("Breadth-first search", "Graphs", "graph",
         ["put the start in the queue", "while the queue has items", "  take the front vertex", "  for each neighbour", "    if unseen: record distance, enqueue", "done"],
         bfs, "O(V + E)", "O(V)", "Gives shortest paths in unweighted graphs."),
    Algo("Depth-first search", "Graphs", "graph",
         ["start", "mark the vertex", "for each neighbour", "  if unseen: recurse", "backtrack", "done"], dfs, "O(V + E)", "O(V)",
         "The base of cycle detection, SCC, bridges and topological order."),
    Algo("Dijkstra", "Graphs", "graph",
         ["distance of the start is 0", "while the heap has items", "  settle the nearest vertex", "  for each neighbour", "    if a shorter path exists: update", "done"],
         dijkstra, "O((V + E) log V)", "O(V)", "Needs non-negative weights."),
    Algo("Kruskal MST", "Graphs", "graph",
         ["sort the edges by weight", "for each edge", "  does it join two components?", "    yes: accept", "    no: skip", "done"], kruskal,
         "O(E log E)", "O(V)", "Greedy, correct by the cut property. Uses union-find."),
    Algo("Topological sort", "Graphs", "graph",
         ["queue the vertices with no incoming edges", "while the queue has items", "  output the front vertex", "  remove its edges", "    a vertex is freed: enqueue", "done"],
         topo_sort, "O(V + E)", "O(V)", "Kahn's algorithm. Leftover vertices mean a cycle."),
    Algo("Grid Dijkstra", "Grids", "grid", ["start", "take the cheapest open cell", "expand it", "add its neighbours", "reach the goal", "path"],
         lambda m: grid_search(m), "O(HW log(HW))", "O(HW)", "Expands evenly in all directions."),
    Algo("A* search", "Grids", "grid", ["start", "take the open cell with the lowest cost + estimate", "expand it", "add its neighbours", "reach the goal", "path"],
         lambda m: grid_search(m, astar=True), "Often far fewer cells than Dijkstra", "O(HW)", "The Manhattan estimate never overestimates, so the path is shortest."),
]
BY_NAME = {a.name: a for a in ALGOS}


def layout_circle(n):
    return [(0.5 + 0.42 * math.cos(2 * math.pi * i / n - math.pi / 2), 0.5 + 0.42 * math.sin(2 * math.pi * i / n - math.pi / 2)) for i in range(n)]


def race(values):
    """Comparison and move counts of every sort on one input."""
    out = []
    for a in ALGOS:
        if a.group != "Sorting" or (a.name == "Counting sort" and min(values) < 0):
            continue
        r = a.run(values)
        out.append({"name": a.name, "comps": r.frames[-1]["comps"], "moves": r.frames[-1]["moves"], "frames": len(r.frames)})
    return out


def growth(name, sizes, seed=1, shape="random"):
    """(n, comparisons + moves) for an algorithm on growing inputs."""
    rng = random.Random(seed)
    out = []
    for n in sizes:
        v = shaped(rng, n, shape)
        last = BY_NAME[name].run(v).frames[-1]
        out.append((n, last["comps"] + last["moves"]))
    return out


def shaped(rng, n, shape):
    if shape == "sorted":
        return list(range(1, n + 1))
    if shape == "reversed":
        return list(range(n, 0, -1))
    if shape == "few unique":
        return [rng.randint(1, 5) for _ in range(n)]
    if shape == "nearly sorted":
        a = list(range(1, n + 1))
        for _ in range(max(1, n // 10)):
            i, j = rng.randrange(n), rng.randrange(n)
            a[i], a[j] = a[j], a[i]
        return a
    return [rng.randint(1, 99) for _ in range(n)]
