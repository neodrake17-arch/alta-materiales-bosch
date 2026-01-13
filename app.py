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
h1, h2, h3, h4 { color: #005691; font-weight: bold; }
h1 { font-size: 2.5em; margin-bottom: 1rem; }
.stButton>button { 
    background-color: #005691 !important; 
    color: white !important; 
    border-radius: 8px !important; 
    height: 42px; 
    font-weight: 600; 
    border: none !important;
}
.stButton>button:hover { background-color: #003d6b !important; }
.btn-logout { background-color: #d32f2f !important; width: 100%; }
.btn-logout:hover { background-color: #b71c1c !important; }
.alert-pendiente { color: #d32f2f !important; font-weight: bold; font-size: 1.3em; }
.status-revision { color: #666666; font-weight: bold; }
.status-cotizacion { color: #ff9800; font-weight: bold; }
.status-alta { color: #1976d2; font-weight: bold; }
.status-espera { color: #f57c00 !important; font-weight: bold; animation: pulse 2s infinite; }
.status-info { color: #8e24aa; font-weight: bold; }
.status-final { color: #388e3c; font-weight: bold; }
.sidebar .sidebar-content { background-color: #f8f9fa !important; }
.metric-container { background-color: #f0f8ff; padding: 1rem; border-radius: 8px; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
</style>
""", unsafe_allow_html=True)

# ========================================
# CONSTANTES Y CONFIGURACIÓN
# ========================================
DB_FILE = "bd_materiales.xlsx"
os.makedirs("imagenes", exist_ok=True)

USERS = {
    "jarol": {"pwd": "jarol123", "rol": "practicante", "responsable": "Jarol"},
    "lalo": {"pwd": "lalo123", "rol": "practicante", "responsable": "Lalo"},
    "jime": {"pwd": "jime123", "rol": "practicante", "responsable": "Jime"},
    "niko": {"pwd": "niko123", "rol": "practicante", "responsable": "Niko"},
    "admin": {"pwd": "admin123", "rol": "jefa", "responsable": "Admin"}
}

LINEAS_POR_PRACTICANTE = {
    "Jarol": ["DP 02", "SCU 33", "SCU 34", "SCU 48", "SSL1"],
    "Lalo": ["APA 36", "APA 38", "SERVO 10", "SERVO 24"],
    "Jime": ["DP 32", "DP 35", "SENSOR 28", "SENSOR 5"],
    "Niko": ["KGT 22", "KGT 23", "LG 01", "LG 03"]
}

LINEAS = list(set(sum(LINEAS_POR_PRACTICANTE.values(), [])))
STATUS = ["En revisión de ingeniería", "En cotización", "En alta SAP", 
          "En espera de InfoRecord", "Info record creado", "Alta finalizada"]

FECHA_MAP = {
    "En cotización": "Fecha_Cotizacion",
    "En alta SAP": "Fecha_Alta_SAP",
    "En espera de InfoRecord": "Fecha_InfoRecord", 
    "Info record creado": "Fecha_InfoRecord",
    "Alta finalizada": "Fecha_Finalizada"
}

# ========================================
# FUNCIONES AUXILIARES
# ========================================
def cargar_datos():
    try:
        if not os.path.exists(DB_FILE):
            return pd.DataFrame(), pd.DataFrame()
        xls = pd.ExcelFile(DB_FILE)
        df_materiales = pd.read_excel(xls, "materiales")
        df_historial = pd.read_excel(xls, "historial") if "historial" in xls.sheet_names else pd.DataFrame()
        return df_materiales, df_historial
    except FileNotFoundError:
        st.info("📄 Creando base de datos nueva...")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error cargando datos: {str(e)}")
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
        "En espera de InfoRecord": "status-espera",
        "Info record creado": "status-info",
        "Alta finalizada": "status-final"
    }
    return f'<span class="{clases.get(estatus, "status-revision")}">{estatus}</span>'

def df_to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte")
    return output.getvalue()

def contar_pendientes(usuario, df_materiales):
    if usuario in LINEAS_POR_PRACTICANTE:
        lineas = LINEAS_POR_PRACTICANTE[usuario]
        return len(df_materiales[(df_materiales["Linea"].isin(lineas)) & 
                                (df_materiales["Estatus"] != "Alta finalizada")])
    return 0

# INICIALIZAR BASE DE DATOS
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

# ========================================
# LOGIN LIMPIO
# ========================================
if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);'>
        <div style='max-width: 450px; margin: auto;'>
            <h1 style='color: #005691; margin-bottom: 1.5rem; font-size: 2.8em;'>🔧 Bosch Materiales</h1>
            <div style='background: white; padding: 2.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.15);'>
                <h3 style='color: #333; margin-bottom: 2rem; font-size: 1.4em;'>Iniciar Sesión</h3>
                <div style='margin-bottom: 1.5rem;'>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.3, 1])
    with col1:
        user = st.text_input("👤 Usuario", placeholder="Escribe tu usuario", 
                           help="Ingresa tu nombre de usuario")
    with col2:
        pwd = st.text_input("🔒 Contraseña", type="password", placeholder="********",
                          help="Ingresa tu contraseña")
    
    col_btn, col_spacer = st.columns([1, 3])
    with col_btn:
        if st.button("🚀 ACCEDER", type="primary", use_container_width=True):
            if user in USERS and USERS[user]["pwd"] == pwd:
                st.session_state.logged = True
                st.session_state.user = user
                st.session_state.rol = USERS[user]["rol"]
                st.session_state.responsable = USERS[user]["responsable"]
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
                st.info("💡 Contacta al administrador si necesitas ayuda")
    
    st.markdown("""
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ========================================
# HEADER CON BOTÓN CERRAR SESIÓN
# ========================================
col_header1, col_header2, col_logout = st.columns([3, 1, 1])
with col_header1:
    st.markdown(f"<h1 style='color: #005691; margin: 0;'>🔧 Bosch Material Management</h1>", unsafe_allow_html=True)
with col_header2:
    st.markdown(f"👤 **{st.session_state.user}** | {st.session_state.rol}")
with col_logout:
    if st.button("🚪 Cerrar Sesión", key="logout", help="Salir de la sesión actual"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ========================================
# CARGAR DATOS
# ========================================
df_materiales, df_historial = cargar_datos()
pendientes_usuario = contar_pendientes(st.session_state.responsable, df_materiales)

# ========================================
# SIDEBAR DINÁMICO POR ROL
# ========================================
with st.sidebar:
    st.markdown("<h3 style='color: #005691; margin-bottom: 1rem;'>📋 Menú Principal</h3>", unsafe_allow_html=True)
    
    if st.session_state.rol == "practicante":
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #ffebee 0%, #ffcdd2 100%); 
                    padding: 1.2rem; border-radius: 10px; border-left: 6px solid #d32f2f; 
                    margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(211,47,47,0.15);'>
            <div class='alert-pendiente'>🔔 **{pendientes_usuario} PENDIENTES**</div>
            <small style='color: #666; font-size: 0.85em;'>
                Líneas: {', '.join(LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, []))}
            </small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"👤 **{st.session_state.user}**")
    st.markdown(f"🎭 **{st.session_state.rol}**")
    st.markdown(f"🏢 **{st.session_state.responsable}**")
    st.markdown("---")
    
    if st.session_state.rol == "practicante":
        opcion = st.radio("Navegar:", ["Mis pendientes", "Seguimiento completo", "Nueva solicitud"])
    elif st.session_state.rol == "jefa":
        st.metric("📊 Total pendientes sistema", pendientes_usuario)
        opcion = st.radio("Navegar:", ["Dashboard", "Seguimiento", "Nueva solicitud"])
    else:
        opcion = st.radio("Navegar:", ["Nueva solicitud", "Mis solicitudes"])

# ========================================
# NUEVA SOLICITUD
# ========================================
if opcion == "Nueva solicitud":
    st.markdown("<h2 style='color: #005691;'>📋 Nueva Solicitud de Materiales</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    ingeniero = col1.text_input("👨‍🔧 Ingeniero solicitante", value=st.session_state.user)
    linea = col2.selectbox("🏭 Línea de producción", LINEAS)
    prioridad = col3.selectbox("🔥 Prioridad", ["Alta", "Media", "Baja"])
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📝 Formulario Dinámico (1-5)", "📊 Excel Masivo (>5)"])
    
    with tab1:
        st.info("**Selecciona cuántos materiales quieres registrar**")
        num_materiales = st.slider("🔢 Número de materiales:", min_value=1, max_value=5, value=1)
        st.markdown(f"**✨ Mostrando {num_materiales} formulario(s):**")
        
        with st.form(key="form_dinamico"):
            materiales = []
            for i in range(num_materiales):
                st.markdown(f"### **Material {i+1}**")
                col_a, col_b = st.columns([1.2, 1])
                
                with col_a:
                    item = st.text_input(f"Item/Nº parte", key=f"item_{i}")
                    descripcion = st.text_input(f"**Descripción** *(obligatorio)*", key=f"desc_{i}")
                    estacion = st.text_input(f"Estación/Máquina", key=f"est_{i}")
                
                with col_b:
                    stock = st.number_input("Stock mínimo requerido", min_value=0.0, format="%.1f", key=f"stock_{i}")
                    equipos = st.number_input("Equipos que usan esta pieza", min_value=0, key=f"eq_{i}")
                    partes_eq = st.number_input("Partes por equipo", min_value=0, key=f"partes_{i}")
                    rp = st.text_input("RP sugerido", key=f"rp_{i}")
                    fabricante = st.text_input("Fabricante/Proveedor", key=f"fab_{i}")
                
                materiales.append({
                    "Item": item, "Descripcion": descripcion, "Estacion": estacion,
                    "Cant_Stock_Requerida": stock, "Cant_Equipos": equipos,
                    "Cant_Partes_Equipo": partes_eq, "RP_Sugerido": rp, "Manufacturer": fabricante
                })
            
            comentario_general = st.text_area("📝 Comentario general de la solicitud", height=80)
            
            col_submit, col_count = st.columns([3, 1])
            with col_submit:
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
                        df_materiales_nuevo = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                        guardar_datos(df_materiales_nuevo, df_historial)
                        st.success(f"✅ **Solicitud {id_solicitud}** creada con **{len(registros)}** materiales")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Completa al menos **una descripción**")
            
            with col_count:
                st.metric("Materiales a crear", len([m for m in materiales if m["Descripcion"].strip()]))
    
    with tab2:
        columnas = ["Item", "Descripcion", "Estacion", "Frecuencia_Cambio", 
                   "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo", 
                   "RP_Sugerido", "Manufacturer"]
        plantilla_df = pd.DataFrame(columns=columnas)
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.download_button("📥 Descargar Plantilla", data=df_to_excel_bytes(plantilla_df),
                             file_name="plantilla_materiales_bosch.xlsx", 
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        with col2:
            archivo = st.file_uploader("📤 Subir plantilla completada", type=["xlsx"])
            with st.form("form_masivo"):
                comentario_general = st.text_area("Comentario general")
                if st.form_submit_button("💾 Guardar Masivo") and archivo is not None:
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
                            df_materiales_nuevo = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                            guardar_datos(df_materiales_nuevo, df_historial)
                            st.success(f"✅ **{id_solicitud}** - {len(registros)} materiales masivos guardados")
                            st.balloons()
                        else:
                            st.error("❌ Plantilla sin descripciones válidas")
                    except Exception as e:
                        st.error(f"❌ Error procesando Excel: {str(e)}")

# ========================================
# MIS PENDIENTES - PRACTICANTES (MEJORADO)
# ========================================
elif opcion == "Mis pendientes":
    st.markdown(f"<h2 style='color: #005691;'>📋 Mis Pendientes - {st.session_state.responsable}</h2>", unsafe_allow_html=True)
    
    mis_lineas = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_mis = df_materiales[
        (df_materiales["Linea"].isin(mis_lineas)) & 
        (df_materiales["Estatus"] != "Alta finalizada")
    ].copy()
    
    if df_mis.empty:
        st.markdown("## 🎉 ¡Felicidades!")
        st.success("**No tienes materiales pendientes.** ✅")
    else:
        # MÉTRICAS MEJORADAS (5 columnas)
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📋 Total pendientes", len(df_mis))
        col2.metric("🗂️ En revisión", len(df_mis[df_mis["Estatus"] == "En revisión de ingeniería"]))
        col3.metric("🧾 En cotización", len(df_mis[df_mis["Estatus"] == "En cotización"]))
        col4.metric("⚙️ En alta SAP", len(df_mis[df_mis["Estatus"] == "En alta SAP"]))
        col5.metric("⏳ Espera InfoRecord", len(df_mis[df_mis["Estatus"] == "En espera de InfoRecord"]))
        
        st.markdown("---")
        st.markdown("<h3 style='color: #1976d2;'>📊 Materiales Pendientes</h3>", unsafe_allow_html=True)
        df_mostrar = df_mis[["ID_Material", "ID_Solicitud", "Descripcion", "Linea", "Estatus", "Prioridad"]].copy()
        df_mostrar["Estatus"] = df_mostrar["Estatus"].apply(estatus_coloreado)
        st.markdown(df_mostrar.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        # ACTUALIZAR MATERIAL INDIVIDUAL - MOSTRAR TODO
        st.markdown("---")
        st.markdown("<h3 style='color: #666;'>🔄 Actualizar Material</h3>", unsafe_allow_html=True)
        id_material = st.text_input("🔍 Ingresa ID_Material:")
        
        if id_material and id_material in df_mis["ID_Material"].values:
            idx = df_materiales[df_materiales["ID_Material"] == id_material].index[0]
            reg = df_materiales.loc[idx]
            
            st.markdown("---")
            st.markdown(f"<h4 style='color: #005691;'>📋 **Información Completa del Material**</h4>", unsafe_allow_html=True)
            
            col_info1, col_info2 = st.columns([1, 1])
            with col_info1:
                st.markdown(f"**👨‍🔧 Ingeniero:** {reg['Ingeniero']}")
                st.markdown(f"**🏭 Línea:** {reg['Linea']}")
                st.markdown(f"**🔥 Prioridad:** {reg['Prioridad']}")
                st.markdown(f"**📝 Comentario solicitud:** {reg.get('Comentario_Solicitud', 'N/A')}")
            
            with col_info2:
                st.markdown(f"**📦 Item:** {reg.get('Item', 'N/A')}")
                st.markdown(f"**📄 Descripción:** **{reg['Descripcion']}**")
                st.markdown(f"**🏢 Estación:** {reg.get('Estacion', 'N/A')}")
            
            col_detalle1, col_detalle2 = st.columns([1, 1])
            with col_detalle1:
                st.markdown(f"**📊 Stock requerido:** {reg.get('Cant_Stock_Requerida', 0)}")
                st.markdown(f"**⚙️ Equipos:** {reg.get('Cant_Equipos', 0)}")
                st.markdown(f"**🔩 Partes/equipo:** {reg.get('Cant_Partes_Equipo', 0)}")
            
            with col_detalle2:
                st.markdown(f"**💡 RP sugerido:** {reg.get('RP_Sugerido', 'N/A')}")
                st.markdown(f"**🏭 Fabricante:** {reg.get('Manufacturer', 'N/A')}")
                st.markdown(f"**📋 Estatus actual:** {estatus_coloreado(reg['Estatus'])}", unsafe_allow_html=True)
            
            col_est1, col_est2 = st.columns(2)
            nuevo_estatus = col_est1.selectbox("➡️ Nuevo estatus:", STATUS, 
                                             index=STATUS.index(reg["Estatus"]))
            practicante = col_est2.text_input("👤 Asignado a:", value=st.session_state.responsable)
            
            col_sap1, col_sap2 = st.columns(2)
            material_sap = col_sap1.text_input("🆔 Material SAP:", value=reg.get("Material_SAP", ""))
            info_sap = col_sap2.text_input("📋 InfoRecord SAP:", value=reg.get("InfoRecord_SAP", ""))
            
            comentario = st.text_area("📝 Comentario del avance:", height=60)
            
            if st.button("✅ ACTUALIZAR ESTATUS", type="primary", use_container_width=True):
                df_materiales.loc[idx, "Estatus"] = nuevo_estatus
                df_materiales.loc[idx, "Practicante_Asignado"] = practicante
                df_materiales.loc[idx, "Comentario_Estatus"] = comentario
                df_materiales.loc[idx, "Material_SAP"] = material_sap
                df_materiales.loc[idx, "InfoRecord_SAP"] = info_sap
                
                fecha = datetime.now()
                if nuevo_estatus in FECHA_MAP:
                    df_materiales.loc[idx, FECHA_MAP[nuevo_estatus]] = fecha
                
                guardar_datos(df_materiales, df_historial)
                st.success("✅ **Material actualizado correctamente!** 🎉")
                st.balloons()
                st.rerun()

# ========================================
# DASHBOARD JEFA (MEJORADO CON GRÁFICAS)
# ========================================
elif opcion == "Dashboard":
    st.markdown("<h2 style='color: #005691;'>📈 Dashboard Ejecutivo - Practicantes</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    total_materiales = len(df_materiales)
    pendientes_total = len(df_materiales[df_materiales["Estatus"] != "Alta finalizada"])
    finalizados = len(df_materiales[df_materiales["Estatus"] == "Alta finalizada"])
    
    col1.metric("📦 Total materiales", total_materiales)
    col2.metric("⏳ Pendientes", pendientes_total)
    col3.metric("✅ Finalizados", finalizados)
    col4.metric("📊 % Completado", f"{finalizados/total_materiales*100:.1f}%" if total_materiales > 0 else "0%")
    
    st.markdown("---")
    st.markdown("<h3 style='color: #005691;'>👥 Productividad por Practicante</h3>", unsafe_allow_html=True)
    
    df_pract = df_materiales[df_materiales["Practicante_Asignado"] != ""].copy()
    if not df_pract.empty:
        resumen_pract = df_pract.groupby("Practicante_Asignado")["Estatus"].value_counts().unstack(fill_value=0)
        
        col_graf1, col_graf2 = st.columns([2, 1])
        with col_graf1:
            st.markdown("**📊 Estatus por Practicante**")
            st.bar_chart(resumen_pract)
        
        with col_graf2:
            st.markdown("**🎯 Total por Practicante**")
            totales_pract = df_pract["Practicante_Asignado"].value_counts()
            st.bar_chart(totales_pract)
    else:
        st.info("📭 No hay materiales asignados a practicantes aún")
    
    # DESCARGAS
    st.markdown("---")
    st.markdown("<h3 style='color: #1976d2;'>📥 Descargar Reportes</h3>", unsafe_allow_html=True)
    col_desc1, col_desc2 = st.columns(2)
    
    with col_desc1:
        st.download_button("📊 Reporte Completo Excel", data=df_to_excel_bytes(df_materiales),
                         file_name=f"reporte_materiales_{datetime.now().strftime('%Y%m%d')}.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    with col_desc2:
        if not df_pract.empty:
            st.download_button("📈 Resumen Practicantes", data=df_to_excel_bytes(resumen_pract.reset_index()),
                             file_name=f"resumen_practicantes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    # TABLA DETALLADA
    st.markdown("---")
    practicante_sel = st.selectbox("👤 Seleccionar practicante:", ["TODOS"] + list(LINEAS_POR_PRACTICANTE.keys()))
    if practicante_sel != "TODOS":
        lineas_pract = LINEAS_POR_PRACTICANTE[practicante_sel]
        df_filtrado = df_materiales[df_materiales["Linea"].isin(lineas_pract)]
        st.dataframe(df_filtrado, use_container_width=True)

# ========================================
# SEGUIMIENTO COMPLETO
# ========================================
elif opcion in ["Seguimiento", "Seguimiento completo"]:
    st.markdown("<h2 style='color: #005691;'>🔍 Seguimiento Completo</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    filtro_linea = col1.selectbox("🏭 Línea:", ["Todas"] + LINEAS)
    filtro_estatus = col2.selectbox("📋 Estatus:", ["Todos"] + STATUS)
    filtro_pract = col3.text_input("👤 Practicante:")
    
    df_view = df_materiales.copy()
    if filtro_linea != "Todas": df_view = df_view[df_view["Linea"] == filtro_linea]
    if filtro_estatus != "Todos": df_view = df_view[df_view["Estatus"] == filtro_estatus]
    if filtro_pract: df_view = df_view[df_view["Practicante_Asignado"].str.contains(filtro_pract, case=False, na=False)]
    
    df_view_mostrar = df_view[["ID_Material", "Descripcion", "Linea", "Estatus", "Practicante_Asignado", "Prioridad"]].copy()
    df_view_mostrar["Estatus"] = df_view_mostrar["Estatus"].apply(estatus_coloreado)
    st.markdown(df_view_mostrar.to_html(escape=False, index=False), unsafe_allow_html=True)

# ========================================
# MIS SOLICITUDES
# ========================================
elif opcion == "Mis solicitudes":
    st.markdown(f"<h2 style='color: #005691;'>📋 Mis Solicitudes - {st.session_state.user}</h2>", unsafe_allow_html=True)
    df_mis = df_materiales[df_materiales["Ingeniero"] == st.session_state.user]
    
    if df_mis.empty:
        st.info("No has creado solicitudes aún. Usa 'Nueva solicitud' para empezar.")
    else:
        st.dataframe(df_mis[["ID_Solicitud", "Fecha_Solicitud", "Linea", "Prioridad", "Estatus"]], use_container_width=True)

# FOOTER
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem; font-size: 0.9em; border-top: 1px solid #eee;'>
    🔧 <strong>Sistema de Gestión de Materiales Bosch</strong> © 2026 | 
    Base de datos: <code>bd_materiales.xlsx</code>
</div>
""", unsafe_allow_html=True)

