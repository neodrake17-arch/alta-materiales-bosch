import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
from io import BytesIO

# ---------------------------------------------------
# CONFIGURACIÓN GENERAL Y ESTILOS
# ---------------------------------------------------
st.set_page_config(
    page_title="Alta de Materiales Bosch",
    layout="wide"
)

st.markdown("""
<style>
/* Fondo general y tipografía */
body {
    background-color: #ffffff;
    font-family: "Arial", sans-serif;
}

/* Títulos con azul Bosch */
h1, h2, h3 {
    color: #005691;
}

/* Botones principales */
.stButton>button {
    background-color: #005691 !important;
    color: white !important;
    border-radius: 8px !important;
    height: 40px;
    border: none;
    font-weight: 600;
}

/* Inputs y selects */
.stTextInput>div>input,
.stTextArea>div>textarea,
.stSelectbox>div>div,
.stDataEditor {
    border-radius: 8px;
    border: 1px solid #cccccc;
    padding: 5px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #f5f5f5;
}

/* Tarjetas */
.card {
    padding: 15px;
    border-radius: 10px;
    background-color: #f7f7f7;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    margin-bottom: 10px;
}

/* Colores de estatus */
.status-revision {
    color: #666666;
    font-weight: bold;
}
.status-cotizacion {
    color: #ff9800;
    font-weight: bold;
}
.status-alta {
    color: #1976d2;
    font-weight: bold;
}
.status-info {
    color: #8e24aa;
    font-weight: bold;
}
.status-final {
    color: #388e3c;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CONSTANTES, ARCHIVOS Y ESTRUCTURA
# ---------------------------------------------------
DB_FILE = "bd_materiales.xlsx"
os.makedirs("imagenes", exist_ok=True)

STATUS = [
    "En revisión de ingeniería",
    "En cotización",
    "En alta SAP",
    "Info record creado",
    "Alta finalizada"
]

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

USERS = {
    "admin": {"pwd": "bosch123", "rol": "jefa"},
    "practicante": {"pwd": "alta2026", "rol": "practicante"},
    "inge": {"pwd": "inge2026", "rol": "ingeniero"}
}

# Inicializar archivo si no existe
if not os.path.exists(DB_FILE):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        df_materiales = pd.DataFrame(columns=[
            "ID_Material",
            "ID_Solicitud",
            "Fecha_Solicitud",
            "Ingeniero",
            "Linea",
            "Prioridad",
            "Comentario_Solicitud",

            "Item",
            "Descripcion",
            "Estacion",
            "Frecuencia_Cambio",
            "Cant_Stock_Requerida",
            "Cant_Equipos",
            "Cant_Partes_Equipo",
            "RP_Sugerido",
            "Manufacturer",

            "Estatus",
            "Practicante_Asignado",

            "Fecha_Revision",
            "Fecha_Cotizacion",
            "Fecha_Alta_SAP",
            "Fecha_InfoRecord",
            "Fecha_Finalizada",

            "Comentario_Estatus",
            "Material_SAP",
            "InfoRecord_SAP"
        ])
        df_materiales.to_excel(writer, sheet_name="materiales", index=False)

        df_historial = pd.DataFrame(columns=[
            "ID_Material",
            "Fecha_Cambio",
            "Usuario",
            "Estatus_Anterior",
            "Estatus_Nuevo",
            "Comentario"
        ])
        df_historial.to_excel(writer, sheet_name="historial", index=False)

# ---------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------
def cargar_datos():
    xls = pd.ExcelFile(DB_FILE)
    materiales = pd.read_excel(xls, "materiales")
    historial = pd.read_excel(xls, "historial")
    return materiales, historial

def guardar_datos(df_materiales, df_historial):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        df_materiales.to_excel(writer, sheet_name="materiales", index=False)
        df_historial.to_excel(writer, sheet_name="historial", index=False)

def generar_id_solicitud():
    return "SOL-" + datetime.now().strftime("%Y%m%d-%H%M%S")

def generar_id_material():
    return "MAT-" + uuid.uuid4().hex[:8].upper()

def estatus_coloreado(estatus: str) -> str:
    clases = {
        "En revisión de ingeniería": "status-revision",
        "En cotización": "status-cotizacion",
        "En alta SAP": "status-alta",
        "Info record creado": "status-info",
        "Alta finalizada": "status-final"
    }
    clase = clases.get(estatus, "status-revision")
    return f'<span class="{clase}">{estatus}</span>'

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ---------------------------------------------------
# LOGIN
# ---------------------------------------------------
if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    st.title("Acceso – Alta de Materiales Bosch")
    user = st.text_input("Usuario")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user in USERS and USERS[user]["pwd"] == pwd:
            st.session_state.logged = True
            st.session_state.user = user
            st.session_state.rol = USERS[user]["rol"]
            st.success(f"Bienvenido, {user}")
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ---------------------------------------------------
# MENÚ PRINCIPAL (sin emojis, estilo profesional)
# ---------------------------------------------------
st.sidebar.title("Navegación")
menu_opciones = ["Nueva solicitud", "Seguimiento", "Dashboard"]
opcion = st.sidebar.radio("Selecciona opción", menu_opciones)
st.sidebar.markdown(f"Usuario: **{st.session_state.user}**  \nRol: **{st.session_state.rol}**")

df_materiales, df_historial = cargar_datos()

# ---------------------------------------------------
# 1) NUEVA SOLICITUD
# ---------------------------------------------------
if opcion == "Nueva solicitud":
    st.title("Nueva solicitud de refacciones")

    with st.form("form_solicitud"):
        st.subheader("Datos de la solicitud")
        col1, col2, col3 = st.columns(3)
        with col1:
            ingeniero = st.text_input("Ingeniero solicitante", value=st.session_state.user)
        with col2:
            linea = st.selectbox("Línea", list(LINEAS.keys()))
        with col3:
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])

        comentario_solicitud = st.text_area("Comentario general de la solicitud")

        st.markdown("---")
        st.subheader("Captura de materiales (Critical Evaluation)")

        st.info("Elige la forma de captura de materiales: manual o carga masiva desde plantilla Excel.")

        opcion_captura = st.radio(
            "Modo de captura",
            ["Captura manual", "Carga masiva (Excel plantilla)"],
            horizontal=True
        )

        materiales_nuevos = None
        archivo_masivo = None

        columnas_material = [
            "Item", "Descripcion", "Estacion", "Frecuencia_Cambio",
            "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo",
            "RP_Sugerido", "Manufacturer"
        ]

        if opcion_captura == "Captura manual":
            df_tmp = pd.DataFrame(columns=columnas_material)
            df_edit = st.data_editor(
                df_tmp,
                num_rows="dynamic",
                use_container_width=True,
                key="editor_materiales"
            )
            materiales_nuevos = df_edit

        else:
            st.markdown("Descarga la plantilla, llénala con los materiales y súbela nuevamente.")
            plantilla_df = pd.DataFrame(columns=columnas_material)
            plantilla_bytes = df_to_excel_bytes(plantilla_df)
            st.download_button(
                label="Descargar plantilla Excel",
                data=plantilla_bytes,
                file_name="plantilla_critical_evaluation.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            archivo_masivo = st.file_uploader(
                "Subir plantilla llenada",
                type=["xlsx"],
                key="uploader_masivo"
            )

        enviado = st.form_submit_button("Guardar solicitud")

    if enviado:
        id_solicitud = generar_id_solicitud()
        fecha_solicitud = datetime.now()

        if opcion_captura == "Captura manual":
            if materiales_nuevos is None or materiales_nuevos.empty:
                st.error("Debes capturar al menos un material.")
            else:
                registros = []
                for _, row in materiales_nuevos.iterrows():
                    if pd.isna(row.get("Descripcion")) or str(row.get("Descripcion")).strip() == "":
                        continue
                    id_material = generar_id_material()
                    registros.append({
                        "ID_Material": id_material,
                        "ID_Solicitud": id_solicitud,
                        "Fecha_Solicitud": fecha_solicitud,
                        "Ingeniero": ingeniero,
                        "Linea": linea,
                        "Prioridad": prioridad,
                        "Comentario_Solicitud": comentario_solicitud,

                        "Item": row.get("Item", ""),
                        "Descripcion": row.get("Descripcion", ""),
                        "Estacion": row.get("Estacion", ""),
                        "Frecuencia_Cambio": row.get("Frecuencia_Cambio", ""),
                        "Cant_Stock_Requerida": row.get("Cant_Stock_Requerida", 0),
                        "Cant_Equipos": row.get("Cant_Equipos", 0),
                        "Cant_Partes_Equipo": row.get("Cant_Partes_Equipo", 0),
                        "RP_Sugerido": row.get("RP_Sugerido", ""),
                        "Manufacturer": row.get("Manufacturer", ""),

                        "Estatus": "En revisión de ingeniería",
                        "Practicante_Asignado": "",
                        "Fecha_Revision": fecha_solicitud,
                        "Fecha_Cotizacion": pd.NaT,
                        "Fecha_Alta_SAP": pd.NaT,
                        "Fecha_InfoRecord": pd.NaT,
                        "Fecha_Finalizada": pd.NaT,
                        "Comentario_Estatus": "",
                        "Material_SAP": "",
                        "InfoRecord_SAP": ""
                    })

                if not registros:
                    st.error("No se generó ningún material válido (revisa que las descripciones no estén vacías).")
                else:
                    df_nuevos = pd.DataFrame(registros)
                    df_materiales = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                    guardar_datos(df_materiales, df_historial)
                    st.success(f"Solicitud {id_solicitud} guardada con {len(df_nuevos)} materiales.")

        else:
            if archivo_masivo is None:
                st.error("Debes subir la plantilla llena con los materiales.")
            else:
                df_masivo = pd.read_excel(archivo_masivo)
                if df_masivo.empty:
                    st.error("La plantilla no tiene materiales.")
                else:
                    registros = []
                    for _, row in df_masivo.iterrows():
                        if pd.isna(row.get("Descripcion")) or str(row.get("Descripcion")).strip() == "":
                            continue
                        id_material = generar_id_material()
                        registros.append({
                            "ID_Material": id_material,
                            "ID_Solicitud": id_solicitud,
                            "Fecha_Solicitud": fecha_solicitud,
                            "Ingeniero": ingeniero,
                            "Linea": linea,
                            "Prioridad": prioridad,
                            "Comentario_Solicitud": comentario_solicitud,

                            "Item": row.get("Item", ""),
                            "Descripcion": row.get("Descripcion", ""),
                            "Estacion": row.get("Estacion", ""),
                            "Frecuencia_Cambio": row.get("Frecuencia_Cambio", ""),
                            "Cant_Stock_Requerida": row.get("Cant_Stock_Requerida", 0),
                            "Cant_Equipos": row.get("Cant_Equipos", 0),
                            "Cant_Partes_Equipo": row.get("Cant_Partes_Equipo", 0),
                            "RP_Sugerido": row.get("RP_Sugerido", ""),
                            "Manufacturer": row.get("Manufacturer", ""),

                            "Estatus": "En revisión de ingeniería",
                            "Practicante_Asignado": "",
                            "Fecha_Revision": fecha_solicitud,
                            "Fecha_Cotizacion": pd.NaT,
                            "Fecha_Alta_SAP": pd.NaT,
                            "Fecha_InfoRecord": pd.NaT,
                            "Fecha_Finalizada": pd.NaT,
                            "Comentario_Estatus": "",
                            "Material_SAP": "",
                            "InfoRecord_SAP": ""
                        })
                    if not registros:
                        st.error("No se generó ningún material válido (revisa que las descripciones no estén vacías).")
                    else:
                        df_nuevos = pd.DataFrame(registros)
                        df_materiales = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                        guardar_datos(df_materiales, df_historial)
                        st.success(f"Solicitud {id_solicitud} guardada con {len(df_nuevos)} materiales.")

# ---------------------------------------------------
# 2) SEGUIMIENTO
# ---------------------------------------------------
elif opcion == "Seguimiento":
    st.title("Seguimiento de materiales")

    # Filtros
    colf1, colf2, colf3, colf4 = st.columns(4)
    with colf1:
        filtro_linea = st.selectbox("Filtrar por línea", ["Todas"] + list(LINEAS.keys()))
    with colf2:
        filtro_estatus = st.selectbox("Filtrar por estatus", ["Todos"] + STATUS)
    with colf3:
        filtro_ingeniero = st.text_input("Filtrar por ingeniero (texto)")
    with colf4:
        filtro_practicante = st.text_input("Filtrar por practicante (texto)")

    df_view = df_materiales.copy()

    if filtro_linea != "Todas":
        df_view = df_view[df_view["Linea"] == filtro_linea]
    if filtro_estatus != "Todos":
        df_view = df_view[df_view["Estatus"] == filtro_estatus]
    if filtro_ingeniero:
        df_view = df_view[df_view["Ingeniero"].str.contains(filtro_ingeniero, case=False, na=False)]
    if filtro_practicante:
        df_view = df_view[df_view["Practicante_Asignado"].str.contains(filtro_practicante, case=False, na=False)]

    st.dataframe(df_view, use_container_width=True)

    st.markdown("---")
    st.subheader("Actualizar estatus de un material")

    id_mat_sel = st.text_input("ID del material (ID_Material) a actualizar")
    if id_mat_sel:
        df_sel = df_materiales[df_materiales["ID_Material"] == id_mat_sel]
        if df_sel.empty:
            st.warning("No se encontró ese ID_Material.")
        else:
            registro = df_sel.iloc[0]
            st.write(f"ID de solicitud: {registro['ID_Solicitud']}")
            st.write(f"Descripción: {registro['Descripcion']}")

            st.markdown(
                "Estatus actual: " +
                estatus_coloreado(registro["Estatus"]),
                unsafe_allow_html=True
            )

            nuevo_estatus = st.selectbox(
                "Nuevo estatus",
                STATUS,
                index=STATUS.index(registro["Estatus"]) if registro["Estatus"] in STATUS else 0
            )
            practicante = st.text_input("Practicante asignado", value=registro.get("Practicante_Asignado", ""))
            comentario = st.text_area("Comentario del cambio")
            material_sap = st.text_input("Material SAP (opcional)", value=registro.get("Material_SAP", ""))
            inforecord_sap = st.text_input("InfoRecord SAP (opcional)", value=registro.get("InfoRecord_SAP", ""))

            if st.button("Guardar cambio de estatus"):
                idx = df_materiales.index[df_materiales["ID_Material"] == id_mat_sel][0]
                estatus_anterior = df_materiales.at[idx, "Estatus"]
                df_materiales.at[idx, "Estatus"] = nuevo_estatus
                df_materiales.at[idx, "Practicante_Asignado"] = practicante
                df_materiales.at[idx, "Comentario_Estatus"] = comentario
                df_materiales.at[idx, "Material_SAP"] = material_sap
                df_materiales.at[idx, "InfoRecord_SAP"] = inforecord_sap

                fecha_hoy = datetime.now()
                if nuevo_estatus == "En revisión de ingeniería":
                    df_materiales.at[idx, "Fecha_Revision"] = fecha_hoy
                elif nuevo_estatus == "En cotización":
                    df_materiales.at[idx, "Fecha_Cotizacion"] = fecha_hoy
                elif nuevo_estatus == "En alta SAP":
                    df_materiales.at[idx, "Fecha_Alta_SAP"] = fecha_hoy
                elif nuevo_estatus == "Info record creado":
                    df_materiales.at[idx, "Fecha_InfoRecord"] = fecha_hoy
                elif nuevo_estatus == "Alta finalizada":
                    df_materiales.at[idx, "Fecha_Finalizada"] = fecha_hoy

                nuevo_hist = {
                    "ID_Material": id_mat_sel,
                    "Fecha_Cambio": fecha_hoy,
                    "Usuario": st.session_state.user,
                    "Estatus_Anterior": estatus_anterior,
                    "Estatus_Nuevo": nuevo_estatus,
                    "Comentario": comentario
                }
                df_historial = pd.concat([df_historial, pd.DataFrame([nuevo_hist])], ignore_index=True)

                guardar_datos(df_materiales, df_historial)
                st.success("Estatus actualizado y cambio registrado en historial.")

# ---------------------------------------------------
# 3) DASHBOARD
# ---------------------------------------------------
elif opcion == "Dashboard":
    st.title("Dashboard de altas de materiales")

    if df_materiales.empty:
        st.info("No hay datos todavía.")
    else:
        df_dash = df_materiales.copy()
        df_dash["Fecha_Solicitud"] = pd.to_datetime(df_dash["Fecha_Solicitud"])
        df_dash["Semana"] = df_dash["Fecha_Solicitud"].dt.isocalendar().week
        df_dash["Anio"] = df_dash["Fecha_Solicitud"].dt.year

        st.subheader("Materiales por estatus")
        estatus_count = df_dash["Estatus"].value_counts()
        st.bar_chart(estatus_count)

        st.subheader("Materiales creados por semana")
        sem_count = df_dash.groupby(["Anio", "Semana"]).size().reset_index(name="Cantidad")
        if not sem_count.empty:
            st.line_chart(data=sem_count, x="Semana", y="Cantidad")
        else:
            st.write("No hay datos suficientes para la gráfica semanal.")

        st.subheader("Materiales finalizados por practicante")
        df_finalizados = df_dash[df_dash["Estatus"] == "Alta finalizada"]
        if not df_finalizados.empty:
            prac_count = df_finalizados["Practicante_Asignado"].value_counts()
            st.bar_chart(prac_count)
        else:
            st.write("Aún no hay materiales con 'Alta finalizada'.")

