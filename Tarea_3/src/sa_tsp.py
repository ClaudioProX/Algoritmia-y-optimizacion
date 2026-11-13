"""TSP euclidiano, vecino 2-opt y recocido simulado reproducible."""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


def distance_matrix(coordinates: np.ndarray) -> np.ndarray:
    points = np.asarray(coordinates, dtype=float)
    return np.linalg.norm(points[:, None, :] - points[None, :, :], axis=2)


def tour_cost(tour, distances: np.ndarray) -> float:
    route = np.asarray(tour, dtype=int)
    return float(distances[route, np.roll(route, -1)].sum())


def two_opt_moves(n: int) -> list[tuple[int, int]]:
    """Corta dos aristas no adyacentes y revierte el segmento i+1,...,j."""
    return [(i, j) for i in range(n) for j in range(i + 2, n)
            if not (i == 0 and j == n - 1)]


def two_opt_delta(tour, distances, i: int, j: int) -> float:
    a, b = tour[i], tour[(i + 1) % len(tour)]
    c, d = tour[j], tour[(j + 1) % len(tour)]
    return float(distances[a, c] + distances[b, d]
                 - distances[a, b] - distances[c, d])


@dataclass
class SAResult:
    tour: list[int]
    best_cost: float
    initial_cost: float
    final_cost: float
    accepted: int
    accepted_worse: int
    trajectory: list[float]


def simulated_annealing(distances: np.ndarray, temperature: float, seed: int,
                        iterations: int = 500, cooling: float = 0.99) -> SAResult:
    if temperature <= 0 or iterations < 1 or not 0 < cooling < 1:
        raise ValueError("Temperatura e iteraciones positivas; enfriamiento entre 0 y 1")
    n = len(distances)
    moves = two_opt_moves(n)
    if not moves:
        raise ValueError("Se requieren al menos cuatro ciudades")
    rng = np.random.default_rng(seed)
    route = rng.permutation(n).tolist()
    initial = current = tour_cost(route, distances)
    best, best_route = current, route.copy()
    accepted = accepted_worse = 0
    trajectory = [best]
    for k in range(iterations):
        i, j = moves[int(rng.integers(len(moves)))]
        delta = two_opt_delta(route, distances, i, j)
        tk = max(temperature * cooling ** k, np.finfo(float).tiny)
        if delta <= 0 or rng.random() < math.exp(-delta / tk):
            route[i + 1:j + 1] = reversed(route[i + 1:j + 1])
            current += delta
            accepted += 1
            accepted_worse += int(delta > 1e-12)
            if current < best - 1e-10:
                best, best_route = current, route.copy()
        trajectory.append(best)
    # Recalcular evita que el redondeo acumulado afecte empates o inferencias.
    best = tour_cost(best_route, distances)
    trajectory[-1] = best
    return SAResult(best_route, best, initial, tour_cost(route, distances),
                    accepted, accepted_worse, trajectory)


def held_karp(distances: np.ndarray) -> tuple[float, list[int]]:
    """Óptimo exacto para validar; nunca participa en el recocido simulado."""
    n = len(distances)
    states: dict[tuple[int, int], tuple[float, int]] = {}
    for j in range(1, n):
        states[(1 << (j - 1), j)] = (float(distances[0, j]), 0)
    for mask in range(1, 1 << (n - 1)):
        cities = [j for j in range(1, n) if mask & (1 << (j - 1))]
        if len(cities) == 1:
            continue
        for j in cities:
            previous_mask = mask ^ (1 << (j - 1))
            states[(mask, j)] = min(
                (states[(previous_mask, k)][0] + float(distances[k, j]), k)
                for k in cities if k != j)
    mask = (1 << (n - 1)) - 1
    optimum, end = min((states[(mask, j)][0] + float(distances[j, 0]), j)
                       for j in range(1, n))
    reverse_path = []
    while end:
        reverse_path.append(end)
        previous = states[(mask, end)][1]
        mask ^= 1 << (end - 1)
        end = previous
    return float(optimum), [0] + reverse_path[::-1]
