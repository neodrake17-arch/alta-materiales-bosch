import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------- CONFIGURACIÓN GENERAL ----------------
st.set_page_config(
    page_title="Alta de Materiales Bosch",
    layout="wide"
)

# ---------------- ESTILOS BOSCH ----------------
st.markdown("""
<style>
body { background-color: #ffffff; font-family: 'Arial', sans-serif; }
h1, h2, h3 { color: #005691; }
.stButton>button {
    background-color: #005691;
    color: white;
    border-radius: 8px;
    height: 40px;
}
.stTextInput>div>input, .stTextArea>div>textarea, .stSelectbox>div>div {
    border-radius: 8px;
    border: 1px solid #ccc;
    padding: 5px;
}
.stFileUploader>div>div>input {
    border-radius: 8px;
}
.sidebar .sidebar-content {
    background-color: #f5f5f5;
    padding: 20px;
}
.status-cotizacion { color: orange; font-weight: bold; }
.status-alta { color: blue; font-weight: bold; }
.status-info { color: purple; font-weight: bold; }
.status-ok { color: green; font-weight: bold; }
.card {
    padding: 15px;
    border-radius: 10px;
    background-color: #f0f0f0;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIN ----------------
USERS = {
    "admin": "bosch123",
    "practicante": "alta2026"
}

if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    st.title("🔐 Acceso – Alta de Materiales Bosch")
    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user in USERS and USERS[user] == pwd:
            st.session_state.logged = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ---------------- DICCIONARIO DE LÍNEAS ----------------
LINEAS = {
    "APA 36": {"responsable": "Lalo", "correo": "external.EduardoAbel.RamirezBecerril@mx.bosch.com"},
    "APA 38": {"responsable": "Lalo", "correo": "external.EduardoAbel.RamirezBecerril@mx.bosch.com"},
    "DP 02": {"responsable": "Jarol", "correo": "external.Jarol.DiazCastro@mx.bosch.com"},
    "DP 32": {"responsable": "Jime", "correo": "external.Jimena.MontalvoSanchez@mx.bosch.com"},
    "DP 35": {"responsable": "Jime", "correo": "external.Jimena.MontalvoSanchez@mx.bosch.com"},
    "KGT 22": {"responsable": "Niko", "correo": "external.Nicolas.BravoVerde@mx.bosch.com"},
    "KGT 23": {"responsable": "Niko", "correo": "external.Nicolas.BravoVerde@mx.bosch.com"},
    "LG 01": {"responsable": "Niko", "correo": "external.Nicolas.BravoVerde@mx.bosch.com"},
    "LG 03": {"responsable": "Niko", "correo": "external.Nicolas.BravoVerde@mx.bosch.com"},
    "SCU 33": {"responsable": "Jarol", "correo": "external.Jarol.DiazCastro@mx.bosch.com"},
    "SCU 34": {"responsable": "Jarol", "correo": "external.Jarol.DiazCastro@mx.bosch.com"},
    "SCU 48": {"responsable": "Jarol", "correo": "external.Jarol.DiazCastro@mx.bosch.com"},
    "SENSOR 28": {"responsable": "Jime", "correo": "external.Jimena.MontalvoSanchez@mx.bosch.com"},
    "SENSOR 5": {"responsable": "Jime", "correo": "external.Jimena.MontalvoSanchez@mx.bosch.com"},
    "SERVO 10": {"responsable": "Lalo", "correo": "external.EduardoAbel.RamirezBecerril@mx.bosch.com"},
    "SERVO 24": {"responsable": "Lalo", "correo": "external.EduardoAbel.RamirezBecerril@mx.bosch.com"},
    "SSL1": {"responsable": "Jarol", "correo": "external.Jarol.DiazCastro@mx.bosch.com"}
}

FILE = "materiales.xlsx"

if not os.path.exists(FILE):
    pd.DataFrame(columns=[
        "Fecha", "Material", "Descripción", "Línea", "Capacidad instalada",
        "No. máquinas", "Piezas por máquina", "Total piezas", "Pieza crítica",
        "Imagen", "Responsable", "Correo", "Estatus"
    ]).to_excel(FILE, index=False)

# ---------------- SIDEBAR ----------------
st.sidebar.title("Menú")
opcion = st.sidebar.radio(
    "Selecciona opción",
    ["➕ Nueva Solicitud", "📋 Seguimiento", "📊 Dashboard"]
)
st.sidebar.markdown(f"👤 Usuario: **{st.session_state.user}**")

# ---------------- NUEVA SOLICITUD ----------------
if opcion == "➕ Nueva Solicitud":
    st.title("➕ Solicitud de Refacciones")

    col1, col2 = st.columns([3,1])

    with col1:
        with st.form("solicitud_form"):
            material = st.text_input("Número de material")
            desc = st.text_area("Descripción")
            linea = st.selectbox("Línea", list(LINEAS.keys()))
            capacidad = st.number_input("Capacidad instalada (piezas)", min_value=0)
            num_maquinas = st.number_input("No. de máquinas", min_value=1)
            piezas_maquina = st.number_input("Piezas por máquina", min_value=1)
            total_piezas = num_maquinas * piezas_maquina
            st.markdown(f"**Total piezas calculadas:** {total_piezas}")
            pieza_critica = st.selectbox("Pieza crítica", ["Sí", "No"])
            imagen = st.file_uploader("Subir imagen del material", type=["png","jpg","jpeg"])
            estatus = st.selectbox(
                "Estatus",
                ["En cotización", "En alta SAP", "Info Record", "Alta confirmada"]
            )
            guardar = st.form_submit_button("Guardar")

        if guardar:
            info = LINEAS[linea]
            df = pd.read_excel(FILE)
            df.loc[len(df)] = [
                datetime.now().strftime("%Y-%m-%d"),
                material,
                desc,
                linea,
                capacidad,
                num_maquinas,
                piezas_maquina,
                total_piezas,
                pieza_critica,
                imagen.name if imagen else "",
                info["responsable"],
                info["correo"],
                estatus
            ]
            df.to_excel(FILE, index=False)
            st.success("Material registrado correctamente")

    with col2:
        st.markdown("### 📌 Solicitudes recientes")
        df = pd.read_excel(FILE)
        for idx, row in df.tail(5).iterrows():
            st.markdown(f"""
            <div class='card'>
            <b>{row['Material']}</b><br>
            Línea: {row['Línea']}<br>
            Total piezas: {row['Total piezas']}<br>
            Estatus: <span class='status-ok'>{row['Estatus']}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 💡 Ayuda rápida")
        st.markdown("- Contacto Responsable por línea\n- Manual de registro\n- Preguntas frecuentes")

# ---------------- SEGUIMIENTO ----------------
elif opcion == "📋 Seguimiento":
    st.title("📋 Seguimiento de materiales")
    df = pd.read_excel(FILE)
    st.dataframe(df, use_container_width=True)
    st.download_button("⬇️ Descargar Excel", df.to_excel(index=False), "materiales.xlsx")

# ---------------- DASHBOARD ----------------
elif opcion == "📊 Dashboard":
    st.title("📊 Dashboard de estatus")
    df = pd.read_excel(FILE)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total materiales", len(df))
    with col2:
        st.metric("Altas confirmadas", len(df[df["Estatus"] == "Alta confirmada"]))
    st.bar_chart(df["Estatus"].value_counts())

