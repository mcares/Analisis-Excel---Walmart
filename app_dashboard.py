# app_dashboard.py – Dashboard NPS Avanzado + PDF
# ───────────────────────────────────────────────
import io, datetime, copy
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.graph_objects import Figure
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config("Dashboard NPS Avanzado", layout="wide")

# ---------- utilidades PDF ----------
def fig_to_bytes(fig: Figure, w=800, h=500) -> bytes:
    try:
        f = copy.deepcopy(fig)
        f.update_layout(template="plotly_white",
                        paper_bgcolor="white", plot_bgcolor="white")
        return f.to_image(format="png", width=w, height=h, engine="kaleido")
    except Exception:  # kaleido no disponible
        return b""

def build_pdf(kpis, figs):
    buff = io.BytesIO()
    pdf  = canvas.Canvas(buff, pagesize=A4)
    W, H = A4
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(W/2, H-70, "Reporte NPS – Walmart Chile")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(W/2, H-100, datetime.date.today().isoformat())
    pdf.showPage()
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, H-80, "Indicadores clave")
    pdf.setFont("Helvetica", 12)
    y = H-110
    for k, v in kpis.items():
        pdf.drawString(50, y, f"{k}: {v}")
        y -= 18
    pdf.showPage()
    for title, fig in figs:
        img = fig_to_bytes(fig)
        if img:
            pdf.drawImage(ImageReader(io.BytesIO(img)),
                          40, 180, width=W-80, preserveAspectRatio=True)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, 160, title)
        pdf.showPage()
    pdf.save(); buff.seek(0); return buff.read()

# ---------- Cargar datos ----------
df = pd.read_excel("outputs/resultado_nps.xlsx")
df["fecha_hora_de_apertura"] = pd.to_datetime(df["fecha_hora_de_apertura"],
                                              errors="coerce")
for col in ["Tipo", "causa_principal", "categoria",
            "id_ejecutivo_resolutor_de_caso", "es_recuperable"]:
    df[col] = df[col].astype(str)

def seg(n):  # clasifica NPS
    if n >= 9: return "Promotor"
    if n >= 7: return "Neutro"
    return "Detractor"
df["segmento"] = df["NPS"].apply(seg)

# ---------- Sidebar filtros ----------
with st.sidebar:
    st.title("Filtros")
    seg_sel = st.multiselect("Segmento NPS",
                             ["Promotor", "Neutro", "Detractor"],
                             default=["Promotor", "Neutro", "Detractor"])
    df = df[df["segmento"].isin(seg_sel)]
    fecha_min = df["fecha_hora_de_apertura"].min().date()
    fecha_max = df["fecha_hora_de_apertura"].max().date()
    rango = st.date_input("Rango Apertura", (fecha_min, fecha_max))
    if len(rango) == 2:
        df = df[
            (df["fecha_hora_de_apertura"].dt.date >= rango[0]) &
            (df["fecha_hora_de_apertura"].dt.date <= rango[1])
        ]
# ---------- KPI generales ----------
total_casos   = len(df)
pct_prom      = round((df["segmento"] == "Promotor").mean()  * 100, 1)
pct_neut      = round((df["segmento"] == "Neutro").mean()    * 100, 1)
pct_detr      = round((df["segmento"] == "Detractor").mean() * 100, 1)
nps_val       = round(pct_prom - pct_detr, 1)          # fórmula NPS real

# ---------- Tarjetas visuales ----------
st.header("Dashboard NPS Avanzado – Walmart Chile")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total encuestas", f"{total_casos:,}")
col2.metric("% Promotores",   f"{pct_prom} %",     delta=None)
col3.metric("% Neutros",      f"{pct_neut} %")
col4.metric("% Detractores",  f"{pct_detr} %")
col5.metric("NPS",            f"{nps_val}")

# ---------- Evolución temporal ----------
ts = (df.set_index("fecha_hora_de_apertura")
        .resample("W")["NPS"]
        .mean()
        .reset_index())

fig_evo = px.line(
    ts, x="fecha_hora_de_apertura", y="NPS",
    title="Evolución semanal de NPS",
    template="plotly_white"
)
st.plotly_chart(fig_evo, use_container_width=True)   # ya no necesitas k2.plotly_chart

# ---------- Tabla Agente × Mes con NPS (%) ----------
df["mes"] = df["fecha_hora_de_apertura"].dt.to_period("M").astype(str)

conteos = (df.groupby(["id_ejecutivo_resolutor_de_caso", "mes", "segmento"])
             .size()
             .unstack(fill_value=0))

for col in ["Promotor", "Detractor"]:
    conteos[col] = conteos.get(col, 0)

conteos["Total"] = conteos.sum(axis=1)
conteos["NPS"]   = ((conteos["Promotor"] - conteos["Detractor"])
                    / conteos["Total"] * 100).round(1)

tabla_nps = (conteos["NPS"]
             .unstack(level="mes")
             .sort_index())

# Si quieres ordenar por NPS promedio en vez de alfabético:
# tabla_nps = tabla_nps.loc[tabla_nps.mean(axis=1).sort_values(ascending=False).index]

st.subheader("NPS (%) por agente y mes")
st.dataframe(
    tabla_nps.style.background_gradient(
        cmap="RdYlGn",     # rojo → amarillo → verde
        axis=None),
    use_container_width=True
)



# =====================================================================
#            BLOQUE → “Análisis de resultados”
# =====================================================================
st.markdown("## Análisis de resultados")

# --- Filtro LOCAL por segmento ---
segmento_local = st.radio("Selecciona segmento:", ["Promotor", "Neutro", "Detractor"],
                          index=0, horizontal=True)
df_local = df[df["segmento"] == segmento_local]

# Top 5 categorías (de causas)
top_cats = (df_local["categoria"]
              .value_counts()
              .head(5)
              .reset_index(name="conteo")
              .rename(columns={"index": "categoria"}))

fig_top = px.bar(top_cats, x="conteo", y="categoria",
                 orientation="h",
                 title=f"Top 5 categorías – {segmento_local}",
                 template="plotly_white")

# Matriz Categoría × Causa principal (detalles)
mat = (df_local.groupby(["categoria", "causa_principal"])
                   .size()
                   .reset_index(name="casos"))
pivot_mat = mat.pivot_table(index="causa_principal",
                            columns="categoria",
                            values="casos",
                            fill_value=0)

c1, c2 = st.columns(2)
c1.plotly_chart(fig_top, use_container_width=True)
c2.subheader("Detalle por causa principal")
c2.dataframe(
    pivot_mat.style.background_gradient(cmap="Blues", axis=None),
    use_container_width=True
)

# ---------- Recuperables ----------
r1, r2 = st.columns(2)
rec = (df["es_recuperable"]
         .replace({"True": "Recuperable", "False": "No Recuperable"})
         .value_counts(normalize=True)
         .reset_index())
rec.columns = ["estado", "proporcion"]
fig_rec = px.pie(rec, names="estado", values="proporcion",
                 title="Recuperables vs No", template="plotly_white")
r1.plotly_chart(fig_rec, use_container_width=True)

nr = df[df["es_recuperable"] == "No Recuperable"]
r2.subheader("Comentarios No Recuperables")
for _, row in nr.iterrows():
    r2.markdown(f"> **{row['numero_del_caso']}**: {row['Walmart LTR - Comentario']}")

st.subheader("Recomendaciones (No recuperables)")
for _, row in nr.iterrows():
    st.markdown(f"- {row['recomendacion']}")

# ---------- Tabla detalle ----------
st.subheader("Detalle de casos")
st.dataframe(
    df[[
        "numero_del_caso", "fecha_hora_de_apertura", "segmento", "Tipo",
        "categoria", "causa_principal", "es_recuperable",
        "id_ejecutivo_resolutor_de_caso", "recomendacion"
    ]],
    use_container_width=True
)

# ---------- PDF ----------
if st.button("📄 Descargar PDF"):
    kpi_dict = {"Total": total, "NPS": nps_val}
    figs = [
        ("Evolución NPS", fig_evo),
        ("NPS Agente x Mes (tabla)", px.imshow(tabla_nps)),  # captura rápida
        (f"Top 5 categorías – {segmento_local}", fig_top),
        ("Recuperables vs No", fig_rec)
    ]
    pdf_bytes = build_pdf(kpi_dict, figs)
    st.download_button("Descargar PDF", pdf_bytes,
                       "reporte_nps_avanzado.pdf", mime="application/pdf")