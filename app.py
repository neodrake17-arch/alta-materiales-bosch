import streamlit as st
import streamlit_authenticator as stauth
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
[data-testid="stSidebar"] {
    background-color: #005691;
}
[data-testid="stSidebar"] * {
    color: white;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
names = ["Ing. Juan", "Ing. Maria", "Practicante 1"]
usernames = ["juan", "maria", "prac1"]
passwords = ["1234", "abcd", "test123"]

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    "alta_materiales_bosch",
    "cookie_bosch_key",
    cookie_expiry_days=365
)

name, authentication_status, username = authenticator.login(
    "Inicio de sesión | Bosch", "main"
)

# =========================
# VALIDACIÓN LOGIN
# =========================
if authentication_status is False:
    st.error("Usuario o contraseña incorrectos")

elif authentication_status is None:
    st.warning("Ingresa tus credenciales")

elif authentication_status:

    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.markdown(f"👤 **Usuario:** {name}")

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
    # SIDEBAR MENU
    # =========================
    menu = st.sidebar.radio(
        "Menú",
        ["📝 Alta de material", "📊 Estatus de materiales", "📈 Dashboard"]
    )

    # =========================
    # ALTA DE MATERIAL
    # =========================
    if menu == "📝 Alta de material":
        st.title("📝 Alta de Materiales")

        with st.form("form_alta"):
            col1, col2 = st.columns(2)

            with col1:
                linea = st.selectbox("Línea", list(LINEAS.keys()))
                estacion = st.text_input("Estación")
                descripcion = st.text_area("Descripción del material")

            with col2:
                proveedor = st.text_input("Proveedor sugerido")
                cantidad = st.number_input("Cantidad", min_value=1)
                prioridad = st.selectbox("Prioridad", ["Normal", "Crítica"])

            enviar = st.form_submit_button("Registrar material")

        if enviar:
            responsable = LINEAS[linea]["responsable"]
            correo = LINEAS[linea]["correo"]

            nuevo = {
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Registrado por": name,
                "Línea": linea,
                "Estación": estacion,
                "Descripción": descripcion,
                "Proveedor": proveedor,
                "Cantidad": cantidad,
                "Prioridad": prioridad,
                "Responsable": responsable,
                "Correo": correo,
                "Estatus": "🟡 En cotización"
            }

            df_nuevo = pd.DataFrame([nuevo])

            if os.path.exists(ARCHIVO_EXCEL):
                df = pd.read_excel(ARCHIVO_EXCEL)
                df = pd.concat([df, df_nuevo], ignore_index=True)
            else:
                df = df_nuevo

            df.to_excel(ARCHIVO_EXCEL, index=False)

            st.success("✅ Material registrado correctamente")
            st.info(f"Responsable asignado: {responsable}")

    # =========================
    # ESTATUS
    # =========================
    elif menu == "📊 Estatus de materiales":
        st.title("📊 Estatus de Materiales")

        if os.path.exists(ARCHIVO_EXCEL):
            df = pd.read_excel(ARCHIVO_EXCEL)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("Aún no hay materiales registrados")

    # =========================
    # DASHBOARD
    # =========================
    elif menu == "📈 Dashboard":
        st.title("📈 Dashboard")

        if os.path.exists(ARCHIVO_EXCEL):
            df = pd.read_excel(ARCHIVO_EXCEL)
            conteo = df["Estatus"].value_counts()
            st.bar_chart(conteo)
        else:
            st.warning("No hay datos para mostrar")




