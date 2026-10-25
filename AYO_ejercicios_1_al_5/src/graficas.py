"""Genera las visualizaciones exigidas a partir de resultados.json."""
import argparse, json, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

BLUE, GOLD, GRAY, GREEN, PURPLE = '#244B70','#B07C25','#777E86','#278376','#8061A1'
COLORS=[BLUE,GOLD,GRAY,GREEN,PURPLE]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','grid.color':'#E4E7EB','savefig.facecolor':'white'})

def make_figures(source, out):
 r=json.loads(Path(source).read_text(encoding='utf-8'))
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 def save(fig,name):
  fig.savefig(out/name,dpi=240,bbox_inches='tight',pad_inches=.14);plt.close(fig)
 def box(ax,data,labels,colors):
  b=ax.boxplot(data,tick_labels=labels,patch_artist=True,widths=.5,medianprops={'color':'#182C3D','linewidth':1.7},flierprops={'markersize':3})
  for patch,c in zip(b['boxes'],colors):patch.set_facecolor(c);patch.set_alpha(.62)
  ax.grid(axis='y',alpha=.8);ax.set_axisbelow(True)
 # 1: aceleracion y linea ideal.
 p=[1,2,4,8];t=[st.median(x['seconds'] for x in r['parallel'] if x['processes']==n) for n in p]
 fig,ax=plt.subplots(figsize=(7.5,3.15));s=[t[0]/x for x in t]
 ax.plot(p,p,'--',color=GRAY,label='Ideal');ax.plot(p,s,'o-',color=BLUE,label='Medida')
 ax.set(xlabel='Procesos',ylabel='Aceleración S(p)',xticks=p,ylim=(0,9));ax.grid(axis='y');ax.legend(frameon=False);fig.tight_layout();save(fig,'ejercicio_1.png')
 # 2: comparacion de valor y capacidad, ademas de la tabla del reporte.
 fig,axes=plt.subplots(1,2,figsize=(8,3.1))
 for ax,key,title in zip(axes,['weight','value'],['Capacidad usada (W = 10)','Valor total']):
  vals=[r['knapsack'][x][key] for x in ['weight','ratio']]
  ax.bar(['Menor peso\nA + B','Valor / peso\nC + A'],vals,color=[GRAY,BLUE],width=.5)
  for i,v in enumerate(vals):ax.text(i,v+.3,str(v),ha='center',fontweight='bold')
  ax.set(title=title,ylim=(0,max(vals)*1.22));ax.grid(axis='y');ax.set_axisbelow(True)
 fig.tight_layout();save(fig,'ejercicio_2.png')
 # 3: distribuciones de mejoras y calidad, 30 pares de instancias.
 groups=[[x for x in r['local'] if x['start']==n] for n in ['Random','NN']]
 fig,axes=plt.subplots(1,2,figsize=(8.4,3.5))
 for ax,key,title in zip(axes,['improvements','final_length'],['Mejoras para converger','Calidad del óptimo local']):
  data=[[x[key] for x in a] for a in groups]
  box(ax,data,['Aleatorio','Vecino cercano\nnodo inicial aleatorio'],[GRAY,BLUE])
  ax.set(title=title,ylabel='Movimientos aceptados' if key=='improvements' else 'Longitud final (menor es mejor)')
  for i,a in enumerate(data):ax.scatter(i+1,st.mean(a),color='#B07C25',marker='D',s=30,zorder=5,label='Media' if i==0 else None)
 axes[0].legend(frameon=False,loc='upper right',fontsize=9)
 fig.tight_layout(w_pad=2);save(fig,'ejercicio_3.png')
 # 4: curvas de estado actual de una repeticion y relacion directa tiempo/calidad.
 names=['G0.90','G0.97','G0.995','Linear'];labels=['Geom. 0,90','Geom. 0,97','Geom. 0,995','Lineal']
 fig,ax=plt.subplots(figsize=(8.4,3.4))
 for name,label,c in zip(names,labels,COLORS):
  h=r['sa_example']['traces'][name];ax.plot([50*k for k in range(len(h))],h,label=label,color=c,linewidth=1.4,alpha=.9)
 ax.set_xscale('symlog',linthresh=50);ax.set(xlabel='Movimientos 2-opt propuestos (escala simétrica logarítmica)',ylabel='Longitud del estado actual',xticks=[0,50,500,5000,50000],xticklabels=['0','50','500','5 000','50 000'])
 ax.grid(alpha=.7);ax.legend(ncol=2,frameon=False,fontsize=9);fig.tight_layout();save(fig,'ejercicio_4_convergencia.png')
 fig,ax=plt.subplots(figsize=(8.4,3.3))
 for name,label,c in zip(names,labels,COLORS):
  a=[x for x in r['sa'] if x['schedule']==name]
  ts=[x['seconds']*1000 for x in a];ys=[x['final_length'] for x in a]
  ax.scatter(ts,ys,s=16,alpha=.27,color=c)
  ax.errorbar(st.mean(ts),st.mean(ys),xerr=st.stdev(ts),yerr=st.stdev(ys),fmt='o',capsize=4,color=c,markersize=7,label=label)
 ax.set(xlabel='Tiempo de búsqueda (ms)',ylabel='Longitud final (menor es mejor)');ax.grid(alpha=.7);ax.legend(ncol=2,frameon=False,fontsize=9,loc='upper right');fig.tight_layout();save(fig,'ejercicio_4_tiempo_calidad.png')
 # 5: razon y costos de todos los metodos sobre las mismas instancias.
 fig,ax=plt.subplots(figsize=(8.4,3.3));a=r['approx']
 ax.scatter([x['instance'] for x in a],[x['ratio_mst'] for x in a],s=15,color=BLUE,label='MST puro')
 ax.scatter([x['instance'] for x in a],[x['ratio_2opt'] for x in a],s=13,color=GOLD,label='MST + 2-opt')
 ax.axhline(2,color=GRAY,linestyle='--',label='Cota teórica 2');ax.axhline(1,color='#B7BABE',linewidth=1)
 ax.set(xlabel='Instancia de 9 ciudades',ylabel='Costo / óptimo exacto',ylim=(.97,2.08));ax.grid(axis='y');ax.legend(ncol=3,frameon=False,fontsize=9);fig.tight_layout();save(fig,'ejercicio_5_razones.png')
 keys=['mst','mst_2opt','local_random','local_nn','sa','optimal']
 labels=['MST\npuro','MST +\n2-opt','2-opt\naleatorio','2-opt\nvecino cercano','Recocido\nsimulado','Óptimo\nexacto']
 fig,ax=plt.subplots(figsize=(8.4,3.6))
 box(ax,[[x[k] for x in a] for k in keys],labels,COLORS+['#C4C9CE'])
 ax.set(ylabel='Costo del recorrido (unidades euclidianas)',title='Comparación sobre las mismas 100 instancias de 9 ciudades')
 fig.tight_layout();save(fig,'ejercicio_5_costos.png')
 fig,axes=plt.subplots(1,2,figsize=(8.4,3.2));w=r['worst']
 for ax,key,title,c in zip(axes,['mst_route','improved_route'],['MST puro','MST + 2-opt'],[BLUE,GOLD]):
  route=w[key]+[w[key][0]];ax.plot([w['points'][i][0] for i in route],[w['points'][i][1] for i in route],'-o',color=c)
  for i,(x,y) in enumerate(w['points']):ax.annotate(str(i),(x,y),xytext=(3,3),textcoords='offset points',fontsize=9)
  ax.set(title=f'{title}: {w["row"]["mst" if key=="mst_route" else "mst_2opt"]:.2f}',xlabel='x',ylabel='y',xlim=(0,10),ylim=(0,10));ax.set_aspect('equal');ax.grid(alpha=.5)
 fig.tight_layout();save(fig,'ejercicio_5_rutas.png')
 print('Generadas 8 figuras: ejercicios 1, 2, 3, 4 (2) y 5 (3).',flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('resultados/resultados.json'));p.add_argument('--out',type=Path,default=Path('figuras'));a=p.parse_args();make_figures(a.source,a.out)
