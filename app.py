import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
from io import BytesIO

# ---------------------------------------------------
# CONFIGURACIÓN GENERAL Y ESTILOS (sidebar sin CSS)
# ---------------------------------------------------
st.set_page_config(
    page_title="Alta de Materiales Bosch",
    layout="wide"
)

st.markdown("""
<style>
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
# CONSTANTES Y ARCHIVOS
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
    "admin": {"pwd": "jarol123", "rol": "jefa"},
    "practicante": {"pwd": "alta2026", "rol": "practicante"},
    "inge": {"pwd": "inge2026", "rol": "ingeniero"}
}

# Inicializar archivo si no existe
if not os.path.exists(DB_FILE):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        df_materiales = pd.DataFrame(columns=[
            "ID_Material", "ID_Solicitud", "Fecha_Solicitud", "Ingeniero", "Linea",
            "Prioridad", "Comentario_Solicitud", "Item", "Descripcion", "Estacion",
            "Frecuencia_Cambio", "Cant_Stock_Requerida", "Cant_Equipos",
            "Cant_Partes_Equipo", "RP_Sugerido", "Manufacturer", "Estatus",
            "Practicante_Asignado", "Fecha_Revision", "Fecha_Cotizacion",
            "Fecha_Alta_SAP", "Fecha_InfoRecord", "Fecha_Finalizada",
            "Comentario_Estatus", "Material_SAP", "InfoRecord_SAP"
        ])
        df_materiales.to_excel(writer, sheet_name="materiales", index=False)

        df_historial = pd.DataFrame(columns=[
            "ID_Material", "Fecha_Cambio", "Usuario", "Estatus_Anterior",
            "Estatus_Nuevo", "Comentario"
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
    col1, col2 = st.columns([2, 1])
    with col1:
        user = st.text_input("Usuario")
    with col2:
        pwd = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar sesión", type="primary"):
        if user in USERS and USERS[user]["pwd"] == pwd:
            st.session_state.logged = True
            st.session_state.user = user
            st.session_state.rol = USERS[user]["rol"]
            st.success(f"Bienvenido, {user}")
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ---------------------------------------------------
# MENÚ PRINCIPAL
# ---------------------------------------------------
st.sidebar.title("Navegación")
menu_opciones = ["Nueva solicitud", "Seguimiento", "Dashboard"]
opcion = st.sidebar.radio("Selecciona opción", menu_opciones)
st.sidebar.markdown(f"**Usuario:** {st.session_state.user}  \n**Rol:** {st.session_state.rol}")

df_materiales, df_historial = cargar_datos()

# ---------------------------------------------------
# 1) NUEVA SOLICITUD - MEJORADA CON 2 MODOS
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

        comentario_solicitud = st.text_area("Comentario general de la solicitud", height=80)

        st.markdown("---")
        st.subheader("Captura de materiales")

        # NUEVA LÓGICA: Cantidad de piezas
        cantidad = st.number_input(
            "¿Cuántas piezas quieres registrar?", 
            min_value=1, 
            max_value=50, 
            value=1, 
            step=1,
            help="Para 5 o menos: formulario simple. Para más: plantilla Excel."
        )

        materiales_nuevos = []
        archivo_masivo = None

        if cantidad <= 5:
            st.info(f"**Modo formulario** - Captura fácil para {cantidad} pieza(s)")
            for i in range(cantidad):
                st.markdown(f"---")
                st.subheader(f"Pieza {i+1}")
                
                col1, col2 = st.columns(2)
                with col1:
                    item = st.text_input(f"Item / Número de parte", key=f"item_{i}")
                    descripcion = st.text_input(f"Descripción", key=f"desc_{i}")
                    estacion = st.text_input(f"Estación", key=f"estacion_{i}")
                    frecuencia = st.text_input(f"Frecuencia de cambio / Tiempo de vida", key=f"frec_{i}")
                
                with col2:
                    cant_stock = st.number_input(f"Cantidad en stock requerida", min_value=0.0, value=0.0, step=1.0, key=f"stock_{i}")
                    cant_equipos = st.number_input(f"Número de equipos que usan esta pieza", min_value=0, value=0, step=1, key=f"equipos_{i}")
                    cant_partes = st.number_input(f"Partes por equipo", min_value=0, value=0, step=1, key=f"partes_{i}")
                    rp = st.text_input(f"RP sugerido", key=f"rp_{i}")
                    manufacturer = st.text_input(f"Manufacturer / Proveedor", key=f"mfg_{i}")

                materiales_nuevos.append({
                    "Item": item,
                    "Descripcion": descripcion,
                    "Estacion": estacion,
                    "Frecuencia_Cambio": frecuencia,
                    "Cant_Stock_Requerida": cant_stock,
                    "Cant_Equipos": cant_equipos,
                    "Cant_Partes_Equipo": cant_partes,
                    "RP_Sugerido": rp,
                    "Manufacturer": manufacturer
                })

        else:
            st.info(f"**Modo carga masiva** - {cantidad} piezas se capturan con plantilla Excel")
            st.markdown("Descarga la plantilla, llénala con las piezas y súbela:")
            
            columnas_plantilla = ["Item", "Descripcion", "Estacion", "Frecuencia_Cambio", 
                                "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo", 
                                "RP_Sugerido", "Manufacturer"]
            plantilla_df = pd.DataFrame(columns=columnas_plantilla)
            plantilla_bytes = df_to_excel_bytes(plantilla_df)
            
            col1, col2 = st.columns([1,3])
            with col1:
                st.download_button(
                    label="📥 Plantilla",
                    data=plantilla_bytes,
                    file_name="plantilla_critical_evaluation.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with col2:
                archivo_masivo = st.file_uploader(
                    "Sube la plantilla completada",
                    type=["xlsx"],
                    key="uploader_masivo"
                )

        enviado = st.form_submit_button("Guardar solicitud", type="primary")

    # PROCESAR GUARDADO
    if enviado:
        id_solicitud = generar_id_solicitud()
        fecha_solicitud = datetime.now()
        registros = []

        if cantidad <= 5:
            # Modo formulario
            if not materiales_nuevos:
                st.error("Debes completar al menos una descripción.")
            else:
                for material in materiales_nuevos:
                    if pd.isna(material.get("Descripcion")) or str(material.get("Descripcion", "")).strip() == "":
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
                        "Item": material.get("Item", ""),
                        "Descripcion": material.get("Descripcion", ""),
                        "Estacion": material.get("Estacion", ""),
                        "Frecuencia_Cambio": material.get("Frecuencia_Cambio", ""),
                        "Cant_Stock_Requerida": material.get("Cant_Stock_Requerida", 0),
                        "Cant_Equipos": material.get("Cant_Equipos", 0),
                        "Cant_Partes_Equipo": material.get("Cant_Partes_Equipo", 0),
                        "RP_Sugerido": material.get("RP_Sugerido", ""),
                        "Manufacturer": material.get("Manufacturer", ""),
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

        else:
            # Modo masivo
            if archivo_masivo is None:
                st.error("Debes subir la plantilla Excel completada.")
            else:
                try:
                    df_masivo = pd.read_excel(archivo_masivo)
                    if df_masivo.empty:
                        st.error("La plantilla no contiene datos.")
                    else:
                        for _, row in df_masivo.iterrows():
                            if pd.isna(row.get("Descripcion")) or str(row.get("Descripcion", "")).strip() == "":
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
                except Exception as e:
                    st.error(f"Error al leer la plantilla: {str(e)}")

        if registros:
            df_nuevos = pd.DataFrame(registros)
            df_materiales = pd.concat([df_materiales, df_nuevos], ignore_index=True)
            guardar_datos(df_materiales, df_historial)
            st.success(f"✅ Solicitud **{id_solicitud}** guardada con **{len(registros)}** materiales.")
        else:
            st.error("❌ No se generó ningún material válido. Verifica las descripciones.")

# ---------------------------------------------------
# 2) SEGUIMIENTO
# ---------------------------------------------------
elif opcion == "Seguimiento":
    st.title("Seguimiento de materiales")

    colf1, colf2, colf3, colf4 = st.columns(4)
    with colf1:
        filtro_linea = st.selectbox("Línea", ["Todas"] + list(LINEAS.keys()))
    with colf2:
        filtro_estatus = st.selectbox("Estatus", ["Todos"] + STATUS)
    with colf3:
        filtro_ingeniero = st.text_input("Ingeniero")
    with colf4:
        filtro_practicante = st.text_input("Practicante")

    df_view = df_materiales.copy()
    if filtro_linea != "Todas":
        df_view = df_view[df_view["Linea"] == filtro_linea]
    if filtro_estatus != "Todos":
        df_view = df_view[df_view["Estatus"] == filtro_estatus]
    if filtro_ingeniero:
        df_view = df_view[df_view["Ingeniero"].str.contains(filtro_ingeniero, case=False, na=False)]
    if filtro_practicante:
        df_view = df_view[df_view["Practicante_Asignado"].str.contains(filtro_practicante, case=False, na=False)]

    st.dataframe(df_view[["ID_Material", "ID_Solicitud", "Descripcion", "Linea", "Estatus", "Practicante_Asignado"]], 
                 use_container_width=True)

    st.markdown("---")
    st.subheader("Actualizar estatus")
    
    id_mat_sel = st.text_input("ID del material a actualizar")
    if id_mat_sel:
        df_sel = df_materiales[df_materiales["ID_Material"] == id_mat_sel]
        if not df_sel.empty:
            registro = df_sel.iloc[0]
            st.markdown(f"**{registro['Descripcion']}**")
            st.markdown(f"**ID Solicitud:** {registro['ID_Solicitud']} | **Línea:** {registro['Linea']}")
            st.markdown("**Estatus actual:** " + estatus_coloreado(registro["Estatus"]), unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                nuevo_estatus = st.selectbox("Nuevo estatus", STATUS, 
                                           index=STATUS.index(registro["Estatus"]) if registro["Estatus"] in STATUS else 0)
                practicante = st.text_input("Practicante", value=registro.get("Practicante_Asignado", ""))
            with col2:
                material_sap = st.text_input("Material SAP", value=registro.get("Material_SAP", ""))
                inforecord_sap = st.text_input("InfoRecord SAP", value=registro.get("InfoRecord_SAP", ""))
            
            comentario = st.text_area("Comentario del cambio", height=60)

            if st.button("Guardar cambio", type="primary"):
                idx = df_materiales.index[df_materiales["ID_Material"] == id_mat_sel][0]
                estatus_anterior = df_materiales.at[idx, "Estatus"]
                
                df_materiales.at[idx, "Estatus"] = nuevo_estatus
                df_materiales.at[idx, "Practicante_Asignado"] = practicante
                df_materiales.at[idx, "Comentario_Estatus"] = comentario
                df_materiales.at[idx, "Material_SAP"] = material_sap
                df_materiales.at[idx, "InfoRecord_SAP"] = inforecord_sap

                fecha_hoy = datetime.now()
                if nuevo_estatus == "En cotización":
                    df_materiales.at[idx, "Fecha_Cotizacion"] = fecha_hoy
                elif nuevo_estatus == "En alta SAP":
                    df_materiales.at[idx, "Fecha_Alta_SAP"] = fecha_hoy
                elif nuevo_estatus == "Info record creado":
                    df_materiales.at[idx, "Fecha_InfoRecord"] = fecha_hoy
                elif nuevo_estatus == "Alta finalizada":
                    df_materiales.at[idx, "Fecha_Finalizada"] = fecha_hoy

                # Guardar historial
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
                st.success("✅ Estatus actualizado correctamente.")

# ---------------------------------------------------
# 3) DASHBOARD
# ---------------------------------------------------
elif opcion == "Dashboard":
    st.title("Dashboard de altas de materiales")

    if df_materiales.empty:
        st.info("No hay datos para mostrar.")
    else:
        df_dash = df_materiales.copy()
        df_dash["Fecha_Solicitud"] = pd.to_datetime(df_dash["Fecha_Solicitud"])
        df_dash["Semana"] = df_dash["Fecha_Solicitud"].dt.isocalendar().week
        df_dash["Anio"] = df_dash["Fecha_Solicitud"].dt.year

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total materiales", len(df_materiales))
        with col2:
            st.metric("En proceso", len(df_materiales[df_materiales["Estatus"] != "Alta finalizada"]))
        with col3:
            st.metric("Finalizados", len(df_materiales[df_materiales["Estatus"] == "Alta finalizada"]))

        st.subheader("Materiales por estatus")
        estatus_count = df_dash["Estatus"].value_counts()
        st.bar_chart(estatus_count)

        st.subheader("Materiales por línea")
        linea_count = df_dash["Linea"].value_counts()
        st.bar_chart(linea_count)

        st.subheader("Materiales creados por semana")
        sem_count = df_dash.groupby(["Anio", "Semana"]).size().reset_index(name="Cantidad")
        if not sem_count.empty:
            st.line_chart(sem_count.set_index("Semana")["Cantidad"])


