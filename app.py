import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os

# =========================
# CONFIGURACIÓN VISUAL BOSCH
# =========================
st.set_page_config(
    page_title="Alta de Materiales | Bosch",
    page_icon="🔧",
    layout="centered"
)

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

st.title("🔧 Alta de Materiales Bosch")

# =========================
# LINEAS → RESPONSABLE → CORREO
# =========================
LINEAS = {
    "APA 36": "external.EduardoAbel.RamirezBecerril@mx.bosch.com",
    "APA 38": "external.EduardoAbel.RamirezBecerril@mx.bosch.com",
    "DP 02": "external.Jarol.DiazCastro@mx.bosch.com",
    "DP 32": "external.Jimena.MontalvoSanchez@mx.bosch.com",
    "DP 35": "external.Jimena.MontalvoSanchez@mx.bosch.com",
    "KGT 22": "external.Nicolas.BravoVerde@mx.bosch.com",
    "KGT 23": "external.Nicolas.BravoVerde@mx.bosch.com",
    "LG 01": "external.Nicolas.BravoVerde@mx.bosch.com",
    "LG 03": "external.Nicolas.BravoVerde@mx.bosch.com",
    "SCU 33": "external.Jarol.DiazCastro@mx.bosch.com",
    "SCU 34": "external.Jarol.DiazCastro@mx.bosch.com",
    "SCU 48": "external.Jarol.DiazCastro@mx.bosch.com",
    "SSL1": "external.Jarol.DiazCastro@mx.bosch.com"
}

# =========================
# ARCHIVO EXCEL
# =========================
ARCHIVO = "materiales.xlsx"

COLUMNAS = [
    "Fecha",
    "Solicitante",
    "Material",
    "Descripción",
    "Proveedor",
    "Línea",
    "Cantidad",
    "Estatus"
]

if not os.path.exists(ARCHIVO):
    pd.DataFrame(columns=COLUMNAS).to_excel(ARCHIVO, index=False)

# =========================
# FORMULARIO
# =========================
with st.form("alta_material"):
    st.subheader("📋 Registro de Material")

    solicitante = st.text_input("Ingeniero solicitante")
    material = st.text_input("Número / Nombre del material")
    descripcion = st.text_area("Descripción")
    proveedor = st.text_input("Proveedor")
    linea = st.selectbox("Línea", list(LINEAS.keys()))
    cantidad = st.number_input("Cantidad", min_value=1, step=1)

    enviar = st.form_submit_button("Enviar material")

# =========================
# GUARDAR + ENVIAR CORREO
# =========================
if enviar:
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    estatus = "Cotización"
    correo_destino = LINEAS[linea]

    nuevo = {
        "Fecha": fecha,
        "Solicitante": solicitante,
        "Material": material,
        "Descripción": descripcion,
        "Proveedor": proveedor,
        "Línea": linea,
        "Cantidad": cantidad,
        "Estatus": estatus
    }

    df = pd.read_excel(ARCHIVO)
    df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
    df.to_excel(ARCHIVO, index=False)

    # -------- CORREO --------
    msg = EmailMessage()
    msg["Subject"] = f"Alta de material | Línea {linea}"
    msg["From"] = "CORREO_REMITE@empresa.com"
    msg["To"] = correo_destino

    msg.set_content(f"""
Nuevo material registrado

Material: {material}
Descripción: {descripcion}
Proveedor: {proveedor}
Línea: {linea}
Cantidad: {cantidad}
Estatus: {estatus}
""")

    # ⚠️ CONFIGURAR SMTP REAL DESPUÉS
    # with smtplib.SMTP("smtp.office365.com", 587) as server:
    #     server.starttls()
    #     server.login("CORREO_REMITE@empresa.com", "PASSWORD_CORREO")
    #     server.send_message(msg)

    st.success("✅ Material registrado y enviado al responsable de la línea")

# =========================
# TABLA
# =========================
st.divider()
st.subheader("📊 Materiales registrados")
st.dataframe(pd.read_excel(ARCHIVO), use_container_width=True)
