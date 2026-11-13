"""Ejecutar una sola vez el diseño fijado antes de observar resultados."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import random
import time

import numpy as np
import pandas as pd

from analysis import analyze
from plots import create_figures
from sa_tsp import distance_matrix, held_karp, simulated_annealing

MATRICULA = 2140485
ITERATIONS = 500
COOLING = 0.99


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    root=args.output.resolve()
    for directory in ["data/instances","results","figures"]:
        (root/directory).mkdir(parents=True,exist_ok=True)
    # Único r: no se reutiliza su generador en ninguna otra etapa.
    r=random.Random(MATRICULA).random()
    fractions=[0.3*r+0.3*j for j in range(3)]
    temperatures=[1+fraction*(100-1) for fraction in fractions]
    configuration=dict(matricula=MATRICULA,r=r,T_min=1,T_max=100,
                       fracciones=fractions,temperaturas=temperatures,
                       tamanos=[5,10,15],replicas=10,iteraciones=ITERATIONS,
                       enfriamiento=COOLING,remuestras_bootstrap=20000,
                       criterio="mediana mínima; empate: media; empate: menor T0",
                       semilla_orden=MATRICULA+50000)
    # Se escribe la configuración antes de generar datos experimentales.
    (root/"results/configuracion.json").write_text(json.dumps(configuration,indent=2),encoding="utf-8")
    instances={}
    exact={}
    for n in [5,10,15]:
        coordinates=np.random.default_rng(MATRICULA+1000+n).uniform(0,100,size=(n,2))
        pd.DataFrame({"ciudad":range(n),"x":coordinates[:,0],"y":coordinates[:,1]}).to_csv(
            root/f"data/instances/tsp_{n}.csv",index=False)
        instances[n]=distance_matrix(coordinates)
        optimum,route=held_karp(instances[n])
        exact[n]=dict(costo=optimum,ruta=route,semilla_instancia=MATRICULA+1000+n)
    (root/"results/optimos_exactos.json").write_text(json.dumps(exact,indent=2),encoding="utf-8")
    design=[(n,level,replica) for n in [5,10,15] for level in range(3)
            for replica in range(1,11)]
    random.Random(MATRICULA+50000).shuffle(design)
    rows,history=[],[]
    for order,(n,level,replica) in enumerate(design,1):
        seed=MATRICULA*10000+n*100+level*10+replica
        start=time.perf_counter()
        result=simulated_annealing(instances[n],temperatures[level],seed,ITERATIONS,COOLING)
        elapsed=time.perf_counter()-start
        rows.append(dict(orden=order,n=n,nivel_id=level,nivel=["Bajo","Medio","Alto"][level],
                         temperatura=temperatures[level],replica=replica,semilla=seed,
                         costo=result.best_cost,costo_inicial=result.initial_cost,
                         costo_final=result.final_cost,aceptados=result.accepted,
                         peores_aceptados=result.accepted_worse,tiempo_s=elapsed,
                         optimo_exacto=exact[n]["costo"],
                         brecha_pct=100*(result.best_cost/exact[n]["costo"]-1),
                         ruta=" ".join(map(str,result.tour))))
        history.extend(dict(n=n,nivel_id=level,replica=replica,iteracion=k,mejor_costo=c)
                       for k,c in enumerate(result.trajectory))
    frame=pd.DataFrame(rows)
    trajectories=pd.DataFrame(history)
    frame.to_csv(root/"data/corridas.csv",index=False)
    trajectories.to_csv(root/"data/trayectorias.csv",index=False)
    anova,summary,selected,diagnostics,sensitivity=analyze(frame,temperatures,MATRICULA)
    for name,data in [("anova",anova),("resumen_celdas",summary),("temperaturas_seleccionadas",selected),
                      ("sensibilidad_kruskal",sensitivity)]:
        data.to_csv(root/f"results/{name}.csv",index=False)
    (root/"results/diagnosticos.json").write_text(json.dumps(diagnostics,indent=2),encoding="utf-8")
    versions={name:importlib.metadata.version(name) for name in ["numpy","pandas","scipy","matplotlib"]}
    (root/"results/versiones.json").write_text(json.dumps(versions,indent=2),encoding="utf-8")
    create_figures(frame,summary,trajectories,root/"figures")
    print("Diseño ejecutado: 90 corridas independientes, sin seleccionar ni descartar resultados.")
    print("\nANOVA\n",anova.to_string(index=False))
    print("\nCELDAS\n",summary.to_string(index=False))
    print("\nSELECCIÓN\n",selected[["n","nivel","temperatura","mediana_bootstrap","IC95_inf","IC95_sup","empates_mediana"]].to_string(index=False))
    print("\nDIAGNÓSTICOS\n",diagnostics)
    print("\nSENSIBILIDAD\n",sensitivity.to_string(index=False))


if __name__ == "__main__":
    main()
