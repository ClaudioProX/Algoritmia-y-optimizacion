"""Generar el reporte del experimento."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def set_font(owner):
    owner.font.name="Arial"
    owner.font.size=Pt(12)
    owner.font.color.rgb=RGBColor(0,0,0)
    prop=owner.element.get_or_add_rPr() if hasattr(owner.element,"get_or_add_rPr") else None
    if prop is not None:
        fonts=prop.find(qn("w:rFonts"))
        if fonts is not None:
            for key in list(fonts.attrib):
                if key.endswith("Theme"):
                    del fonts.attrib[key]
            for key in ["ascii","hAnsi","eastAsia","cs"]:
                fonts.set(qn("w:"+key),"Arial")
        color=prop.find(qn("w:color"))
        if color is not None:
            for key in list(color.attrib):
                if key!=qn("w:val"):
                    del color.attrib[key]


def hyperlink(paragraph,label,url):
    rel=paragraph.part.relate_to(url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",is_external=True)
    element=OxmlElement("w:hyperlink");element.set(qn("r:id"),rel)
    run=OxmlElement("w:r");props=OxmlElement("w:rPr")
    font=OxmlElement("w:rFonts")
    for key in ["ascii","hAnsi","eastAsia","cs"]:font.set(qn("w:"+key),"Arial")
    props.append(font)
    size=OxmlElement("w:sz");size.set(qn("w:val"),"24");props.append(size)
    color=OxmlElement("w:color");color.set(qn("w:val"),"000000");props.append(color)
    run.append(props);text=OxmlElement("w:t");text.text=label;run.append(text)
    element.append(run);paragraph._p.append(element)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-url",default="https://github.com/ClaudioProX/Algoritmia-y-optimizacion")
    args=parser.parse_args()
    config=json.loads((ROOT/"results/configuracion.json").read_text())
    cells=pd.read_csv(ROOT/"results/resumen_celdas.csv")
    anova=pd.read_csv(ROOT/"results/anova.csv")
    best=pd.read_csv(ROOT/"results/temperaturas_seleccionadas.csv")
    sensitivity=pd.read_csv(ROOT/"results/sensibilidad_kruskal.csv")
    diag=json.loads((ROOT/"results/diagnosticos.json").read_text())
    doc=Document(ROOT/"assets/Portada_AYO.docx")
    # Conservar la sección inicial del documento base.
    for style in doc.styles:
        if hasattr(style,"font"):
            set_font(style)
    for p in doc.paragraphs:
        for run in p.runs:
            set_font(run)
    for name in ["Title","Heading 1","Heading 2"]:
        style=doc.styles[name]
        style.font.bold=True
        style.font.italic=False
        pf=style.paragraph_format
        pf.space_before=Pt(12 if name!="Title" else 0)
        pf.space_after=Pt(8)
        pf.line_spacing=1.158333
        pf.keep_with_next=True
        for border in style.element.xpath(".//w:pBdr"):
            border.getparent().remove(border)
    section=doc.add_section(WD_SECTION_START.NEW_PAGE)
    section.top_margin=section.bottom_margin=section.left_margin=section.right_margin=Inches(1)
    section.header_distance=section.footer_distance=Inches(.5)
    section.different_first_page_header_footer=False
    # El encabezado normal del original ya está vacío; los logos están en el primero.
    section.header.is_linked_to_previous=False
    for p in section.header.paragraphs:p.clear()
    section.footer.is_linked_to_previous=False
    for p in section.footer.paragraphs:p.clear()

    def p(text="",style=None):
        paragraph=doc.add_paragraph(text,style=style)
        paragraph.alignment=WD_ALIGN_PARAGRAPH.LEFT
        for run in paragraph.runs:set_font(run)
        return paragraph
    def h(text):return p(text,"Heading 1")
    def page(title):
        paragraph=h(title)
        paragraph.paragraph_format.page_break_before=True
        paragraph.paragraph_format.space_before=Pt(0)
        return paragraph
    def table(headers,rows,widths):
        t=doc.add_table(rows=1,cols=len(headers))
        t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
        for column,width in zip(t.columns,widths):column.width=Inches(width)
        for i,text in enumerate(headers):t.rows[0].cells[i].text=str(text)
        for values in rows:
            for cell,value in zip(t.add_row().cells,values):cell.text=str(value)
        for row_index,row in enumerate(t.rows):
            no_split=OxmlElement("w:cantSplit");row._tr.get_or_add_trPr().append(no_split)
            for cell,width in zip(row.cells,widths):
                cell.width=Inches(width);cell.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
                props=cell._tc.get_or_add_tcPr()
                margins=OxmlElement("w:tcMar")
                for edge in ["top","left","bottom","right"]:
                    item=OxmlElement("w:"+edge);item.set(qn("w:w"),"75")
                    item.set(qn("w:type"),"dxa");margins.append(item)
                props.append(margins)
                shading=OxmlElement("w:shd");shading.set(qn("w:fill"),"FFFFFF");props.append(shading)
                for para in cell.paragraphs:
                    para.paragraph_format.space_after=Pt(0)
                    para.paragraph_format.line_spacing=1.0
                    para.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    for run in para.runs:
                        set_font(run);run.bold=(row_index==0)
        borders=OxmlElement("w:tblBorders")
        for edge in ["top","left","bottom","right","insideH","insideV"]:
            item=OxmlElement("w:"+edge);item.set(qn("w:val"),"single")
            item.set(qn("w:sz"),"4");item.set(qn("w:color"),"000000");borders.append(item)
        t._tbl.tblPr.append(borders)
        repeat=OxmlElement("w:tblHeader");t.rows[0]._tr.get_or_add_trPr().append(repeat)
        after=p();after.paragraph_format.space_after=Pt(0)
        after.paragraph_format.line_spacing=0.4
        return t
    def figure(name,caption):
        paragraph=p();paragraph.alignment=WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after=Pt(4)
        paragraph.paragraph_format.keep_with_next=True
        paragraph.add_run().add_picture(str(ROOT/"figures"/name),width=Inches(6.1))
        p(caption)
    def number(v):return f"{float(v):.3f}"
    def prob(v):return f"{float(v):.3e}" if float(v)<.001 else f"{float(v):.5f}"

    p("Tarea 3","Title")
    p("Ajuste de temperatura mediante diseño de experimentos","Title")
    if args.repo_url:
        para=p("Repositorio público: ");hyperlink(para,args.repo_url,args.repo_url)
    h("Objetivo y resultado general")
    p("Evalué la temperatura inicial del recocido simulado con movimientos 2-opt para el problema del agente viajero (TSP). El objetivo fue reducir la longitud de la mejor ruta encontrada con un presupuesto fijo de búsqueda, a partir del algoritmo aplicado en el ejercicio 4 de la Tarea 2.")
    p("Elegí la opción A y ejecuté 90 corridas. Las temperaturas seleccionadas fueron 3.428, 33.128 y 3.428 para 5, 10 y 15 ciudades, respectivamente. Son las mejores selecciones observadas con el criterio definido en este reporte. El ANOVA no encontró un efecto significativo de la temperatura ni de su interacción con el tamaño al nivel de 0.05.")
    h("Diseño experimental")
    p("El diseño factorial completo combinó tres temperaturas con tres tamaños, n = 5, 10 y 15. Utilicé una instancia fija por tamaño y diez réplicas independientes por combinación: 3 × 3 × 10 = 90 corridas. El tamaño actuó como bloque y se incluyó como segundo factor en el ANOVA con interacción.")
    p(f"Generé un único valor r = {config['r']:.15f} con random.Random(2140485).random(). Lo mantuve fijo durante todo el experimento. Definí el rango de temperatura de 1 a 100 y convertí cada fracción a temperatura mediante T0 = 1 + fracción × 99.")
    table(["Nivel","Fracción","Temperatura T0","Corridas"],
          [[name,f"{fraction:.9f}",f"{temperature:.9f}",30]
           for name,fraction,temperature in zip(["Bajo","Medio","Alto"],config["fracciones"],config["temperaturas"])],
          [.9,1.5,2.6,1.5])
    p("Las fracciones fueron 0.3r, 0.3r + 0.3 y 0.3r + 0.6. El rango permite contrastar una búsqueda poco permisiva con otras que aceptan más deterioros: un aumento de costo de 10 se acepta inicialmente con probabilidades aproximadas de 0.054, 0.739 y 0.853, respectivamente.")

    page("Implementación del recocido simulado")
    p("Cada instancia contiene ciudades con coordenadas uniformes en el cuadrado de 0 a 100. El costo es la suma de distancias euclidianas de un recorrido cerrado que visita cada ciudad una vez y vuelve al inicio. La respuesta experimental es el menor costo encontrado durante la corrida; un valor menor representa una mejor solución.")
    h("Procedimiento")
    for text in [
        "1. Generar una permutación aleatoria de las ciudades como recorrido inicial.",
        "2. Elegir uniformemente dos aristas no adyacentes y proponer la inversión del segmento intermedio mediante 2-opt.",
        "3. Calcular la diferencia de costo usando las cuatro distancias afectadas. Aceptar cualquier mejora; si el costo aumenta, aceptar con probabilidad exp(−Δ/T).",
        "4. Multiplicar la temperatura por 0.99 y repetir hasta completar 500 movimientos propuestos, incluso si se alcanza una solución estable.",
        "5. Conservar la mejor ruta visitada y recalcular su costo con la matriz de distancias antes de registrarla."
    ]:p(text)
    table(["Condición","Valor"],[
        ["Temperatura ajustada","T0 en tres niveles"],
        ["Enfriamiento geométrico","Factor 0.99 por movimiento"],
        ["Presupuesto","500 propuestas por corrida"],
        ["Réplicas por combinación","10 semillas diferentes"],
        ["Instancias","Una fija para cada tamaño"],
        ["Remuestras bootstrap","20000 por combinación"],
    ],[3.25,3.25])
    p("Las semillas de las instancias fueron 2141490, 2141495 y 2141500. Para una réplica j de 1 a 10 y nivel l de 0 a 2, usé la semilla de corrida 2140485 × 10000 + n × 100 + l × 10 + j. Las 90 semillas son distintas. Aleatoricé el orden de ejecución con la semilla 2190485.")
    p("La configuración se guardó antes de ejecutar el diseño. No seleccioné semillas ni descarté resultados. Calculé por separado el óptimo exacto de cada instancia con programación dinámica de Held-Karp para validar las soluciones; ese resultado no intervino en la búsqueda ni en su parada.")

    page("Resultados de las 90 corridas")
    p("La tabla reúne las diez réplicas de cada combinación. Los costos están expresados en unidades de distancia y redondeados a tres decimales. La columna Óptimos indica cuántas corridas alcanzaron el óptimo exacto de su instancia.")
    table(["n","Nivel","T0","Media","Mediana","Desv.","Óptimos"],
          [[int(row.n),row.nivel,number(row.temperatura),number(row.media),number(row.mediana),
            number(row.desviacion),f"{int(row.exitos_optimo)}/10"] for row in cells.itertuples()],
          [.4,.75,.9,1.12,1.12,1.12,1.09])
    p("En n = 5, las 30 corridas alcanzaron el costo óptimo de 232.728. En n = 10, las tres medianas empataron en 322.390, aunque el nivel bajo falló en una corrida. En n = 15, el nivel bajo obtuvo la menor mediana, mientras que el nivel medio tuvo una media ligeramente menor. El nivel alto presentó mayor dispersión.")
    figure("06_convergencia_n15.png","Figura 1. Convergencia media de la mejor solución acumulada para n = 15. Cada curva resume diez corridas y todas usan el mismo presupuesto de 500 propuestas.")

    page("ANOVA de dos factores")
    p("Ajusté un modelo de efectos fijos que separa el costo en media general, efecto de temperatura, efecto de tamaño, interacción y error. El ANOVA compara las medias, mientras que la mediana se utiliza después como criterio práctico de selección. En este diseño balanceado, la descomposición de sumas de cuadrados sigue las fórmulas de NIST [1].")
    p("Para cada fuente dividí su suma de cuadrados (SC) entre sus grados de libertad (gl) para obtener el cuadrado medio (CM). El estadístico F compara ese CM con el CM del error. La regla de decisión fijada fue p < 0.05. Los grados de libertad son 2, 2, 4 y 81, con 89 en total.")
    table(["Fuente","SC","gl","CM","F","p"],
          [[row.fuente,number(row.SC),int(row.gl),"—" if pd.isna(row.CM) else number(row.CM),
            "—" if pd.isna(row.F) else number(row.F),"—" if pd.isna(row.p) else prob(row.p)]
           for row in anova.itertuples()],
          [1.18,1.32,.35,1.27,1.03,1.45])
    p("Temperatura: F = 1.632 y p = 0.20199. No se rechaza la igualdad de las medias marginales. Las diferencias observadas no bastan para afirmar que un nivel de temperatura mejora el costo de forma general.")
    p("Tamaño: F = 2527.622 y p = 1.029 × 10⁻⁷³. Bajo el modelo clásico, el costo difiere entre los bloques. Como solo hay una instancia por tamaño, este resultado combina tamaño y geometría de la instancia; no demuestra una ley general de escalamiento.")
    p("Interacción: F = 2.367 y p = 0.05955. No resulta significativa con el umbral fijado. Que su p esté cerca de 0.05 no justifica cambiar la regla después de observar los datos.")
    h("Comprobación complementaria")
    p("Los diagnósticos de la última sección cuestionan los supuestos del ANOVA. Como comprobación exploratoria, comparé los niveles dentro de cada tamaño con Kruskal-Wallis [5] y ajusté las tres pruebas mediante Holm. Los p ajustados fueron 1.00000, 0.73576 y 0.07396 para n = 5, 10 y 15. Ninguno es menor que 0.05. Esto tampoco demuestra equivalencia entre temperaturas.")

    page("Gráficas de efectos principales")
    figure("01_efecto_temperatura.png","Figura 2. Efecto principal de la temperatura. Cada punto es el costo promedio de 30 corridas, promediando los tres tamaños.")
    figure("02_efecto_tamano.png","Figura 3. Efecto principal del tamaño. Cada punto resume 30 corridas, promediando los tres niveles de temperatura.")
    p("Las medias por temperatura fueron 312.635, 311.289 y 315.078. La diferencia es pequeña frente a la separación de costos entre tamaños. Estos promedios marginales no sustituyen la selección por bloque.")

    page("Interacción y temperatura seleccionada")
    figure("03_interaccion.png","Figura 4. Interacción entre temperatura y tamaño. Cada punto promedia diez corridas. Las líneas identifican los tres tamaños del problema.")
    p("La curva de n = 5 permanece plana; en n = 10 el costo medio baja del nivel bajo al medio y después se mantiene. En n = 15 aumenta en el nivel alto. Este patrón visual no cambia la conclusión del ANOVA: la interacción no alcanzó significancia al nivel de 0.05.")
    h("Selección por tamaño y bootstrap")
    p("Fijé el criterio de menor mediana de costo. Ante un empate numérico con tolerancia de 0.00000001, elegí la menor media y después la menor temperatura. Con 20000 remuestras de tamaño diez, con reemplazo, calculé la mediana bootstrap y su IC percentil del 95 % [2].")
    table(["n","T0 elegida","Mediana bootstrap","IC del 95 %","Óptimos"],
          [[int(row.n),number(row.temperatura),number(row.mediana_bootstrap),
            f"[{number(row.IC95_inf)}, {number(row.IC95_sup)}]",f"{int(row.exitos_optimo)}/10"]
           for row in best.itertuples()],
          [.35,1.0,1.6,2.55,1.0])
    p("En n = 5 empataron los tres niveles y se eligió el menor T0. En n = 10 empataron las medianas; el medio y el alto también empataron en media, por lo que se eligió el medio. En n = 15 el nivel bajo obtuvo la menor mediana. Estas selecciones no prueban superioridad estadística.")

    page("Validación y conclusiones")
    h("Diagnóstico estadístico")
    table(["Prueba","Estadístico","p"],[
        ["Shapiro-Wilk",f"W = {diag['shapiro_W']:.3f}",prob(diag["shapiro_p"])],
        ["Levene con mediana",f"W = {diag['levene_W']:.3f}",prob(diag["levene_p"])],
    ],[2.75,1.6,2.15])
    p("Shapiro-Wilk sobre los residuos rechaza normalidad [4] y Levene entre las nueve celdas rechaza igualdad de varianzas [3]. Las celdas constantes y los costos altos aislados limitan el ANOVA: sus p deben leerse como evidencia exploratoria bajo supuestos que no se cumplen.")
    p("El tamaño fue significativo bajo ese modelo; se presenta el bootstrap de las configuraciones seleccionadas por bloque. Los IC de ancho cero reflejan costos iguales o mayoritariamente iguales. No prueban certeza sobre nuevas instancias ni corrigen el sesgo de seleccionar y evaluar con las mismas corridas.")
    h("Respuesta a las preguntas analíticas")
    p("La temperatura elegida cambia de 3.428 a 33.128 y vuelve a 3.428. No hay una tendencia monótona entre n y T0, y dos selecciones dependen de desempates. Estos resultados no permiten afirmar que la temperatura óptima aumente con el tamaño.")
    p("Para n = 15 selecciono el nivel bajo por su mediana. El medio tiene menor costo promedio; otro criterio puede cambiar la decisión. Generalizar requiere más instancias por tamaño y corridas independientes de confirmación.")
    h("Validación y reproducción")
    p("Las cinco pruebas verificaron 2-opt, el óptimo exacto, la integridad y repetibilidad del recocido, el ANOVA y el bootstrap. El proyecto conserva datos, semillas, código y gráficas. Se reproduce con python src/experiment.py; véase README.md.")
    h("Referencias")
    refs=[
        ("[1] NIST. The two-way ANOVA. Engineering Statistics Handbook. ","Consultar fuente","https://www.itl.nist.gov/div898/handbook/prc/section4/prc437.htm"),
        ("[2] SciPy 1.17.0. Bootstrap e intervalos percentiles. ","Documentación","https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.bootstrap.html"),
        ("[3] SciPy 1.17.0. Prueba de Levene. ","Documentación","https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.levene.html"),
        ("[4] SciPy 1.17.0. Prueba de Shapiro-Wilk. ","Documentación","https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.shapiro.html"),
        ("[5] SciPy 1.17.0. Prueba de Kruskal-Wallis. ","Documentación","https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.stats.kruskal.html"),
    ]
    for lead,label,url in refs:
        para=p(lead);hyperlink(para,label,url)
        para.paragraph_format.space_after=Pt(4)
    doc.core_properties.title="Tarea 3 Ajuste de temperatura mediante diseño de experimentos"
    doc.core_properties.author="Claudio Correa Torres"
    doc.core_properties.subject="Algoritmia y optimización"
    doc.core_properties.keywords="TSP, recocido simulado, DOE, ANOVA, bootstrap"
    (ROOT/"report").mkdir(exist_ok=True)
    output=ROOT/"report/Tarea_3_Claudio_Correa.docx"
    doc.save(output)
    print(output)


if __name__=="__main__":main()
