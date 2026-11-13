# Tarea 3 Ajuste de temperatura mediante DOE

Claudio Correa Torres · Matrícula 2140485 · Algoritmia y optimización

Repositorio público: [ClaudioProX/Algoritmia-y-optimizacion](https://github.com/ClaudioProX/Algoritmia-y-optimizacion).
Este proyecto corresponde a la carpeta `Tarea_3/` dentro del repositorio.

Se implementó la **opción A**, un diseño factorial de tres temperaturas por tres
tamaños de TSP, con diez réplicas por celda y 90 corridas en total. El recocido
simulado parte de una solución aleatoria, usa movimientos 2-opt y conserva la mejor
ruta visitada. Los resultados incluidos se obtuvieron ejecutando el programa.

## Ejecutar

Requiere Python 3.11 o posterior. Desde esta carpeta:

```bash
python -m venv .venv
```

Activa el entorno virtual según tu sistema. Después:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/experiment.py
```

La última instrucción vuelve a generar las instancias, las 90 observaciones, los
resúmenes y las gráficas. Para conservar los resultados originales, usa una carpeta
de salida distinta:

```bash
python src/experiment.py --output reproduccion
```

Los costos, rutas, ANOVA y bootstrap se reproducen con las semillas fijadas y las
versiones indicadas. `tiempo_s` mide la duración real de cada corrida y cambia entre
ejecuciones y equipos. Los tiempos no intervienen en la selección de temperatura.

## Archivos

| Carpeta o archivo | Contenido |
| --- | --- |
| `src/sa_tsp.py` | Costo del TSP, movimientos 2-opt, recocido y validación exacta |
| `src/experiment.py` | Generación y ejecución del diseño fijado |
| `src/analysis.py` | ANOVA balanceado, bootstrap y análisis de sensibilidad |
| `src/plots.py` | Gráficas de resultados y diagnósticos |
| `tests/test_algorithms.py` | Cinco verificaciones numéricas y de integridad |
| `data/instances/` | Coordenadas de una instancia por tamaño |
| `data/corridas.csv` | Las 90 corridas, semillas, costos, rutas y tiempos |
| `data/trayectorias.csv` | Mejor costo acumulado por iteración y corrida |
| `results/` | Configuración, ANOVA, bootstrap, selección y diagnósticos |
| `figures/` | Imágenes PNG y versiones PDF de las gráficas |
| `report/` | Reporte editable y reporte en PDF |
| `assets/Portada_AYO.docx` | Documento base de la primera página |
| `tools/build_report.py` | Generador del documento con la portada |

## Diseño y decisiones fijadas

- Se genera un solo `r` con `random.Random(2140485).random()`, igual a
  `0.08175124691477531`.
- Rango de temperatura: de 1 a 100. Las fracciones son `0.3*r + 0.3*j` para
  `j = 0, 1, 2`. Se convierten con `1 + fraccion * 99`.
- Temperaturas sin redondear: `3.4280120333688266`, `33.128012033368826` y
  `62.82801203336882`. Los experimentos no usan los valores redondeados del reporte.
- Se usa una instancia por tamaño, con coordenadas uniformes en `[0,100)`.
  Sus semillas son `2141490`, `2141495` y `2141500`.
- Cada corrida propone 500 movimientos. La temperatura se multiplica por 0.99
  después de cada propuesta. Se registra la mejor solución, no necesariamente la
  última solución visitada.
- Las semillas de corrida son `2140485*10000 + n*100 + nivel*10 + replica`, donde
  `nivel` va de 0 a 2 y `replica` de 1 a 10. Son 90 semillas distintas.
- La semilla de aleatorización del orden de ejecución es `2190485`.
- Se selecciona la menor mediana; los empates dentro de una tolerancia absoluta
  de `1e-8` se resuelven por menor media y después por menor temperatura.
- Bootstrap: 20000 remuestras de tamaño diez con reemplazo; intervalos percentiles
  2.5 y 97.5. Semilla por celda: `2140485 + 200000 + n*100 + nivel`.

El ANOVA se calcula con las fórmulas del diseño factorial balanceado de NIST. No
requiere statsmodels. Una prueba independiente verifica las sumas de cuadrados
frente al ajuste por mínimos cuadrados. Los residuos y las varianzas no cumplen los
supuestos clásicos, por lo que se añade un diagnóstico y una comprobación
exploratoria con Kruskal-Wallis y corrección de Holm. Para asignar rangos, los
costos se redondean a diez decimales; esto elimina diferencias de redondeo entre
rutas equivalentes. La celda constante de n = 5 no permite diferenciar temperaturas.

## Resultados

| n | T0 seleccionada | Mediana bootstrap | IC del 95 % |
| --- | --- | --- | --- |
| 5 | 3.428012033 | 232.727838 | [232.727838, 232.727838] |
| 10 | 33.128012033 | 322.390356 | [322.390356, 322.390356] |
| 15 | 3.428012033 | 377.956234 | [377.956234, 378.888183] |

El ANOVA da p = 0.201994 para temperatura y p = 0.059550 para interacción. No se
rechazan esas hipótesis con alfa = 0.05. Las selecciones son empíricas, dos dependen
de desempates y no prueban superioridad estadística. Con una instancia por tamaño
no puede generalizarse una tendencia de temperatura óptima. Los intervalos
bootstrap describen la muestra por configuración y no corrigen el sesgo de
seleccionar y evaluar con las mismas observaciones.

## Reporte y repositorio

Para reconstruir el Word:

```bash
python tools/build_report.py
```

El generador incluye la dirección del repositorio de forma predeterminada. También
puedes indicarla explícitamente:

```bash
python tools/build_report.py --repo-url https://github.com/ClaudioProX/Algoritmia-y-optimizacion
```

Después de reconstruir el Word, exporta de nuevo a PDF desde Word o LibreOffice.
En Linux con LibreOffice:

```bash
soffice --headless --convert-to pdf --outdir report report/Tarea_3_Claudio_Correa.docx
```

## Referencias

- [NIST The two-way ANOVA](https://www.itl.nist.gov/div898/handbook/prc/section4/prc437.htm)
- [SciPy bootstrap](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.bootstrap.html)
- [SciPy Levene](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.levene.html)
- [SciPy Shapiro-Wilk](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.shapiro.html)
- [SciPy Kruskal-Wallis](https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.kruskal.html)
