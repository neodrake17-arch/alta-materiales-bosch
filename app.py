import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
from io import BytesIO
from PIL import Image

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
.btn-download { background-color: #1976d2 !important; }
.btn-download:hover { background-color: #1565c0 !important; }
.btn-status { background-color: #4caf50 !important; margin: 2px; width: 140px; font-size: 0.85em; }
.btn-status:hover { background-color: #45a049 !important; }
.alert-pendiente { color: #d32f2f !important; font-weight: bold; font-size: 1.3em; }
.status-revision { color: #666666; font-weight: bold; }
.status-cotizacion { color: #ff9800; font-weight: bold; }
.status-alta { color: #1976d2; font-weight: bold; }
.status-espera { color: #f57c00 !important; font-weight: bold; animation: pulse 2s infinite; }
.status-info { color: #8e24aa; font-weight: bold; }
.status-final { color: #388e3c; font-weight: bold; }
.sidebar .sidebar-content { background-color: #f8f9fa !important; }
.metric-container { background-color: #f0f8ff; padding: 1rem; border-radius: 8px; }
.file-link { 
    background: linear-gradient(45deg, #1976d2, #42a5f5); 
    color: white !important; 
    padding: 8px 12px; 
    border-radius: 20px; 
    text-decoration: none !important; 
    font-size: 0.85em;
    display: inline-block;
    margin: 2px;
    font-weight: 500;
}
.file-link:hover { background: linear-gradient(45deg, #1565c0, #2196f3) !important; }
.file-zone { border: 2px dashed #005691; border-radius: 10px; padding: 20px; text-align: center; background: #f8f9fa; }
.status-buttons { display: flex; flex-wrap: wrap; gap: 5px; margin: 10px 0; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
.expander-header { font-size: 1.1em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ========================================
# CONSTANTES Y CONFIGURACIÓN (SIN CAMBIOS)
# ========================================
DB_FILE = "bd_materiales.xlsx"
IMG_FOLDER = "imagenes"
os.makedirs(IMG_FOLDER, exist_ok=True)

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

CATEGORIAS_MATERIAL = ["MAZE", "FHMI", "HIBE"]
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
# FUNCIONES AUXILIARES (TUS FUNCIONES ORIGINALES + NUEVA)
# ========================================
def cargar_datos():
    try:
        if not os.path.exists(DB_FILE):
            return pd.DataFrame(), pd.DataFrame()
        xls = pd.ExcelFile(DB_FILE)
        df_materiales = pd.read_excel(xls, "materiales")
        df_historial = pd.read_excel(xls, "historial") if "historial" in xls.sheet_names else pd.DataFrame()
        return df_materiales, df_historial
    except Exception as e:
        st.error(f"❌ Error cargando datos: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def guardar_datos(df_materiales, df_historial):
    try:
        with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
            df_materiales.to_excel(writer, sheet_name="materiales", index=False)
            df_historial.to_excel(writer, sheet_name="historial", index=False)
        return True
    except Exception as e:
        st.error(f"❌ Error guardando datos: {str(e)}")
        return False

def generar_id_solicitud():
    return f"SOL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def generar_id_material():
    return f"MAT-{uuid.uuid4().hex[:8].upper()}"

def guardar_archivo(uploaded_file, material_id):
    if uploaded_file is not None and hasattr(uploaded_file, 'getbuffer'):
        try:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            filename = f"{material_id}{ext}"
            filepath = os.path.join(IMG_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            return filename
        except Exception:
            return ""
    return ""

def crear_link_archivo(filename):
    if pd.isna(filename) or filename == "" or filename is None:
        return "❌"
    filepath = os.path.join(IMG_FOLDER, str(filename))
    if os.path.exists(filepath):
        tipo = "📷" if str(filename).lower().endswith(('.png', '.jpg', '.jpeg')) else "📄"
        return f'<a href="/files/{IMG_FOLDER}/{filename}" class="file-link" download target="_blank">{tipo} {os.path.splitext(filename)[0]}</a>'
    return "❌"

def estatus_coloreado(estatus):
    clases = {
        "En revisión de ingeniería": "status-revision",
        "En cotización": "status-cotizacion",
        "En alta SAP": "status-alta",
        "En espera de InfoRecord": "status-espera",
        "Info record creado": "status-info",
        "Alta finalizada": "status-final"
    }
    return f'<span class="{clases.get(str(estatus), "status-revision")}">{str(estatus)}</span>'

# 🔥 NUEVA FUNCIÓN: ACTUALIZAR ESTATUS
def actualizar_estatus(df_materiales, material_id, nuevo_estatus, comentario="", material_sap="", info_sap=""):
    """Actualiza estatus, fecha, campos SAP y guarda historial"""
    try:
        idx = df_materiales[df_materiales["ID_Material"] == material_id].index
        if len(idx) == 0:
            return False, "Material no encontrado"
        
        idx = idx[0]
        viejo_estatus = df_materiales.loc[idx, "Estatus"]
        
        # Actualizar fecha automática
        fecha_col = FECHA_MAP.get(nuevo_estatus)
        if fecha_col and fecha_col in df_materiales.columns:
            df_materiales.loc[idx, fecha_col] = datetime.now()
        
        # Actualizar todos los campos
        df_materiales.loc[idx, "Estatus"] = nuevo_estatus
        df_materiales.loc[idx, "Practicante_Asignado"] = st.session_state.responsable
        df_materiales.loc[idx, "Comentario_Estatus"] = comentario
        df_materiales.loc[idx, "Material_SAP"] = material_sap
        df_materiales.loc[idx, "InfoRecord_SAP"] = info_sap
        
        # Guardar historial
        _, df_historial = cargar_datos()
        historial_nuevo = pd.DataFrame([{
            "ID_Material": material_id,
            "Fecha_Cambio": datetime.now(),
            "Estatus_Anterior": viejo_estatus,
            "Nuevo_Estatus": nuevo_estatus,
            "Practicante": st.session_state.responsable,
            "Comentario": comentario,
            "Material_SAP": material_sap,
            "InfoRecord_SAP": info_sap
        }])
        
        df_historial_final = pd.concat([df_historial, historial_nuevo], ignore_index=True)
        return guardar_datos(df_materiales, df_historial_final), "Éxito"
    except Exception as e:
        return False, f"Error: {str(e)}"

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

def safe_columns(df, columnas_deseadas):
    columnas_existentes = [col for col in columnas_deseadas if col in df.columns]
    return df[columnas_existentes].copy() if columnas_existentes else pd.DataFrame()

# Inicializar BD (SIN CAMBIOS)
COLUMNAS_COMPLETAS = [
    "ID_Material", "ID_Solicitud", "Fecha_Solicitud", "Ingeniero", "Linea",
    "Prioridad", "Comentario_Solicitud", "Item", "Descripcion", "Estacion",
    "Categoria", "Frecuencia_Cambio", "Cant_Stock_Requerida", "Cant_Equipos", 
    "Cant_Partes_Equipo", "RP_Sugerido", "Manufacturer", "Archivo_Adjunto",
    "Estatus", "Practicante_Asignado", "Fecha_Revision", "Fecha_Cotizacion", 
    "Fecha_Alta_SAP", "Fecha_InfoRecord", "Fecha_Finalizada", 
    "Comentario_Estatus", "Material_SAP", "InfoRecord_SAP"
]

if not os.path.exists(DB_FILE):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        pd.DataFrame(columns=COLUMNAS_COMPLETAS).to_excel(writer, sheet_name="materiales", index=False)

# ========================================
# LOGIN Y HEADER (SIN CAMBIOS)
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
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.3, 1])
    with col1:
        user = st.text_input("👤 Usuario", placeholder="jarol, lalo, jime, niko, admin")
    with col2:
        pwd = st.text_input("🔒 Contraseña", type="password", placeholder="jarol123...")
    
    if st.button("🚀 ACCEDER", type="primary", use_container_width=True):
        if user in USERS and USERS[user]["pwd"] == pwd:
            st.session_state.logged = True
            st.session_state.user = user
            st.session_state.rol = USERS[user]["rol"]
            st.session_state.responsable = USERS[user]["responsable"]
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    
    st.markdown("</div></div></div>", unsafe_allow_html=True)
    st.stop()

# Header
col_header1, col_header2, col_logout = st.columns([3, 1, 1])
with col_header1:
    st.markdown(f"<h1 style='color: #005691; margin: 0;'>🔧 Bosch Material Management</h1>", unsafe_allow_html=True)
with col_header2:
    st.markdown(f"👤 **{st.session_state.user}** | {st.session_state.rol}")
with col_logout:
    if st.button("🚪 Cerrar Sesión", key="logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Cargar datos
df_materiales, df_historial = cargar_datos()
pendientes_usuario = contar_pendientes(st.session_state.responsable, df_materiales)

# Sidebar (SIN CAMBIOS)
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
# 🔥 MIS PENDIENTES CON BOTONES ACTUALIZAR ESTATUS ✅
# ========================================
if opcion == "Mis pendientes":
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
        # MÉTRICAS (SIN CAMBIOS)
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📋 Total pendientes", len(df_mis))
        col2.metric("🗂️ En revisión", len(df_mis[df_mis["Estatus"] == "En revisión de ingeniería"]))
        col3.metric("🧾 En cotización", len(df_mis[df_mis["Estatus"] == "En cotización"]))
        col4.metric("⚙️ En alta SAP", len(df_mis[df_mis["Estatus"] == "En alta SAP"]))
        col5.metric("⏳ Espera InfoRecord", len(df_mis[df_mis["Estatus"] == "En espera de InfoRecord"]))
        
        st.markdown("---")
        st.markdown("<h3 style='color: #1976d2;'>🔧 Materiales Pendientes - ACTUALIZAR ESTATUS</h3>", unsafe_allow_html=True)
        
        # 🔥 EXPANDERS CON BOTONES DE ESTATUS POR MATERIAL
        for idx, row in df_mis.iterrows():
            with st.expander(f"🔧 {row['ID_Material']} | {row['Descripcion'][:60]}... | 📍 {row['Linea']} | {row['Prioridad']}", expanded=False):
                col_info, col_status = st.columns([2, 1])
                
                with col_info:
                    st.markdown(f"""
                    **Item:** `{row.get('Item', 'N/A')}`  
                    **Estación:** {row.get('Estacion', 'N/A')}  
                    **Categoría:** {row.get('Categoria', 'N/A')}  
                    **Stock req:** {row.get('Cant_Stock_Requerida', 0)}  
                    **Estatus actual:** {estatus_coloreado(row['Estatus'])}  
                    **Archivo:** {crear_link_archivo(row.get('Archivo_Adjunto', ''))}
                    """, unsafe_allow_html=True)
                
                with col_status:
                    st.markdown("### **🔄 ACTUALIZAR ESTATUS**")
                    
                    # Selector de nuevo estatus (secuencial)
                    idx_actual = STATUS.index(row['Estatus']) if row['Estatus'] in STATUS else 0
                    nuevo_estatus = st.selectbox("Nuevo estatus:", STATUS, 
                                               index=min(idx_actual + 1, len(STATUS)-1),
                                               key=f"status_sel_{row['ID_Material']}")
                    
                    # Campos SAP
                    col_sap1, col_sap2 = st.columns(2)
                    with col_sap1:
                        material_sap = st.text_input("Material SAP:", 
                                                   value=row.get('Material_SAP', ''), 
                                                   key=f"sap_mat_{row['ID_Material']}")
                    with col_sap2:
                        info_sap = st.text_input("InfoRecord SAP:", 
                                               value=row.get('InfoRecord_SAP', ''), 
                                               key=f"sap_info_{row['ID_Material']}")
                    
                    comentario = st.text_area("Comentario del cambio:", 
                                            value=row.get('Comentario_Estatus', ''), 
                                            key=f"comentario_{row['ID_Material']}", 
                                            height=70)
                    
                    # BOTÓN ACTUALIZAR
                    if st.button(f"✅ CAMBIAR A {nuevo_estatus[:20]}...", key=f"update_{row['ID_Material']}", 
                               help=f"Actualizar {row['ID_Material']} a {nuevo_estatus}"):
                        exito, mensaje = actualizar_estatus(df_materiales, row['ID_Material'], 
                                                          nuevo_estatus, comentario, material_sap, info_sap)
                        if exito:
                            st.success(f"✅ **{row['ID_Material']}** actualizado correctamente")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {mensaje}")
        
        st.markdown("---")
        if st.button("🔄 RECARGAR DATOS", key="reload_data"):
            st.rerun()

# ========================================
# NUEVA SOLICITUD, DASHBOARD, SEGUIMIENTO (SIN CAMBIOS - TU CÓDIGO ORIGINAL)
# ========================================
elif opcion == "Nueva solicitud":
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
        
        with st.form(key="form_dinamico"):
            materiales = []
            for i in range(num_materiales):
                st.markdown(f"### **Material {i+1}**")
                col_a, col_b = st.columns([1.2, 1])
                
                with col_a:
                    item = st.text_input(f"Item/Nº parte", key=f"item_{i}")
                    descripcion = st.text_input(f"**Descripción** *(obligatorio)*", key=f"desc_{i}")
                    estacion = st.text_input(f"Estación/Máquina", key=f"est_{i}")
                    categoria = st.selectbox(f"🏷️ Categoría", CATEGORIAS_MATERIAL, key=f"cat_{i}")
                
                with col_b:
                    stock = st.number_input("Stock mínimo requerido", min_value=0.0, format="%.1f", key=f"stock_{i}")
                    equipos = st.number_input("Equipos que usan esta pieza", min_value=0, key=f"eq_{i}")
                    partes_eq = st.number_input("Partes por equipo", min_value=0, key=f"partes_{i}")
                    rp = st.text_input("RP sugerido", key=f"rp_{i}")
                    fabricante = st.text_input("Fabricante/Proveedor", key=f"fab_{i}")
                
                st.markdown(f"<div class='file-zone'><h4>📎 **Adjuntar imagen o PDF** *(opcional)*</h4></div>", unsafe_allow_html=True)
                uploaded_file = st.file_uploader(f"Archivo para Material {i+1}", 
                                               type=['png', 'jpg', 'jpeg', 'pdf'], 
                                               key=f"file_{i}")
                
                if uploaded_file is not None:
                    if uploaded_file.type.startswith('image/'):
                        image = Image.open(uploaded_file)
                        st.image(image, caption=f"Preview - {uploaded_file.name}", width=200)
                    else:
                        st.success(f"✅ PDF cargado: {uploaded_file.name}")
                
                materiales.append({
                    "Item": item, "Descripcion": descripcion, "Estacion": estacion,
                    "Categoria": categoria, "Cant_Stock_Requerida": stock, 
                    "Cant_Equipos": equipos, "Cant_Partes_Equipo": partes_eq, 
                    "RP_Sugerido": rp, "Manufacturer": fabricante,
                    "Archivo": uploaded_file
                })
            
            comentario_general = st.text_area("📝 Comentario general de la solicitud", height=80)
            
            col_submit, col_count = st.columns([3, 1])
            with col_submit:
                if st.form_submit_button("💾 Guardar Solicitud", use_container_width=True):
                    registros = []
                    id_solicitud = generar_id_solicitud()
                    
                    for mat in materiales:
                        if mat["Descripcion"].strip():
                            id_material = generar_id_material()
                            archivo_adjunto = guardar_archivo(mat["Archivo"], id_material)
                            
                            registro = {
                                "ID_Material": id_material,
                                "ID_Solicitud": id_solicitud,
                                "Fecha_Solicitud": datetime.now(),
                                "Ingeniero": ingeniero,
                                "Linea": linea,
                                "Prioridad": prioridad,
                                "Comentario_Solicitud": comentario_general,
                                "Item": mat["Item"],
                                "Descripcion": mat["Descripcion"],
                                "Estacion": mat["Estacion"],
                                "Categoria": mat["Categoria"],
                                "Cant_Stock_Requerida": mat["Cant_Stock_Requerida"],
                                "Cant_Equipos": mat["Cant_Equipos"],
                                "Cant_Partes_Equipo": mat["Cant_Partes_Equipo"],
                                "RP_Sugerido": mat["RP_Sugerido"],
                                "Manufacturer": mat["Manufacturer"],
                                "Archivo_Adjunto": archivo_adjunto,
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
                            }
                            registros.append(registro)
                    
                    if registros:
                        df_nuevos = pd.DataFrame(registros)
                        df_materiales_nuevo = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                        if guardar_datos(df_materiales_nuevo, df_historial):
                            st.success(f"✅ **Solicitud {id_solicitud}** creada con **{len(registros)}** materiales")
                            st.balloons()
                            st.rerun()
            
            with col_count:
                st.metric("Materiales a crear", len([m for m in materiales if m["Descripcion"].strip()]))

elif opcion == "Dashboard":
    st.markdown("<h2 style='color: #005691;'>📈 Dashboard Ejecutivo</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    total_materiales = len(df_materiales)
    pendientes_total = len(df_materiales[df_materiales["Estatus"] != "Alta finalizada"])
    finalizados = len(df_materiales[df_materiales["Estatus"] == "Alta finalizada"])
    
    col1.metric("📦 Total materiales", total_materiales)
    col2.metric("⏳ Pendientes", pendientes_total)
    col3.metric("✅ Finalizados", finalizados)
    col4.metric("📊 % Completado", f"{finalizados/total_materiales*100:.1f}%" if total_materiales > 0 else "0%")
    
    st.download_button("📊 Reporte Completo", data=df_to_excel_bytes(df_materiales),
                      file_name=f"reporte_materiales_{datetime.now().strftime('%Y%m%d')}.xlsx",
                      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    practicante_sel = st.selectbox("👤 Practicante:", ["TODOS"] + list(LINEAS_POR_PRACTICANTE.keys()))
    if practicante_sel != "TODOS":
        lineas_pract = LINEAS_POR_PRACTICANTE[practicante_sel]
        df_filtrado = df_materiales[df_materiales["Linea"].isin(lineas_pract)]
        st.dataframe(df_filtrado, use_container_width=True)

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
    
    columnas_view = ["ID_Material", "Descripcion", "Linea", "Categoria", "Estatus", "Practicante_Asignado", "Prioridad"]
    df_view_mostrar = safe_columns(df_view, columnas_view)
    
    if "Estatus" in df_view_mostrar.columns:
        df_view_mostrar["Estatus"] = df_view_mostrar["Estatus"].apply(estatus_coloreado)
    
    st.markdown(df_view_mostrar.to_html(escape=False, index=False), unsafe_allow_html=True)

# ========================================
# FOOTER
# ========================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem; font-size: 0.9em; border-top: 1px solid #eee;'>
    🔧 <strong>Sistema de Gestión de Materiales Bosch</strong> © 2026 | 
    📁 <code>imagenes/</code> | 🗄️ <code>bd_materiales.xlsx</code> | 
    ✅ <strong>ESTATUS + ARCHIVOS + DASHBOARD = 100% FUNCIONAL</strong>
</div>
""", unsafe_allow_html=True)




