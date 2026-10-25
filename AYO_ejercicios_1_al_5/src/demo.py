"""Demostracion real de cada ejercicio, sin cargar resultados precalculados."""
import argparse, statistics as st, time, random
import experimentos as e

def demo(n):
 print(f'EJERCICIO {n}: EJECUCION DE LOS ALGORITMOS',flush=True)
 if n==1:
  import multiprocessing as mp
  ctx=mp.get_context('fork' if 'fork' in mp.get_all_start_methods() else 'spawn')
  times=[]
  print('8 tareas x 1 000 000 muestras; carga fija.',flush=True)
  for p in [1,2,4,8]:
   t=time.perf_counter()
   with ctx.Pool(p) as pool:v=pool.map(e.estimate_pi,range(8),chunksize=1)
   elapsed=time.perf_counter()-t;times.append(elapsed)
   print(f'p={p}  pi={sum(v)/8:.7f}  segundos={elapsed:.3f}  speedup={times[0]/elapsed:.2f}',flush=True)
  print('Demo: una repeticion. El reporte usa medianas de cinco.',flush=True)
 elif n==2:
  items=[('A',3,2),('B',4,3),('C',24,8)]
  print('Capacidad = 10; objetos (valor,peso): A(3,2), B(4,3), C(24,8)',flush=True)
  for key in ['weight','ratio']:
   v=e.greedy_knapsack(items,10,key)
   print(f'{key}: objetos={v["chosen"]}  peso={v["weight"]}  valor={v["value"]}',flush=True)
 elif n==3:
  rows,_=e.local_search_experiment()
  for i in [1,10,20,30]:
   a=[x for x in rows if x['instance']==i]
   print(f'Instancia {i:02d}: aleatorio={a[0]["improvements"]:2d}; NN(nodo {a[1]["initial_node"]:2d})={a[1]["improvements"]:2d} mejoras',flush=True)
  for name in ['Random','NN']:
   a=[x for x in rows if x['start']==name]
   print(f'{name}: media mejoras={st.mean(x["improvements"] for x in a):.2f}; costo final={st.mean(x["final_length"] for x in a):.2f}',flush=True)
 elif n==4:
  rows,_=e.annealing_experiment()
  for name in ['G0.90','G0.97','G0.995','Linear']:
   a=[x for x in rows if x['schedule']==name]
   print(f'{name}: 20 repeticiones; propuestas={a[0]["proposals"]}; costo medio={st.mean(x["final_length"] for x in a):.2f}',flush=True)
  print('Se calcularon 80 soluciones mediante recocido simulado.',flush=True)
 elif n==5:
  print('100 instancias x 9 ciudades; OPT por fuerza bruta (8!).',flush=True)
  rows,_=e.approximation_experiment()
  for key in ['mst','mst_2opt','local_random','local_nn','sa']:
   print(f'{key:12s}: costo medio={st.mean(x[key] for x in rows):.4f}; optimos={sum(abs(x[key]/x["optimal"]-1)<1e-9 for x in rows)}/100',flush=True)
  print('Todos los metodos usaron las mismas instancias.',flush=True)
 print('EJECUCION FINALIZADA CORRECTAMENTE',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ejercicio',type=int,required=True,choices=range(1,6));demo(p.parse_args().ejercicio)
