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
    layout="wide"
)

# =========================
# ESTILO BOSCH
# =========================
st.markdown("""
<style>
body {
    background-color: #f5f7f9;
    font-family: 'Segoe UI', sans-serif;
}
h1, h2, h3 {
    color: #005691;
    font-weight: bold;
}
.stButton > button {
    background-color: #005691;
    color: white;
    border-radius: 6px;
    font-weight: bold;
    padding: 0.5em 1em;
}
.stButton > button:hover {
    background-color: #003f6b;
}
.stTextInput>div>div>input {
    padding: 0.5em;
}
label {
    color: #003f6b !important;
    font-weight: bold;
}
.sidebar .sidebar-content {
    background-color: #005691;
    color: white;
}
.card {
    border-radius: 10px;
    padding: 1em;
    margin-bottom: 1em;
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =========================
# CONSTANTES
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
USUARIOS_FILE = "usuarios.xlsx"

COLOR_ESTATUS = {
    "En cotización": "#FFD700",
    "En alta": "#1E90FF",
    "Info Record": "#FFA500",
    "Completado": "#32CD32"
}

# =========================
# FUNCIONES LOGIN
# =========================
def crear_usuario(correo, contrasena):
    df = pd.DataFrame([[correo, contrasena]], columns=["Correo", "Contraseña"])
    if os.path.exists(USUARIOS_FILE):
        df_existente = pd.read_excel(USUARIOS_FILE)
        if correo in df_existente["Correo"].values:
            st.error("❌ Este correo ya está registrado.")
            return False
        df_final = pd.concat([df_existente, df], ignore_index=True)
    else:
        df_final = df
    df_final.to_excel(USUARIOS_FILE, index=False)
    return True

def validar_usuario(correo, contrasena):
    if os.path.exists(USUARIOS_FILE):
        df = pd.read_excel(USUARIOS_FILE)
        usuario = df[(df["Correo"]==correo) & (df["Contraseña"]==contrasena)]
        if not usuario.empty:
            return True
    return False

# =========================
# SESIÓN
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

# =========================
# LOGIN
# =========================
if not st.session_state.login:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Bosch_logo.svg/2560px-Bosch_logo.svg.png", width=200)
    st.title("🔧 Alta de Materiales – Bosch")
    st.subheader("Inicia sesión con tu correo Bosch")

    correo = st.text_input("Correo Bosch")
    contrasena = st.text_input("Contraseña", type="password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Iniciar sesión"):
            if correo.lower().endswith("@mx.bosch.com") and validar_usuario(correo, contrasena):
                st.session_state.login = True
                st.success("✅ Sesión iniciada correctamente")
                st.experimental_rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
    with col2:
        if st.button("Registrarse"):
            if correo.lower().endswith("@mx.bosch.com") and contrasena:
                if crear_usuario(correo, contrasena):
                    st.success("✅ Usuario registrado. Ahora inicia sesión.")
            else:
                st.error("❌ Solo correos Bosch MX permitidos y contraseña no vacía")

# =========================
# APP PRINCIPAL
# =========================
if st.session_state.login:
    # Sidebar
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Bosch_logo.svg/2560px-Bosch_logo.svg.png", width=150)
    st.sidebar.title("Menú")
    st.sidebar.markdown("---")
    opcion = st.sidebar.radio("", ["📝 Alta de material", "📊 Estatus de materiales", "📈 Dashboard", "🚪 Cerrar sesión"])

    if opcion == "📝 Alta de material":
        st.header("📝 Alta de material")
        with st.form("form_alta_material"):
            col1, col2 = st.columns(2)
            with col1:
                linea = st.selectbox("Línea", list(LINEAS.keys()))
                estacion = st.text_input("Estación")
                descripcion = st.text_area("Descripción del material")
            with col2:
                proveedor = st.text_input("Proveedor sugerido")
                cantidad = st.number_input("Cantidad req_

