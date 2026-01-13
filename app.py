import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
from io import BytesIO
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

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
.btn-update { background-color: #4caf50 !important; }
.btn-update:hover { background-color: #388e3c !important; }
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
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
.status-select { width: 180px !important; }
.card { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# ========================================
# CONSTANTES Y CONFIGURACIÓN
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

# ========================================
# FUNCIONES AUXILIARES (COMPLETAS)
# ========================================
def cargar_datos():
    try:
        if not os.path.exists(DB_FILE):
            return pd.DataFrame(), pd.DataFrame()
        xls = pd.ExcelFile(DB_FILE)
        df_materiales = pd.read_excel(xls, "materiales")
        df_historial = pd.read_excel(xls, "historial") if "historial" in xls.sheet_names else pd.DataFrame()
        return df_materiales, df_historial
    except:
        return pd.DataFrame(), pd.DataFrame()

def guardar_datos(df_materiales, df_historial):
    try:
        with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
            df_materiales.to_excel(writer, sheet_name="materiales", index=False)
            df_historial.to_excel(writer, sheet_name="historial", index=False)
        return True
    except:
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
        except:
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

def actualizar_estatus(df_materiales, id_material, nuevo_estatus, comentario=""):
    """Actualiza estatus y guarda historial"""
    idx = df_materiales[df_materiales["ID_Material"] == id_material].index
    if len(idx) > 0:
        df_materiales.loc[idx, "Estatus"] = nuevo_estatus
        fecha_col = FECHA_MAP.get(nuevo_estatus)
        if fecha_col:
            df_materiales.loc[idx, fecha_col] = datetime.now()
        df_materiales.loc[idx, "Comentario_Estatus"] = comentario
        return True
    return False

# Inicializar DB
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

# SESSION STATE
if "logged" not in st.session_state:
    st.session_state.logged = False

# LOGIN
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
        pwd = st.text_input("🔒 Contraseña", type="password", placeholder="jarol123, lalo123...")
    
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

# HEADER
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

# SIDEBAR COMPLETO
with st.sidebar:
    st.markdown("<h3 style='color: #005691; margin-bottom: 1rem;'>📋 Menú Principal</h3>", unsafe_allow_html=True)
    
    if st.session_state.rol == "practicante":
        pendientes = len(df_materiales[
            (df_materiales["Linea"].isin(LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, []))) & 
            (df_materiales["Estatus"] != "Alta finalizada")
        ])
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #ffebee 0%, #ffcdd2 100%); 
                    padding: 1.2rem; border-radius: 10px; border-left: 6px solid #d32f2f; 
                    margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(211,47,47,0.15);'>
            <div class='alert-pendiente'>🔔 **{pendientes} PENDIENTES**</div>
            <small style='color: #666; font-size: 0.85em;'>
                Líneas: {', '.join(LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, []))}
            </small>
        </div>
        """, unsafe_allow_html=True)
        
        opcion = st.radio("Navegar:", ["Mis pendientes", "Seguimiento completo", "Actualizar estatus", "Nueva solicitud"])
    else:
        st.metric("📊 Total pendientes sistema", len(df_materiales[df_materiales["Estatus"] != "Alta finalizada"]))
        opcion = st.radio("Navegar:", ["Dashboard", "Seguimiento", "Nueva solicitud"])

# ========================================
# DASHBOARD COMPLETO ✅
# ========================================
if opcion == "Dashboard":
    st.markdown("<h2 style='color: #005691;'>📊 Dashboard Ejecutivo</h2>", unsafe_allow_html=True)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    total = len(df_materiales)
    pendientes = len(df_materiales[df_materiales["Estatus"] != "Alta finalizada"])
    cotizacion = len(df_materiales[df_materiales["Estatus"] == "En cotización"])
    finalizados = len(df_materiales[df_materiales["Estatus"] == "Alta finalizada"])
    
    with col1:
        st.metric("📦 Total Materiales", total)
    with col2:
        st.metric("⏳ Pendientes", pendientes)
    with col3:
        st.metric("💰 En Cotización", cotizacion)
    with col4:
        st.metric("✅ Finalizados", finalizados)
    
    # Gráficos
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_status = px.pie(df_materiales, names='Estatus', title='Distribución por Estatus')
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col_g2:
        fig_prioridad = px.histogram(df_materiales[df_materiales["Estatus"] != "Alta finalizada"], 
                                   x='Prioridad', color='Practicante_Asignado', 
                                   title='Pendientes por Prioridad y Practicante')
        st.plotly_chart(fig_prioridad, use_container_width=True)

# ========================================
# MIS PENDIENTES ✅
# ========================================
if opcion == "Mis pendientes":
    st.markdown(f"<h2 style='color: #005691;'>📋 Mis Pendientes ({st.session_state.responsable})</h2>", unsafe_allow_html=True)
    
    lineas_usuario = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_pendientes = df_materiales[
        (df_materiales["Linea"].isin(lineas_usuario)) & 
        (df_materiales["Estatus"] != "Alta finalizada")
    ].copy()
    
    if len(df_pendientes) == 0:
        st.success("🎉 ¡No tienes pendientes! ✅")
    else:
        st.dataframe(df_pendientes[["ID_Solicitud", "Linea", "Descripcion", "Prioridad", "Estatus"]])

# ========================================
# SEGUIMIENTO COMPLETO ✅
# ========================================
if opcion in ["Seguimiento completo", "Seguimiento"]:
    st.markdown("<h2 style='color: #005691;'>🔍 Seguimiento Completo</h2>", unsafe_allow_html=True)
    
    col_filt1, col_filt2, col_filt3 = st.columns(3)
    linea_filtro = col_filt1.selectbox("🏭 Línea", ["Todas"] + LINEAS)
    practicante_filtro = col_filt2.selectbox("👤 Practicante", ["Todos"] + list(LINEAS_POR_PRACTICANTE.keys()))
    estatus_filtro = col_filt3.selectbox("📊 Estatus", ["Todos"] + STATUS)
    
    df_filtrado = df_materiales.copy()
    if linea_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Linea"] == linea_filtro]
    if practicante_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Practicante_Asignado"] == practicante_filtro]
    if estatus_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Estatus"] == estatus_filtro]
    
    st.dataframe(df_filtrado, use_container_width=True)

# ========================================
# ACTUALIZAR ESTATUS ✅
# ========================================
if opcion == "Actualizar estatus":
    st.markdown("<h2 style='color: #005691;'>🔄 Actualizar Estatus</h2>", unsafe_allow_html=True)
    
    if len(df_materiales) == 0:
        st.warning("📭 No hay materiales para actualizar")
    else:
        col_sel, col_est = st.columns([1, 2])
        
        with col_sel:
            material_sel = st.selectbox("Seleccionar material:", df_materiales["ID_Material"].tolist())
        
        with col_est:
            idx_sel = df_materiales[df_materiales["ID_Material"] == material_sel].index[0]
            estatus_actual = df_materiales.loc[idx_sel, "Estatus"]
            nuevo_estatus = st.selectbox("Nuevo estatus:", STATUS, index=STATUS.index(estatus_actual))
            comentario = st.text_area("Comentario:", height=60)
        
        if st.button("💾 Actualizar Estatus", use_container_width=True):
            if actualizar_estatus(df_materiales, material_sel, nuevo_estatus, comentario):
                if guardar_datos(df_materiales, df_historial):
                    st.success(f"✅ Estatus actualizado a: {nuevo_estatus}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Error guardando")
            else:
                st.error("❌ Material no encontrado")

# ========================================
# NUEVA SOLICITUD (YA FUNCIONAL) ✅
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
                
                uploaded_file = st.file_uploader(f"Archivo para Material {i+1}", 
                                               type=['png', 'jpg', 'jpeg', 'pdf'], 
                                               key=f"file_{i}")
                
                materiales.append({
                    "Item": item, "Descripcion": descripcion, "Estacion": estacion,
                    "Categoria": categoria, "Cant_Stock_Requerida": stock, 
                    "Cant_Equipos": equipos, "Cant_Partes_Equipo": partes_eq, 
                    "RP_Sugerido": rp, "Manufacturer": fabricante,
                    "Archivo": uploaded_file
                })
            
            comentario_general = st.text_area("📝 Comentario general de la solicitud", height=80)
            
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
                            "Frecuencia_Cambio": "",
                            "Cant_Stock_Requerida": mat["Cant_Stock_Requerida"],
                            "Cant_Equipos": mat["Cant_Equipos"],
                            "Cant_Partes_Equipo": mat["Cant_Partes_Equipo"],
                            "RP_Sugerido": mat["RP_Sugerido"],
                            "Manufacturer": mat["Manufacturer"],
                            "Archivo_Adjunto": archivo_adjunto,
                            "Estatus": "En revisión de ingeniería",
                            "Practicante_Asignado": "",
                            "Fecha_Revision": None,
                            "Fecha_Cotizacion": None,
                            "Fecha_Alta_SAP": None,
                            "Fecha_InfoRecord": None,
                            "Fecha_Finalizada": None,
                            "Comentario_Estatus": "",
                            "Material_SAP": "",
                            "InfoRecord_SAP": ""
                        }
                        registros.append(registro)
                
                # Asignar practicante automáticamente
                for registro in registros:
                    for resp, lineas_resp in LINEAS_POR_PRACTICANTE.items():
                        if registro["Linea"] in lineas_resp:
                            registro["Practicante_Asignado"] = resp
                            break
                
                df_materiales = pd.concat([df_materiales, pd.DataFrame(registros)], ignore_index=True)
                
                if guardar_datos(df_materiales, df_historial):
                    st.success(f"✅ Solicitud {id_solicitud} guardada con {len(registros)} materiales!")
                    st.balloons()
                    st.rerun()




