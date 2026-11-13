"""Figuras en blanco y negro para el reporte."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from scipy import stats


def create_figures(frame, summary, trajectories, out: Path):
    available = {item.name for item in font_manager.fontManager.ttflist}
    family = "Arial" if "Arial" in available else "Liberation Sans"
    plt.rcParams.update({"font.family":family,"font.size":12,"axes.labelsize":12,
                         "axes.titlesize":12,"xtick.labelsize":12,"ytick.labelsize":12,
                         "legend.fontsize":12,"figure.dpi":150,"savefig.dpi":250,
                         "axes.spines.top":False,"axes.spines.right":False,
                         "axes.grid":True,"grid.color":"0.87","grid.linewidth":0.6})
    out.mkdir(parents=True, exist_ok=True)
    def save(fig, name):
        fig.savefig(out / (name+".png"), facecolor="white")
        fig.savefig(out / (name+".pdf"), facecolor="white")
        plt.close(fig)

    temperatures = summary[summary.n==5].temperatura.to_numpy()
    fig, ax = plt.subplots(figsize=(6.1,3.0),layout="constrained")
    means = frame.groupby("nivel_id").costo.mean()
    ax.plot(temperatures,means,"o-",color="black")
    ax.set(xlabel="Temperatura inicial T0",ylabel="Costo medio",xticks=temperatures,
           xticklabels=[f"{v:.3f}" for v in temperatures])
    save(fig,"01_efecto_temperatura")

    fig, ax = plt.subplots(figsize=(6.1,3.0),layout="constrained")
    ax.plot([5,10,15],frame.groupby("n").costo.mean(),"s-",color="black")
    ax.set(xlabel="Número de ciudades n",ylabel="Costo medio",xticks=[5,10,15])
    save(fig,"02_efecto_tamano")

    fig, ax = plt.subplots(figsize=(6.1,3.2),layout="constrained")
    for n,marker,style in [(5,"o","-"),(10,"s","--"),(15,"^",":")]:
        group=summary[summary.n==n]
        ax.plot(group.temperatura,group.media,marker=marker,linestyle=style,
                color="black",label=f"n = {n}")
    ax.set(xlabel="Temperatura inicial T0",ylabel="Costo medio",xticks=temperatures,
           xticklabels=[f"{v:.3f}" for v in temperatures])
    ax.legend(loc="lower right",bbox_to_anchor=(1,0.12),frameon=False)
    save(fig,"03_interaccion")

    fig, axes = plt.subplots(3,1,figsize=(6.1,7.1),layout="constrained")
    for ax,n in zip(axes,[5,10,15]):
        group=summary[summary.n==n]
        for level in range(3):
            sample=frame[(frame.n==n)&(frame.nivel_id==level)].costo.to_numpy()
            jitter=np.linspace(-0.075,0.075,len(sample))
            ax.scatter(level+jitter,sample,s=18,facecolors="none",edgecolors="0.55",zorder=2)
        ax.errorbar(range(3),group.mediana_bootstrap,
                    yerr=[group.mediana_bootstrap-group.IC95_inf,
                          group.IC95_sup-group.mediana_bootstrap],fmt="ko",capsize=5,zorder=3)
        ax.set_title(f"n = {n}")
        ax.set_xticks(range(3),[f"{v:.3f}" for v in temperatures])
        ax.set_ylabel("Costo")
        optimum=frame[frame.n==n].optimo_exacto.iloc[0]
        ax.axhline(optimum,color="0.35",linestyle="--",linewidth=1)
    axes[-1].set_xlabel("Temperatura inicial T0")
    save(fig,"04_bootstrap")

    residuals=frame.costo-frame.groupby(["n","nivel_id"]).costo.transform("mean")
    fitted=frame.groupby(["n","nivel_id"]).costo.transform("mean")
    fig,axes=plt.subplots(2,1,figsize=(6.1,6.0),layout="constrained")
    axes[0].scatter(fitted,residuals,color="black",s=18)
    axes[0].axhline(0,color="0.45",linestyle="--")
    axes[0].set(xlabel="Costo ajustado por celda",ylabel="Residuo")
    (q,order),(slope,intercept,_)=stats.probplot(residuals,dist="norm")
    axes[1].scatter(q,order,color="black",s=18)
    axes[1].plot(q,slope*q+intercept,color="0.45")
    axes[1].set(xlabel="Cuantil normal teórico",ylabel="Residuo ordenado")
    save(fig,"05_diagnosticos")

    fig,ax=plt.subplots(figsize=(6.1,2.8),layout="constrained")
    for level,style in enumerate(["-","--",":"]):
        group=trajectories[(trajectories.n==15)&(trajectories.nivel_id==level)]
        curve=group.groupby("iteracion").mejor_costo.mean()
        ax.plot(curve.index,curve,color="black",linestyle=style,
                label=f"T0 = {temperatures[level]:.3f}")
    ax.set(xlabel="Movimientos propuestos",ylabel="Mejor costo medio acumulado")
    ax.legend(loc="best")
    save(fig,"06_convergencia_n15")
