"""Ejercicios 1 a 5 de Algorithms Optimization.

Ejecucion: python experimentos.py --out resultados
Solo usa la biblioteca estandar. Los tiempos dependen del equipo.
"""
import argparse
import csv
import itertools
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
import random
import statistics as st
import time

EPS = 1e-10


def estimate_pi(seed, samples=1_000_000):
    rng = random.Random(seed)
    inside = sum(rng.random() ** 2 + rng.random() ** 2 <= 1.0
                 for _ in range(samples))
    return 4 * inside / samples


def parallel_experiment():
    # Ocho tareas fijas, ocho millones de muestras para cada p.
    ctx = mp.get_context("fork" if "fork" in mp.get_all_start_methods()
                         else "spawn")
    seeds, rows = list(range(8)), []
    order_rng = random.Random(20261015)
    estimate_pi(99, 10_000)  # calentamiento fuera del cronometro
    reference = None
    for repeat in range(1, 6):
        order = [1, 2, 4, 8]
        order_rng.shuffle(order)
        for p in order:
            start = time.perf_counter()
            with ctx.Pool(processes=p) as pool:
                estimates = pool.map(estimate_pi, seeds, chunksize=1)
            elapsed = time.perf_counter() - start
            if reference is None:
                reference = estimates
            assert estimates == reference
            rows.append(dict(repetition=repeat, processes=p,
                             seconds=elapsed, pi=sum(estimates) / 8))
    return rows, ctx.get_start_method()


def greedy_knapsack(items, capacity, criterion):
    # Cada registro es (nombre, valor, peso). Se omiten los que no caben.
    key = ((lambda x: (x[2], x[0])) if criterion == "weight"
           else (lambda x: (-x[1] / x[2], x[0])))
    chosen, weight, value = [], 0, 0
    for name, v, w in sorted(items, key=key):
        if weight + w <= capacity:
            chosen.append(name)
            weight += w
            value += v
    return dict(chosen=chosen, weight=weight, value=value)


def points_from_seed(n, seed, scale=100):
    rng = random.Random(seed)
    return [(rng.uniform(0, scale), rng.uniform(0, scale))
            for _ in range(n)]


def distances(points):
    return [[math.dist(a, b) for b in points] for a in points]


def tour_length(route, d):
    return sum(d[route[i]][route[(i + 1) % len(route)]]
               for i in range(len(route)))


def moves(n):
    # Primera ciudad de la ruta fija. Excluir la inversion del ciclo completo.
    return [(i, k) for i in range(1, n - 1)
            for k in range(i + 1, n)
            if (i, k) != (1, n - 1)]


def delta_2opt(route, d, i, k):
    a, b = route[i - 1], route[i]
    c, e = route[k], route[(k + 1) % len(route)]
    return d[a][c] + d[b][e] - d[a][b] - d[c][e]


def two_opt(route, d):
    route = list(route)
    pairs = moves(len(route))
    history = [tour_length(route, d)]
    while True:
        for i, k in pairs:
            if delta_2opt(route, d, i, k) < -EPS:
                route[i:k + 1] = reversed(route[i:k + 1])
                history.append(tour_length(route, d))
                break  # primera mejora; volver a explorar desde el inicio
        else:
            assert min(delta_2opt(route, d, i, k)
                       for i, k in pairs) >= -EPS
            return route, len(history) - 1, history


def nearest_neighbour(d, start=0):
    route, remaining = [start], set(range(len(d))) - {start}
    while remaining:
        v = min(remaining, key=lambda x: (d[route[-1]][x], x))
        route.append(v)
        remaining.remove(v)
    return route


def local_search_experiment():
    rows, example = [], None
    for trial in range(30):
        points = points_from_seed(30, 3000 + trial)
        d = distances(points)
        random_route = [0] + random.Random(4000 + trial).sample(
            list(range(1, 30)), 29)
        nn_start = random.Random(4500 + trial).randrange(30)
        starts = {"Random": random_route, "NN": nearest_neighbour(d, nn_start)}
        records = {}
        for name, route in starts.items():
            start = time.perf_counter()
            final, count, history = two_opt(route, d)
            elapsed = time.perf_counter() - start
            assert sorted(final) == list(range(30))
            rows.append(dict(instance=trial + 1, start=name,
                             initial_node=route[0],
                             initial_length=history[0],
                             final_length=history[-1],
                             improvements=count, seconds=elapsed))
            records[name] = dict(initial=route, final=final, history=history)
        if trial == 0:
            example = dict(points=points, records=records)
    return rows, example


def cooling_levels(alpha, t0=50, tmin=0.01):
    return math.ceil(math.log(tmin / t0) / math.log(alpha))


def anneal(route, d, seed, kind, levels, alpha=None,
           t0=50, proposals_per_level=50):
    # El PDF maximiza VALUE; para TSP, VALUE = -longitud.
    route, rng = list(route), random.Random(seed)
    pairs = moves(len(route))
    history = [tour_length(route, d)]
    worse_accepted = 0
    for level in range(levels):
        t = (t0 * alpha ** level if kind == "geometric"
             else t0 * (1 - level / levels))
        for _ in range(proposals_per_level):
            i, k = rng.choice(pairs)
            delta = delta_2opt(route, d, i, k)
            if delta <= 0 or rng.random() < math.exp(-delta / t):
                route[i:k + 1] = reversed(route[i:k + 1])
                worse_accepted += int(delta > 0)
        history.append(tour_length(route, d))
    # schedule(levels) = 0: devolver el estado actual, como el PDF.
    return route, history, worse_accepted


def annealing_experiment():
    d = distances(points_from_seed(30, 3000))
    initial = [0] + random.Random(5000).sample(list(range(1, 30)), 29)
    configs = [dict(name="G0.90", kind="geometric", alpha=0.90),
               dict(name="G0.97", kind="geometric", alpha=0.97),
               dict(name="G0.995", kind="geometric", alpha=0.995),
               dict(name="Linear", kind="linear", alpha=None)]
    rows, traces = [], {}
    for config in configs:
        levels = (cooling_levels(config["alpha"])
                  if config["kind"] == "geometric" else cooling_levels(.97))
        for repeat in range(20):
            start = time.perf_counter()
            route, history, worse = anneal(
                initial, d, 6000 + repeat, config["kind"],
                levels, config["alpha"])
            elapsed = time.perf_counter() - start
            assert sorted(route) == list(range(30))
            rows.append(dict(schedule=config["name"],
                             repetition=repeat + 1, seed=6000 + repeat,
                             levels=levels, proposals=levels * 50,
                             initial_length=tour_length(initial, d),
                             final_length=history[-1], seconds=elapsed,
                             worse_accepted=worse))
            if repeat == 0:
                traces[config["name"]] = history
    return rows, dict(initial=initial, traces=traces)


def mst_preorder(d):
    # Prim y preorden, en el mismo orden de insercion del PDF.
    best = {v: (d[0][v], 0) for v in range(1, len(d))}
    children = {v: [] for v in range(len(d))}
    tree_weight = 0
    while best:
        v = min(best, key=lambda u: best[u][0])
        weight, parent = best.pop(v)
        children[parent].append(v)
        tree_weight += weight
        for u in best:
            if d[v][u] < best[u][0]:
                best[u] = (d[v][u], v)
    def visit(v):
        return [v] + [x for child in children[v] for x in visit(child)]
    return visit(0), tree_weight


def exact_tsp(d):
    # Fijar 0 elimina rotaciones: para n=9 se evalua 8! = 40 320.
    best_route, best_length = None, math.inf
    for tail in itertools.permutations(range(1, len(d))):
        route = (0,) + tail
        value = tour_length(route, d)
        if value < best_length:
            best_route, best_length = route, value
    return list(best_route), best_length


def approximation_experiment():
    rows, worst = [], None
    for trial in range(100):
        points = points_from_seed(9, 7000 + trial, scale=10)
        d = distances(points)
        mst_route, tree_weight = mst_preorder(d)
        opt_route, opt = exact_tsp(d)
        improved, count, _ = two_opt(mst_route, d)
        before, after = tour_length(mst_route, d), tour_length(improved, d)
        initial = [0] + random.Random(8000 + trial).sample(list(range(1, 9)), 8)
        local, local_count, _ = two_opt(initial, d)
        nn_start = random.Random(8500 + trial).randrange(9)
        nn, nn_count, _ = two_opt(nearest_neighbour(d, nn_start), d)
        # La escala espacial es 10 veces menor que en el ejercicio 4.
        # T0=5 y Tmin=0.001 mantienen la misma escala relativa.
        sa_route, _, _ = anneal(initial, d, 9000 + trial, "geometric",
                               cooling_levels(.97, t0=5, tmin=.001), .97, t0=5)
        local_cost = tour_length(local, d)
        nn_cost = tour_length(nn, d)
        sa_cost = tour_length(sa_route, d)
        assert all(sorted(x) == list(range(9)) for x in [local, nn, sa_route])
        assert min(local_cost, nn_cost, sa_cost) >= opt - EPS
        assert tree_weight <= opt + EPS
        assert before <= 2 * tree_weight + EPS
        assert opt - EPS <= after <= before + EPS
        assert sorted(mst_route) == sorted(improved) == list(range(9))
        row = dict(instance=trial + 1, seed=7000 + trial,
                   optimal=opt, mst=before, mst_2opt=after,
                   ratio_mst=before / opt, ratio_2opt=after / opt,
                   improvements=count, tree_weight=tree_weight,
                   reduction_percent=100 * (before - after) / before,
                   local_random=local_cost, local_nn=nn_cost, sa=sa_cost,
                   ratio_local_random=local_cost / opt,
                   ratio_local_nn=nn_cost / opt, ratio_sa=sa_cost / opt,
                   local_improvements=local_count, nn_improvements=nn_count,
                   nn_start=nn_start, initial_seed=8000 + trial,
                   sa_seed=9000 + trial)
        rows.append(row)
        if worst is None or row["ratio_mst"] > worst["row"]["ratio_mst"]:
            worst = dict(row=row, points=points, mst_route=mst_route,
                         opt_route=opt_route, improved_route=improved)
    return rows, worst


def save_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(out):
    out.mkdir(parents=True, exist_ok=True)
    print("Ejercicio 1: mediciones con 1, 2, 4 y 8 procesos", flush=True)
    parallel, method = parallel_experiment()
    save_csv(out / "ejercicio_1.csv", parallel)
    items = [("A", 3, 2), ("B", 4, 3), ("C", 24, 8)]
    knapsack = {name: greedy_knapsack(items, 10, name)
                for name in ["weight", "ratio"]}
    print("Ejercicio 3: 30 comparaciones de 2-opt", flush=True)
    local, local_example = local_search_experiment()
    save_csv(out / "ejercicio_3.csv", local)
    print("Ejercicio 4: 80 ejecuciones de recocido simulado", flush=True)
    sa, sa_example = annealing_experiment()
    save_csv(out / "ejercicio_4.csv", sa)
    print("Ejercicio 5: 100 instancias y 100 optimos exactos", flush=True)
    approx, worst = approximation_experiment()
    save_csv(out / "ejercicio_5.csv", approx)
    result = dict(environment=dict(python=platform.python_version(),
                  system=platform.system(), cpu_count=os.cpu_count(),
                  available_cpus=len(os.sched_getaffinity(0))
                  if hasattr(os, "sched_getaffinity") else os.cpu_count(),
                  multiprocessing_method=method), parallel=parallel,
                  knapsack=knapsack, local=local, local_example=local_example,
                  sa=sa, sa_example=sa_example, approx=approx, worst=worst)
    (out / "resultados.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Finalizado", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("resultados"))
    run(parser.parse_args().out)
