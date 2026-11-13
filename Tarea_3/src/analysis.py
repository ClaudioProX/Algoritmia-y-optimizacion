"""ANOVA balanceado de dos factores e IC percentiles de la mediana."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def balanced_anova(values: np.ndarray) -> pd.DataFrame:
    """Ejes: temperatura, tamaño, réplica. Fórmulas de NIST, efectos fijos."""
    y = np.asarray(values, dtype=float)
    if y.ndim != 3 or not np.isfinite(y).all() or min(y.shape) < 2:
        raise ValueError("Se requiere un arreglo balanceado finito de tres ejes")
    a, b, r = y.shape
    grand = y.mean()
    am, bm, cells = y.mean(axis=(1, 2)), y.mean(axis=(0, 2)), y.mean(axis=2)
    ss_a = b * r * np.sum((am - grand) ** 2)
    ss_b = a * r * np.sum((bm - grand) ** 2)
    ss_ab = r * np.sum((cells - am[:, None] - bm[None, :] + grand) ** 2)
    ss_e = np.sum((y - cells[:, :, None]) ** 2)
    ss_t = np.sum((y - grand) ** 2)
    error_df = a * b * (r - 1)
    mse = ss_e / error_df
    if mse <= 0:
        raise ValueError("Sin varianza residual, la prueba F no está definida")
    rows = []
    for label, ss, df in [("Temperatura", ss_a, a-1), ("Tamaño", ss_b, b-1),
                           ("Interacción", ss_ab, (a-1)*(b-1))]:
        f_value = ss / df / mse
        rows.append(dict(fuente=label, SC=ss, gl=df, CM=ss/df, F=f_value,
                         p=stats.f.sf(f_value, df, error_df)))
    rows.extend([dict(fuente="Error", SC=ss_e, gl=error_df, CM=mse, F=np.nan, p=np.nan),
                 dict(fuente="Total", SC=ss_t, gl=y.size-1, CM=np.nan, F=np.nan, p=np.nan)])
    return pd.DataFrame(rows)


def bootstrap_median(values, seed: int, resamples: int = 20000) -> dict:
    sample = np.asarray(values, dtype=float)
    if sample.ndim != 1 or len(sample) < 2:
        raise ValueError("Se requieren al menos dos observaciones")
    rng = np.random.default_rng(seed)
    distribution = np.median(rng.choice(sample, size=(resamples, len(sample)),
                                       replace=True), axis=1)
    lower, upper = np.quantile(distribution, [0.025, 0.975])
    return dict(mediana=float(np.median(sample)),
                mediana_bootstrap=float(np.median(distribution)),
                IC95_inf=float(lower), IC95_sup=float(upper))


def holm_adjust(p_values) -> np.ndarray:
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p)
    adjusted = np.minimum(1, np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order]))
    result = np.empty_like(p)
    result[order] = adjusted
    return result


def analyze(frame: pd.DataFrame, temperatures: list[float], matricula: int):
    sizes = [5, 10, 15]
    values = np.array([[frame[(frame.n == n) & (frame.nivel_id == level)]
                       .sort_values("replica").costo.to_numpy()
                       for n in sizes] for level in range(3)])
    anova = balanced_anova(values)
    rows = []
    for n in sizes:
        for level, temperature in enumerate(temperatures):
            group = frame[(frame.n == n) & (frame.nivel_id == level)]
            boot_seed = matricula + 200000 + n * 100 + level
            boot = bootstrap_median(group.costo, boot_seed)
            rows.append(dict(n=n, nivel_id=level, nivel=["Bajo","Medio","Alto"][level],
                             temperatura=temperature, replicas=len(group),
                             media=group.costo.mean(), desviacion=group.costo.std(ddof=1),
                             minimo=group.costo.min(), maximo=group.costo.max(),
                             exitos_optimo=int((group.brecha_pct.abs() < 1e-7).sum()),
                             semilla_bootstrap=boot_seed, **boot))
    summary = pd.DataFrame(rows)
    selected = []
    for n in sizes:
        group = summary[summary.n == n]
        candidates = group[np.isclose(group.mediana, group.mediana.min(), rtol=0, atol=1e-8)]
        median_ties = candidates.nivel.tolist()
        candidates = candidates[np.isclose(candidates.media, candidates.media.min(), rtol=0, atol=1e-8)]
        row = candidates.sort_values("temperatura").iloc[0].to_dict()
        row["empates_mediana"] = ", ".join(median_ties)
        selected.append(row)
    residual = (values - values.mean(axis=2, keepdims=True)).ravel()
    shapiro = stats.shapiro(residual)
    levene = stats.levene(*[values[i,j] for i in range(3) for j in range(3)], center="median")
    diagnostics = dict(shapiro_W=float(shapiro.statistic), shapiro_p=float(shapiro.pvalue),
                       levene_W=float(levene.statistic), levene_p=float(levene.pvalue))
    # Sensibilidad al incumplimiento de normalidad o igualdad de varianzas.
    kw = []
    for j, n in enumerate(sizes):
        # Rutas equivalentes difieren hasta 1e-13 por el orden de la suma.
        # Colapsar ese ruido evita asignar rangos distintos a empates reales.
        all_costs = np.round(values[:,j,:], 10)
        if np.ptp(all_costs) < 1e-8:
            statistic, p_value = 0.0, 1.0
        else:
            result = stats.kruskal(*all_costs)
            statistic, p_value = float(result.statistic), float(result.pvalue)
        kw.append(dict(n=n,H=statistic,p=p_value))
    sensitivity = pd.DataFrame(kw)
    sensitivity["p_Holm"] = holm_adjust(sensitivity.p)
    return anova, summary, pd.DataFrame(selected), diagnostics, sensitivity
