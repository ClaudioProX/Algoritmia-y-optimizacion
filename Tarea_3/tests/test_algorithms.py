"""Verificaciones de integridad numérica y de las soluciones devueltas."""
import itertools
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from analysis import balanced_anova, bootstrap_median
from sa_tsp import distance_matrix,held_karp,simulated_annealing,tour_cost,two_opt_delta,two_opt_moves


class NumericalChecks(unittest.TestCase):
    def test_delta_matches_full_recomputation(self):
        for n in [5,10,15]:
            rng=np.random.default_rng(930+n)
            d=distance_matrix(rng.uniform(0,100,(n,2)))
            route=rng.permutation(n).tolist()
            for i,j in two_opt_moves(n):
                changed=route.copy()
                changed[i+1:j+1]=reversed(changed[i+1:j+1])
                self.assertAlmostEqual(two_opt_delta(route,d,i,j),tour_cost(changed,d)-tour_cost(route,d),places=10)

    def test_exact_solver_matches_enumeration(self):
        d=distance_matrix(np.random.default_rng(822).uniform(0,100,(6,2)))
        brute=min(tour_cost([0]+list(p),d) for p in itertools.permutations(range(1,6)))
        optimum,route=held_karp(d)
        self.assertAlmostEqual(brute,optimum,places=10)
        self.assertEqual(sorted(route),list(range(6)))
        self.assertAlmostEqual(tour_cost(route,d),optimum,places=10)

    def test_annealing_integrity_and_reproducibility(self):
        d=distance_matrix(np.random.default_rng(55).uniform(0,100,(10,2)))
        first=simulated_annealing(d,33.0,42)
        second=simulated_annealing(d,33.0,42)
        optimum,_=held_karp(d)
        self.assertEqual(first,second)
        self.assertEqual(sorted(first.tour),list(range(10)))
        self.assertLessEqual(first.best_cost,first.initial_cost+1e-8)
        self.assertGreaterEqual(first.best_cost,optimum-1e-8)
        self.assertTrue(np.all(np.diff(first.trajectory)<=1e-8))

    def test_anova_matches_nested_least_squares(self):
        y=np.random.default_rng(721).normal(size=(3,3,10))
        ai,bj=np.indices((3,3,10))[:2].reshape(2,-1)
        av=np.eye(3)[ai][:,1:]
        bv=np.eye(3)[bj][:,1:]
        interactions=np.column_stack([av[:,i]*bv[:,j] for i in range(2) for j in range(2)])
        base=np.column_stack([np.ones(y.size),av,bv])
        full=np.column_stack([base,interactions])
        def sse(x):
            residual=y.ravel()-x@np.linalg.lstsq(x,y.ravel(),rcond=None)[0]
            return residual@residual
        table=balanced_anova(y).set_index("fuente")
        error=sse(full)
        self.assertAlmostEqual(error,table.loc["Error","SC"],places=10)
        self.assertAlmostEqual(sse(base)-error,table.loc["Interacción","SC"],places=10)
        self.assertAlmostEqual(sse(np.column_stack([np.ones(y.size),bv]))-sse(base),table.loc["Temperatura","SC"],places=10)
        self.assertAlmostEqual(table.loc[["Temperatura","Tamaño","Interacción","Error"],"SC"].sum(),table.loc["Total","SC"],places=10)
        self.assertEqual(table.gl.tolist(),[2,2,4,81,89])

    def test_constant_bootstrap_has_zero_width(self):
        result=bootstrap_median([17.5]*10,934)
        self.assertEqual(result["mediana_bootstrap"],17.5)
        self.assertEqual(result["IC95_inf"],17.5)
        self.assertEqual(result["IC95_sup"],17.5)


if __name__=="__main__":
    unittest.main()
