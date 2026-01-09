import streamlit as st
import pandas as pd
from datetime import datetime
import os

# =========================
# CONFIGURACIÓN DE LA APP
# =========================
st.set_page_config(
    page_title="Alta de Materiales | Bosch",
    page_icon="🔧",
    layout="centered"
)

st.title("🔧 Alta de Materiales Bosch")

# =========================
# ARCHIVO EXCEL
# =========================
ARCHIVO_EXCEL = "materiales.xlsx"

COLUMNAS = [
    "Fecha",
    "Solicitante",
    "Material",
    "Descripción",
    "Proveedor",
    "Línea",
    "Cantidad",
    "Practicante",
    "Estatus"
]

# Crear Excel si no existe
if not os.path.exists(ARCHIVO_EXCEL):
    df_init = pd.DataFrame(columns=COLUMNAS)
    df_init.to_excel(ARCHIVO_EXCEL, index=False)

# =========================
# FORMULARIO DE ALTA
# =========================
with st.form("form_alta_material"):
    st.subheader("Formulario de Alta de Material")

    solicitante = st.text_input("Solicitante (Ingeniero)")
    material = st.text_input("Número / Nombre del material")
    descripcion = st.text_area("Descripción del material")
    proveedor = st.text_input("Proveedor")
    linea = st.text_input("Línea / Área")
    cantidad = st.number_input("Cantidad", min_value=1, step=1)
    practicante = st.selectbox(
        "Practicante asignado",
        ["Jarol", "Jime", "Lalo", "Niko"]
    )

    enviar = st.form_submit_button("Guardar material")

# =========================
# GUARDAR EN EXCEL
# =========================
if enviar:
    nuevo_registro = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Solicitante": solicitante,
        "Material": material,
        "Descripción": descripcion,
        "Proveedor": proveedor,
        "Línea": linea,
        "Cantidad": cantidad,
        "Practicante": practicante,
        "Estatus": "Cotización"
    }

    df = pd.read_excel(ARCHIVO_EXCEL)
    df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
    df.to_excel(ARCHIVO_EXCEL, index=False)

    st.success("✅ Material guardado correctamente con estatus: COTIZACIÓN")

# =========================
# TABLA DE MATERIALES
# =========================
st.divider()
st.subheader("📋 Materiales registrados")

df_view = pd.read_excel(ARCHIVO_EXCEL)
st.dataframe(df_view, use_container_width=True)
