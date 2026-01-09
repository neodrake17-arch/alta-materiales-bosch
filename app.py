import streamlit as st
import pandas as pd
from datetime import datetime
import os

# =========================
# CONFIGURACIÓN GENERAL
# =========================
st.set_page_config(
    page_title="Alta de Materiales | Bosch",
    page_icon="🔧",
    layout="centered"
)

# =========================
# ESTILO BOSCH
# =========================
st.markdown("""
<style>
body {
    background-color: #f5f7f9;
}
h1, h2, h3 {
    color: #005691;
}
.stButton > button {
    background-color: #005691;
    color: white;
    border-radius: 6px;
    font-weight: bold;
}
.stButton > button:hover {
    background-color: #003f6b;
}
label {
    color: #003f6b !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LINEAS → RESPONSABLE
# =========================
LINEAS = {
    "APA 36": {"responsable": "Lalo", "correo": "lalo@bosch.com"},
    "APA 38": {"responsable": "Lalo", "correo": "lalo@bosch.com"},
    "DP 02": {"responsable": "Jarol", "correo": "jarol@bosch.com"},
    "DP 32": {"responsable": "Jime", "correo": "jime@bosch.com"},
    "SCU 48": {"responsable": "Jarol", "correo": "jarol@bosch.com"},
    "SSL1": {"responsable": "Jarol", "correo": "jarol@bosch.com"}
}

ARCHIVO_EXCEL = "alta_materiales.xlsx"

# =========================
# TÍTULO
# =========================
st.title("🔧 Alta de Materiales – Bosch")

st.markdown("""
Esta aplicación sustituye el Excel compartido y permite:
- Control de estatus
- Seguimiento por línea
- Visualización futura por gráficas
""")

# =========================
# FORMULARIO
# =========================
with st.form("form_alta_material"):
    col1, col2 = st.columns(2)

    with col1:
        solicitante = st.text_input("Ingeniero solicitante")
        linea = st.selectbox("Línea", list(LINEAS.keys()))
        estacion = st.text_input("Estación")
        descripcion = st.text_area("Descripción del material")

    with col2:
        proveedor = st.text_input("Proveedor sugerido")
        cantidad = st.number_input("Cantidad requerida", min_value=1)
        prioridad = st.selectbox("Prioridad", ["Normal", "Crítica"])
        imagen = st.file_uploader("Imagen del material", type=["jpg", "png", "jpeg"])

    enviar = st.form_submit_button("Registrar material")

# =========================
# GUARDADO
# =========================
if enviar:
    responsable = LINEAS[linea]["responsable"]
    correo = LINEAS[linea]["correo"]

    nuevo_registro = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Solicitante": solicitante,
        "Línea": linea,
        "Estación": estacion,
        "Descripción": descripcion,
        "Proveedor": proveedor,
        "Cantidad": cantidad,
        "Prioridad": prioridad,
        "Responsable": responsable,
        "Correo responsable": correo,
        "Estatus": "En cotización"
    }

    df_nuevo = pd.DataFrame([nuevo_registro])

    if os.path.exists(ARCHIVO_EXCEL):
        df_existente = pd.read_excel(ARCHIVO_EXCEL)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo

    df_final.to_excel(ARCHIVO_EXCEL, index=False)

    st.success("✅ Material registrado correctamente")
    st.info(f"📧 Responsable asignado: {responsable}")
