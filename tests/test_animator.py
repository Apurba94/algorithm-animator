import os
import random
import shutil
import tempfile
import tkinter as tk
import unittest

from algorithm_animator import algos as al
from algorithm_animator import app as A
from algorithm_animator import appkit as ak


class TestSorting(unittest.TestCase):
    def test_every_sort_sorts(self):
        rng = random.Random(3)
        for a in al.ALGOS:
            if a.group != "Sorting":
                continue
            for _ in range(60):
                v = [rng.randint(0, 30) for _ in range(rng.randint(1, 25))]
                r = a.run(v)
                self.assertEqual(r.frames[-1]["values"], sorted(v), a.name)
                self.assertEqual(sorted(r.frames[0]["values"]), sorted(v))
                for f in r.frames:                                # no value is ever lost, except the overwrite in merge
                    self.assertEqual(len(f["values"]), len(v))

    def test_counts(self):
        self.assertEqual(al.bubble([3, 2, 1]).frames[-1]["moves"], 3)
        self.assertEqual(al.bubble([1, 2, 3, 4]).frames[-1]["comps"], 3)              # early exit on sorted input
        self.assertEqual(al.selection([5, 4, 3, 2, 1]).frames[-1]["comps"], 10)
        self.assertEqual(al.insertion([1, 2, 3]).frames[-1]["comps"], 2)
        with self.assertRaises(ValueError):
            al.counting([1, -1])

    def test_quick_sort_degrades_on_sorted_input(self):
        srt = list(range(1, 41))
        shuffled = srt[:]
        random.Random(1).shuffle(shuffled)
        self.assertEqual(al.quick_sort(srt).frames[-1]["comps"], 40 * 39 // 2)
        self.assertLess(al.quick_sort(shuffled).frames[-1]["comps"], 40 * 39 // 4)

    def test_lines_are_valid(self):
        for a in al.ALGOS:
            r = A.build(a, "", 2)[0]
            self.assertGreater(len(r.frames), 1, a.name)
            for f in r.frames:
                self.assertLess(f["line"], len(a.pseudo), a.name)
                self.assertTrue(f["note"], a.name)


class TestOthers(unittest.TestCase):
    def test_binary_search(self):
        self.assertEqual(al.binary_search([1, 3, 5, 7], 5).frames[-1]["found"], 2)
        self.assertEqual(al.binary_search([1, 3, 5, 7], 4).frames[-1]["found"], -1)
        self.assertLessEqual(al.binary_search(list(range(1000)), 1).frames[-1]["comps"], 11)

    def test_sliding_max_against_naive(self):
        rng = random.Random(4)
        for _ in range(50):
            v = [rng.randint(-9, 9) for _ in range(rng.randint(3, 20))]
            self.assertEqual(al.sliding_max(v, 3).frames[-1]["out"], [max(v[i:i + 3]) for i in range(len(v) - 2)])

    def test_bst_heap_union(self):
        self.assertEqual(al.bst_insert([5, 2, 8, 2, 9]).frames[-1]["inorder"], [2, 5, 8, 9])
        v = [random.Random(1).randint(0, 50) for _ in range(1)] + [7, 3, 9, 1, 5]
        self.assertEqual(al.heap_ops(v).frames[-1]["popped"], sorted(v))
        self.assertEqual(al.union_find(5, [(0, 1), (1, 2), (3, 4)]).frames[-1]["sets"], 2)
        self.assertEqual(al.union_find(4, [(0, 0)]).frames[-1]["sets"], 4)

    def test_graphs_against_floyd(self):
        for seed in range(25):
            g = al.random_graph(seed, 9)
            inf = 10 ** 9
            d = [[0 if i == j else inf for j in range(9)] for i in range(9)]
            for u, v, w in g.edges:
                d[u][v] = d[v][u] = min(d[u][v], w)
            for k in range(9):
                for i in range(9):
                    for j in range(9):
                        d[i][j] = min(d[i][j], d[i][k] + d[k][j])
            self.assertEqual(al.dijkstra(g).frames[-1]["dist"], {i: d[0][i] for i in range(9)})
            hops = al.bfs(g).frames[-1]["dist"]
            self.assertEqual(set(hops), set(range(9)))
            self.assertEqual(len(al.dfs(g).frames[-1]["order"]), 9)

    def test_kruskal_and_topo(self):
        g = al.G(4, [(0, 1, 1), (1, 2, 2), (0, 2, 3), (2, 3, 1)])
        last = al.kruskal(g).frames[-1]
        self.assertEqual((last["total"], len(last["tree"])), (4, 3))
        dag = al.G(4, [(0, 1, 1), (1, 2, 1), (0, 3, 1), (3, 2, 1)], True)
        order = al.topo_sort(dag).frames[-1]["order"]
        self.assertLess(order.index(0), order.index(2))
        self.assertEqual(len(order), 4)
        cyc = al.topo_sort(al.G(3, [(0, 1, 1), (1, 2, 1), (2, 1, 1)], True)).frames[-1]
        self.assertIn("cycle", cyc["note"])

    def test_astar_matches_dijkstra_and_explores_less(self):
        total_a = total_d = 0
        for seed in range(30):
            grid = al.maze(seed)
            a = al.grid_search(grid, astar=True).frames[-1]
            d = al.grid_search(grid).frames[-1]
            self.assertEqual(a["length"], d["length"], seed)
            total_a += len(a["closed"])
            total_d += len(d["closed"])
        self.assertLess(total_a, total_d)
        walled = [list("..#.."), list("..#.."), list("..#..")]
        self.assertIsNone(al.grid_search(walled).frames[-1]["length"])

    def test_parsers(self):
        self.assertEqual(al.parse_numbers("3, 1 2"), [3, 1, 2])
        g = al.parse_graph("0 1 5\n1 2\n")
        self.assertEqual((g.n, g.edges), (3, [(0, 1, 5), (1, 2, 1)]))
        with self.assertRaises(ValueError):
            al.parse_graph("0\n")
        with self.assertRaises(ValueError):
            al.parse_graph("")

    def test_build_and_race(self):
        algo = al.BY_NAME["Bubble sort"]
        self.assertEqual(A.build(algo, "3 1 2")[1], "3 1 2")
        with self.assertRaises(ValueError):
            A.build(algo, " ".join(["1"] * 300))
        with self.assertRaises(ValueError):
            A.build(al.BY_NAME["A* search"], "...\n..\n")
        generated = A.build(algo, "", 7)[1].split()
        self.assertGreater(len(set(generated)), 6)                       # generated input must actually vary
        rows = al.race([5, 2, 9, 1])
        self.assertEqual(len(rows), 7)
        self.assertEqual(len(al.race([5, -2])), 6)                       # counting sort needs non-negatives
        line = al.growth("Merge sort", [8, 16, 32])
        self.assertLess(line[0][1], line[2][1])

    def test_quiz_questions_are_sound(self):
        rng = random.Random(9)
        for _ in range(80):
            name, before, opts, ans = A.make_question(rng)
            self.assertEqual(len(opts), 4)
            self.assertEqual(len({tuple(o) for o in opts}), 4)
            self.assertTrue(0 <= ans < 4)
            states = [f["values"] for f in al.BY_NAME[name].run(sorted(before)).frames]
            self.assertTrue(states)
            self.assertEqual(sorted(opts[ans]), sorted(before))


class TestGui(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.store = ak.Store(A.SCHEMA, os.path.join(self.dir, "t.sqlite3"), A.APP.APP_NAME)
        A.sample(self.store)
        try:
            self.app = A.APP(self.store)
        except tk.TclError as exc:
            self.skipTest(str(exc))
        self.errors = []
        self.app.report_callback_exception = lambda e, v, t: self.errors.append(repr(v))
        self.app.update()

    def tearDown(self):
        self.store.close()
        self.app.destroy()
        shutil.rmtree(self.dir, ignore_errors=True)
        self.assertEqual(self.errors, [])

    def test_every_screen_in_both_themes(self):
        for theme in ("Dark", "Light"):
            self.app.set_theme(theme)
            for t in self.app.titles():
                self.app.navigate(t)
                self.app.update()

    def test_every_algorithm_draws_every_stage(self):
        p = self.app.views["Player"]
        for a in al.ALGOS:
            p.group.set(a.group)
            p.name.set(a.name)
            p.load(None)
            for i in (0, len(p.rec.frames) // 2, len(p.rec.frames) - 1):
                p.seek(i)
                self.app.update_idletasks()
            self.assertIn("Step", p.count.cget("text"))

    def test_transport(self):
        p = self.app.views["Player"]
        p.first()
        p.forward()
        self.assertEqual(p.i, 1)
        p.last()
        p.forward()
        self.assertEqual(p.i, len(p.rec.frames) - 1)
        p.toggle()
        self.assertTrue(p.playing)
        p.stop()
        self.assertEqual(p.play_btn.cget("text"), "Play")

    def test_preset_and_quiz(self):
        self.app.navigate("Saved inputs")
        v = self.app.views["Saved inputs"]
        rid = self.store.list("preset", "name='Small graph'")[0]["id"]
        v.view.select(rid)
        v.open()
        p = self.app.views["Player"]
        self.assertEqual(p.name.get(), "Dijkstra")
        self.assertEqual(p.rec.frames[-1]["dist"][3], 8)
        self.app.navigate("Quiz")
        q = self.app.views["Quiz"]
        n = self.store.count("attempt")
        q.choice.set(q.answer)
        q.check()
        q.check()
        self.assertEqual(self.store.count("attempt"), n + 1)
        self.assertEqual(q.result.cget("text"), "Correct.")


if __name__ == "__main__":
    unittest.main()
