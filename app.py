import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
from io import BytesIO

# Configuración
st.set_page_config(page_title="Alta de Materiales Bosch", layout="wide")

st.markdown("""
<style>
h1, h2, h3 { color: #005691; font-weight: bold; }
h1 { font-size: 2.5em; }
.stButton>button { 
    background-color: #005691 !important; 
    color: white !important; 
    border-radius: 8px !important; 
    height: 42px; 
    font-weight: 600; 
    border: none !important;
}
.stButton>button:hover { background-color: #003d6b !important; }
.alert-pendiente { color: #d32f2f !important; font-weight: bold; font-size: 1.3em; }
.alert-proceso { color: #ff9800 !important; font-weight: bold; }
.status-revision { color: #666666; font-weight: bold; }
.status-cotizacion { color: #ff9800; font-weight: bold; }
.status-alta { color: #1976d2; font-weight: bold; }
.status-info { color: #8e24aa; font-weight: bold; }
.status-final { color: #388e3c; font-weight: bold; }
.sidebar .sidebar-content { background-color: #f8f9fa !important; }
</style>
""", unsafe_allow_html=True)

# ========================================
# CONSTANTES Y CONFIGURACIÓN
# ========================================
DB_FILE = "bd_materiales.xlsx"
os.makedirs("imagenes", exist_ok=True)

# USUARIOS INDIVIDUALES - CAMBIA LAS CONTRASEÑAS AQUÍ
USERS = {
    "jarol": {"pwd": "jarol123", "rol": "practicante", "responsable": "Jarol"},
    "lalo": {"pwd": "lalo123", "rol": "practicante", "responsable": "Lalo"},
    "jime": {"pwd": "jime123", "rol": "practicante", "responsable": "Jime"},
    "niko": {"pwd": "niko123", "rol": "practicante", "responsable": "Niko"},
    "admin": {"pwd": "admin123", "rol": "jefa", "responsable": "Admin"}
}

# LÍNEAS POR PRACTICANTE
LINEAS_POR_PRACTICANTE = {
    "Jarol": ["DP 02", "SCU 33", "SCU 34", "SCU 48", "SSL1"],
    "Lalo": ["APA 36", "APA 38", "SERVO 10", "SERVO 24"],
    "Jime": ["DP 32", "DP 35", "SENSOR 28", "SENSOR 5"],
    "Niko": ["KGT 22", "KGT 23", "LG 01", "LG 03"]
}

LINEAS = list(set(sum(LINEAS_POR_PRACTICANTE.values(), [])))
STATUS = ["En revisión de ingeniería", "En cotización", "En alta SAP", "Info record creado", "Alta finalizada"]

# ========================================
# BASE DE DATOS
# ========================================
if not os.path.exists(DB_FILE):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        pd.DataFrame(columns=[
            "ID_Material", "ID_Solicitud", "Fecha_Solicitud", "Ingeniero", "Linea",
            "Prioridad", "Comentario_Solicitud", "Item", "Descripcion", "Estacion",
            "Frecuencia_Cambio", "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo",
            "RP_Sugerido", "Manufacturer", "Estatus", "Practicante_Asignado",
            "Fecha_Revision", "Fecha_Cotizacion", "Fecha_Alta_SAP", "Fecha_InfoRecord",
            "Fecha_Finalizada", "Comentario_Estatus", "Material_SAP", "InfoRecord_SAP"
        ]).to_excel(writer, sheet_name="materiales", index=False)

def cargar_datos():
    try:
        xls = pd.ExcelFile(DB_FILE)
        df_materiales = pd.read_excel(xls, "materiales")
        df_historial = pd.read_excel(xls, "historial") if "historial" in xls.sheet_names else pd.DataFrame()
        return df_materiales, df_historial
    except:
        return pd.DataFrame(), pd.DataFrame()

def guardar_datos(df_materiales, df_historial):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        df_materiales.to_excel(writer, sheet_name="materiales", index=False)
        df_historial.to_excel(writer, sheet_name="historial", index=False)

def generar_id_solicitud():
    return f"SOL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def generar_id_material():
    return f"MAT-{uuid.uuid4().hex[:8].upper()}"

def estatus_coloreado(estatus):
    clases = {
        "En revisión de ingeniería": "status-revision",
        "En cotización": "status-cotizacion",
        "En alta SAP": "status-alta",
        "Info record creado": "status-info",
        "Alta finalizada": "status-final"
    }
    return f'<span class="{clases.get(estatus, "status-revision")}">{estatus}</span>'

def df_to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def contar_pendientes(usuario, df_materiales):
    if usuario in LINEAS_POR_PRACTICANTE:
        lineas = LINEAS_POR_PRACTICANTE[usuario]
        return len(df_materiales[(df_materiales["Linea"].isin(lineas)) & 
                                (df_materiales["Estatus"] != "Alta finalizada")])
    return 0

# ========================================
# LOGIN
# ========================================
if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <h1 style='color: #005691; margin-bottom: 1rem;'>🔧 Bosch Material Management</h1>
        <div style='background: #f8f9fa; padding: 2rem; border-radius: 12px; max-width: 500px; margin: auto;'>
            <h3 style='color: #333;'>Iniciar Sesión</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        user = st.text_input("👤 Usuario", placeholder="jarol, lalo, jime, niko, admin")
    with col2:
        pwd = st.text_input("🔒 Contraseña", type="password", placeholder="Escribe tu contraseña")
    
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("🚀 ENTRAR", type="primary", use_container_width=True):
            if user in USERS and USERS[user]["pwd"] == pwd:
                st.session_state.logged = True
                st.session_state.user = user
                st.session_state.rol = USERS[user]["rol"]
                st.session_state.responsable = USERS[user]["responsable"]
                st.success("✅ ¡Bienvenido!")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
    
    with col_info:
        st.markdown("""
        **Usuarios disponibles:**
        - `jarol` / `jarol123`
        - `lalo` / `lalo123`  
        - `jime` / `jime123`
        - `niko` / `niko123`
        - `admin` / `admin123`
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ========================================
# CARGAR DATOS
# ========================================
df_materiales, df_historial = cargar_datos()
pendientes_usuario = contar_pendientes(st.session_state.responsable, df_materiales)

# ========================================
# SIDEBAR DINÁMICO POR ROL
# ========================================
with st.sidebar:
    st.markdown("<h3 style='color: #005691; margin-bottom: 1rem;'>Bosch Materiales</h3>", unsafe_allow_html=True)
    
    # ALERTA PERSONALIZADA POR ROL
    if st.session_state.rol == "practicante":
        st.markdown(f"""
        <div style='background: #ffebee; padding: 1rem; border-radius: 8px; border-left: 5px solid #d32f2f; margin-bottom: 1rem;'>
            <div class='alert-pendiente'>🔔 **{pendientes_usuario} PENDIENTES**</div>
            <small style='color: #666;'>Solo tus líneas: {', '.join(LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, []))}</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"👤 **{st.session_state.user}**")
    st.markdown(f"🎭 **{st.session_state.rol}**")
    st.markdown(f"🏢 **{st.session_state.responsable}**")
    st.markdown("---")
    
    # MENÚ POR ROL
    if st.session_state.rol == "practicante":
        opcion = st.radio("Navegar:", ["Mis pendientes", "Seguimiento completo", "Nueva solicitud"])
    elif st.session_state.rol == "jefa":
        st.metric("Total pendientes", pendientes_usuario)
        opcion = st.radio("Navegar:", ["Dashboard", "Seguimiento", "Nueva solicitud"])
    else:  # ingeniero
        opcion = st.radio("Navegar:", ["Nueva solicitud", "Mis solicitudes"])

# ========================================
# CONTENIDO PRINCIPAL
# ========================================
if opcion == "Nueva solicitud":
    st.markdown("<h1 style='color: #005691;'>📋 Nueva Solicitud de Materiales</h1>", unsafe_allow_html=True)
    
    # DATOS GENERALES
    col1, col2, col3 = st.columns(3)
    ingeniero = col1.text_input("👨‍🔧 Ingeniero", value=st.session_state.user)
    linea = col2.selectbox("🏭 Línea", LINEAS)
    prioridad = col3.selectbox("🔥 Prioridad", ["Alta", "Media", "Baja"])
    
    st.markdown("---")
    
    # 2 TABS CLAROS
    tab1, tab2 = st.tabs(["📝 Formulario (1-5 materiales)", "📊 Excel masivo (>5)"])
    
    with tab1:
        st.info("**Formulario simple - máximo 5 materiales**")
        with st.form("formulario_simple"):
            materiales = []
            
            for i in range(5):
                with st.container():
                    st.markdown(f"### **Material {i+1}**")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        item = st.text_input("Item/Nº parte", key=f"item_{i}")
                        descripcion = st.text_input("**Descripción** *", key=f"desc_{i}")
                        estacion = st.text_input("Estación", key=f"est_{i}")
                    
                    with col_b:
                        stock = st.number_input("Stock mínimo", min_value=0.0, format="%.1f", key=f"stock_{i}")
                        equipos = st.number_input("Equipos que usan", min_value=0, key=f"eq_{i}")
                        partes_eq = st.number_input("Partes por equipo", min_value=0, key=f"partes_{i}")
                        rp = st.text_input("RP sugerido", key=f"rp_{i}")
                        fabricante = st.text_input("Fabricante", key=f"fab_{i}")
                    
                    materiales.append({
                        "Item": item, "Descripcion": descripcion, "Estacion": estacion,
                        "Cant_Stock_Requerida": stock, "Cant_Equipos": equipos,
                        "Cant_Partes_Equipo": partes_eq, "RP_Sugerido": rp, "Manufacturer": fabricante
                    })
            
            comentario_general = st.text_area("Comentario general de la solicitud")
            if st.form_submit_button("💾 Guardar Solicitud", use_container_width=True):
                registros = []
                id_solicitud = generar_id_solicitud()
                
                for mat in materiales:
                    if mat["Descripcion"].strip():
                        registros.append({
                            "ID_Material": generar_id_material(),
                            "ID_Solicitud": id_solicitud,
                            "Fecha_Solicitud": datetime.now(),
                            "Ingeniero": ingeniero,
                            "Linea": linea,
                            "Prioridad": prioridad,
                            "Comentario_Solicitud": comentario_general,
                            **mat,
                            "Estatus": "En revisión de ingeniería",
                            "Practicante_Asignado": "",
                            "Fecha_Revision": datetime.now(),
                            "Fecha_Cotizacion": pd.NaT,
                            "Fecha_Alta_SAP": pd.NaT,
                            "Fecha_InfoRecord": pd.NaT,
                            "Fecha_Finalizada": pd.NaT,
                            "Comentario_Estatus": "",
                            "Material_SAP": "",
                            "InfoRecord_SAP": ""
                        })
                
                if registros:
                    df_nuevos = pd.DataFrame(registros)
                    df_materiales = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                    guardar_datos(df_materiales, df_historial)
                    st.success(f"✅ **Solicitud {id_solicitud}** creada con {len(registros)} materiales")
                    st.balloons()
                else:
                    st.error("❌ Completa al menos una descripción")
    
    with tab2:
        st.info("**Para más de 5 materiales, descarga la plantilla y súbela**")
        
        columnas = ["Item", "Descripcion", "Estacion", "Frecuencia_Cambio", 
                   "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo", 
                   "RP_Sugerido", "Manufacturer"]
        
        plantilla_df = pd.DataFrame(columns=columnas)
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Descargar Plantilla",
                data=df_to_excel_bytes(plantilla_df),
                file_name="plantilla_critical_evaluation.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        archivo = st.file_uploader("📤 Subir plantilla completada", type=["xlsx"])
        
        with st.form("form_masivo"):
            comentario_general = st.text_area("Comentario general")
            if st.form_submit_button("💾 Guardar Masivo", use_container_width=True) and archivo is not None:
                try:
                    df_archivo = pd.read_excel(archivo)
                    registros = []
                    id_solicitud = generar_id_solicitud()
                    
                    for _, row in df_archivo.iterrows():
                        if str(row.get("Descripcion", "")).strip():
                            registros.append({
                                "ID_Material": generar_id_material(),
                                "ID_Solicitud": id_solicitud,
                                "Fecha_Solicitud": datetime.now(),
                                "Ingeniero": ingeniero,
                                "Linea": linea,
                                "Prioridad": prioridad,
                                "Comentario_Solicitud": comentario_general,
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
                                "Fecha_Revision": datetime.now(),
                                "Fecha_Cotizacion": pd.NaT,
                                "Fecha_Alta_SAP": pd.NaT,
                                "Fecha_InfoRecord": pd.NaT,
                                "Fecha_Finalizada": pd.NaT,
                                "Comentario_Estatus": "",
                                "Material_SAP": "",
                                "InfoRecord_SAP": ""
                            })
                    
                    if registros:
                        df_nuevos = pd.DataFrame(registros)
                        df_materiales = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                        guardar_datos(df_materiales, df_historial)
                        st.success(f"✅ **{id_solicitud}** - {len(registros)} materiales masivos guardados")
                        st.balloons()
                    else:
                        st.error("❌ La plantilla no tiene descripciones válidas")
                except Exception as e:
                    st.error(f"❌ Error procesando Excel: {str(e)}")

elif opcion == "Mis pendientes" and st.session_state.rol == "practicante":
    st.markdown(f"<h1 style='color: #005691;'>📋 Mis Pendientes - {st.session_state.responsable}</h1>", unsafe_allow_html=True)
    
    # FILTRAR SOLO SUS LÍNEAS
    mis_lineas = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_mis = df_materiales[
        (df_materiales["Linea"].isin(mis_lineas)) & 
        (df_materiales["Estatus"] != "Alta finalizada")
    ].copy()
    
    if df_mis.empty:
        st.info("✅ ¡No tienes pendientes! 🎉")
    else:
        # MÉTRICAS PERSONALES
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total pendientes", len(df_mis))
        col2.metric("En revisión", len(df_mis[df_mis["Estatus"] == "En revisión de ingeniería"]))
        col3.metric("Cotización", len(df_mis[df_mis["Estatus"] == "En cotización"]))
        col4.metric("Alta SAP", len(df_mis[df_mis["Estatus"] == "En alta SAP"]))
        
        st.markdown("---")
        
        # TABLA DE TRABAJO
        st.markdown("<h3 style='color: #1976d2;'>📋 Lista de Trabajo</h3>", unsafe_allow_html=True)
        df_mostrar = df_mis[["ID_Material", "ID_Solicitud", "Descripcion", "Linea", "Estatus", "Practicante_Asignado"]].copy()
        df_mostrar["Estatus"] = df_mostrar["Estatus"].apply(estatus_coloreado)
        st.markdown(df_mostrar.to_html(escape=False), unsafe_allow_html=True)
        
        # ACTUALIZAR MATERIAL
        st.markdown("---")
        st.markdown("<h4 style='color: #666;'>🔄 Actualizar Material</h4>", unsafe_allow_html=True)
        id_material = st.text_input("ID_Material a actualizar")
        
        if id_material in df_mis["ID_Material"].values:
            idx = df_materiales[df_materiales["ID_Material"] == id_material].index[0]
            reg = df_materiales.loc[idx]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{reg['Descripcion']}**")
                st.markdown(f"**{reg['Linea']}**")
                nuevo_estatus = st.selectbox("Nuevo estatus", STATUS, 
                                           index=STATUS.index(reg["Estatus"]))
            with col2:
                practicante = st.text_input("Asignado a", value=reg.get("Practicante_Asignado", st.session_state.responsable))
                material_sap = st.text_input("Material SAP", value=reg.get("Material_SAP", ""))
                info_sap = st.text_input("InfoRecord SAP", value=reg.get("InfoRecord_SAP", ""))
            
            comentario = st.text_area("Comentario del avance")
            
            if st.button("✅ Actualizar Estatus", type="primary"):
                df_materiales.loc[idx, "Estatus"] = nuevo_estatus
                df_materiales.loc[idx, "Practicante_Asignado"] = practicante
                df_materiales.loc[idx, "Comentario_Estatus"] = comentario
                df_materiales.loc[idx, "Material_SAP"] = material_sap
                df_materiales.loc[idx, "InfoRecord_SAP"] = info_sap
                
                # FECHAS AUTOMÁTICAS
                fecha = datetime.now()
                if nuevo_estatus == "En cotización": df_materiales.loc[idx, "Fecha_Cotizacion"] = fecha
                elif nuevo_estatus == "En alta SAP": df_materiales.loc[idx, "Fecha_Alta_SAP"] = fecha
                elif nuevo_estatus == "Info record creado": df_materiales.loc[idx, "Fecha_InfoRecord"] = fecha
                elif nuevo_estatus == "Alta finalizada": df_materiales.loc[idx, "Fecha_Finalizada"] = fecha
                
                guardar_datos(df_materiales, df_historial)
                st.success("✅ Material actualizado correctamente")
                st.rerun()

elif opcion == "Seguimiento completo":
    st.markdown("<h1 style='color: #005691;'>📊 Seguimiento Completo</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    filtro_linea = col1.selectbox("Filtrar línea", ["Todas"] + LINEAS)
    filtro_estatus = col2.selectbox("Filtrar estatus", ["Todos"] + STATUS)
    filtro_pract = col3.text_input("Filtrar practicante")
    
    df_view = df_materiales.copy()
    if filtro_linea != "Todas": df_view = df_view[df_view["Linea"] == filtro_linea]
    if filtro_estatus != "Todos": df_view = df_view[df_view["Estatus"] == filtro_estatus]
    if filtro_pract: df_view = df_view[df_view["Practicante_Asignado"].str.contains(filtro_pract, case=False, na=False)]
    
    st.dataframe(df_view[["ID_Material", "Descripcion", "Linea", "Estatus", "Practicante_Asignado"]], use_container_width=True)

elif opcion == "Dashboard" and st.session_state.rol == "jefa":
    st.markdown("<h1 style='color: #005691;'>📈 Dashboard Ejecutivo</h1>", unsafe_allow_html=True)
    
    # MÉTRICAS GENERALES
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total materiales", len(df_materiales))
    col2.metric("Pendientes", len(df_materiales[df_materiales["Estatus"] != "Alta finalizada"]))
    col3.metric("Finalizados", len(df_materiales[df_materiales["Estatus"] == "Alta finalizada"]))
    col4.metric("Semana actual", len(df_materiales[df_materiales["Fecha_Solicitud"] >= datetime.now().strftime('%Y-%m-%d')]))
    
    # GRÁFICAS
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<h3>Por Estatus</h3>", unsafe_allow_html=True)
        st.bar_chart(df_materiales["Estatus"].value_counts())
    
    with col2:
        st.markdown("<h3>Por Línea</h3>", unsafe_allow_html=True)
        st.bar_chart(df_materiales["Linea"].value_counts())
    
    # POR PRACTICANTE
    st.markdown("<h3>Productividad por Practicante</h3>", unsafe_allow_html=True)
    df_finalizados = df_materiales[df_materiales["Estatus"] == "Alta finalizada"]
    if not df_finalizados.empty:
        st.bar_chart(df_finalizados["Practicante_Asignado"].value_counts())

elif opcion == "Mis solicitudes":
    st.markdown("<h1 style='color: #005691;'>📋 Mis Solicitudes</h1>", unsafe_allow_html=True)
    df_mis = df_materiales[df_materiales["Ingeniero"] == st.session_state.user]
    st.dataframe(df_mis[["ID_Solicitud", "Linea", "Prioridad", "Estatus"]], use_container_width=True)
