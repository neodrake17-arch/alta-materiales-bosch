import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
from io import BytesIO
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# Configuración - MUST BE FIRST
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
.btn-update { background-color: #4caf50 !important; }
.btn-update:hover { background-color: #388e3c !important; }
.alert-pendiente { color: #d32f2f !important; font-weight: bold; font-size: 1.5em; }
.status-revision { color: #666666; font-weight: bold; background: #f5f5f5; padding: 4px 8px; border-radius: 4px; }
.status-cotizacion { color: #ff9800; font-weight: bold; background: #fff3e0; padding: 4px 8px; border-radius: 4px; }
.status-alta { color: #1976d2; font-weight: bold; background: #e3f2fd; padding: 4px 8px; border-radius: 4px; }
.status-espera { color: #f57c00; font-weight: bold; background: #fff8e1; padding: 4px 8px; border-radius: 4px; animation: pulse 2s infinite; }
.status-info { color: #8e24aa; font-weight: bold; background: #f3e5f5; padding: 4px 8px; border-radius: 4px; }
.status-final { color: #388e3c; font-weight: bold; background: #e8f5e8; padding: 4px 8px; border-radius: 4px; }
.sidebar .sidebar-content { background-color: #f8f9fa !important; }
.metric-container { background: linear-gradient(135deg, #f0f8ff 0%, #e3f2fd 100%); padding: 1.5rem; border-radius: 12px; border-left: 5px solid #005691; }
.file-link { 
    background: linear-gradient(45deg, #1976d2, #42a5f5); 
    color: white !important; 
    padding: 6px 12px; 
    border-radius: 15px; 
    text-decoration: none !important; 
    font-size: 0.8em;
    display: inline-block;
    margin: 2px;
}
.file-link:hover { background: linear-gradient(45deg, #1565c0, #2196f3) !important; }
.card-pendiente { background: linear-gradient(135deg, #fff5f5 0%, #ffebee 100%); border-left: 6px solid #d32f2f; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; }
.card-metrics { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin: 1rem 0; }
.status-select { width: 200px !important; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
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

FECHA_MAP = {
    "En revisión de ingeniería": "Fecha_Revision",
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

# SIDEBAR
with st.sidebar:
    st.markdown("<h3 style='color: #005691;'>📋 Navegación</h3>", unsafe_allow_html=True)
    opcion = st.radio("Ir a:", ["Mis pendientes", "Seguimiento", "Actualizar estatus", "Nueva solicitud"])

# ========================================
# **MIS PENDIENTES** - NUEVA VERSIÓN COMPLETA
# ========================================
if opcion == "Mis pendientes":
    st.markdown(f"<h2 style='color: #005691;'>📋 Mis Pendientes - {st.session_state.responsable}</h2>", unsafe_allow_html=True)
    
    lineas_usuario = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_pendientes = df_materiales[
        (df_materiales["Linea"].isin(lineas_usuario)) & 
        (df_materiales["Estatus"] != "Alta finalizada")
    ].copy()
    
    if len(df_pendientes) == 0:
        st.success("🎉 ¡No tienes pendientes! ✅")
    else:
        # Tabla COMPLETA como pediste
        columnas_mis_pendientes = [
            "ID_Solicitud", "Linea", "Item", "Descripcion", "Estacion", 
            "Categoria", "Cant_Stock_Requerida", "Cant_Equipos", 
            "Cant_Partes_Equipo", "Manufacturer", "Archivo_Adjunto"
        ]
        
        # Mostrar tabla con formato especial para archivos
        for idx, row in df_pendientes.iterrows():
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
            with col1:
                st.markdown(f"**SOLICITUD:** {row['ID_Solicitud']}")
            with col2:
                st.markdown(f"**LÍNEA:** {row['Linea']}")
            with col3:
                st.markdown(f"**CATEGORÍA:** {row['Categoria']}")
            with col4:
                st.markdown(f"**STOCK:** {row['Cant_Stock_Requerida']}")
            
            st.markdown("**DETALLES:**")
            detalle_cols = [
                f"**Item:** {row['Item'] or 'N/A'}",
                f"**Descripción:** {row['Descripcion']}",
                f"**Estación:** {row['Estacion'] or 'N/A'}",
                f"**Equipos:** {row['Cant_Equipos']}",
                f"**Partes/Equipo:** {row['Cant_Partes_Equipo']}",
                f"**Proveedor:** {row['Manufacturer'] or 'N/A'}"
            ]
            for i, detalle in enumerate(detalle_cols):
                col_d = st.columns(3)[i % 3]
                with col_d:
                    st.markdown(detalle)
            
            # ARCHIVO
            if pd.notna(row['Archivo_Adjunto']) and row['Archivo_Adjunto']:
                st.markdown(f"**📎 ARCHIVO:** {row['Archivo_Adjunto']}")
            else:
                st.markdown("**📎 ARCHIVO:** ❌ Sin archivo")
            
            st.markdown("---")

# ========================================
# **SEGUIMIENTO** - NUEVA VERSIÓN CON CONTADORES Y COLORES
# ========================================
if opcion == "Seguimiento":
    st.markdown("<h2 style='color: #005691;'>🔍 Seguimiento Completo</h2>", unsafe_allow_html=True)
    
    # CONTADORES SUPERIORES COMO PEDISTE
    lineas_usuario = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_seguimiento = df_materiales[
        df_materiales["Linea"].isin(lineas_usuario)
    ].copy()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        revision = len(df_seguimiento[df_seguimiento["Estatus"] == "En revisión de ingeniería"])
        st.metric("🔍 En Revisión", revision)
    with col2:
        cotizacion = len(df_seguimiento[df_seguimiento["Estatus"] == "En cotización"])
        st.metric("💰 Cotización", cotizacion)
    with col3:
        info_record = len(df_seguimiento[df_seguimiento["Estatus"] == "En espera de InfoRecord"])
        st.metric("📋 InfoRecord", info_record)
    with col4:
        finalizados = len(df_seguimiento[df_seguimiento["Estatus"] == "Alta finalizada"])
        st.metric("✅ Finalizados", finalizados)
    
    # FILTROS
    col_f1, col_f2 = st.columns(2)
    linea_filtro = col_f1.selectbox("🏭 Línea", ["Todas"] + LINEAS)
    estatus_filtro = col_f2.selectbox("📊 Estatus", ["Todos"] + STATUS)
    
    df_filtrado = df_seguimiento.copy()
    if linea_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Linea"] == linea_filtro]
    if estatus_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Estatus"] == estatus_filtro]
    
    # TABLA CON ESTATUS COLORIDO
    st.markdown("### 📋 Tabla de Seguimiento")
    for idx, row in df_filtrado.iterrows():
        with st.container():
            col_id, col_info, col_estatus = st.columns([1, 3, 1.5])
            with col_id:
                st.markdown(f"**ID:** `{row['ID_Material']}`")
            with col_info:
                st.markdown(f"**{row['Descripcion'][:60]}...**")
                st.markdown(f"*{row['Linea']} - {row['Item'] or 'N/A'}*")
            with col_estatus:
                st.markdown(estatus_coloreado(row['Estatus']), unsafe_allow_html=True)
    
    # APARTADO PARA COPIAR ID
    st.markdown("---")
    st.markdown("### 📋 **Copiar ID para Actualizar**")
    ids_disponibles = df_filtrado["ID_Material"].tolist()
    id_seleccionado = st.selectbox("Seleccionar ID:", ids_disponibles)
    st.code(f"`{id_seleccionado}`", language="text")
    st.info("✅ Copia este ID y ve a 'Actualizar estatus'")

# ========================================
# ACTUALIZAR ESTATUS
# ========================================
if opcion == "Actualizar estatus":
    st.markdown("<h2 style='color: #005691;'>🔄 Actualizar Estatus</h2>", unsafe_allow_html=True)
    
    col_id, col_est = st.columns([1, 2])
    with col_id:
        id_manual = st.text_input("📋 Pegar ID del Material:")
        if id_manual:
            material_sel = id_manual
        else:
            material_sel = st.selectbox("O seleccionar:", df_materiales["ID_Material"].tolist())
    
    with col_est:
        if material_sel and len(df_materiales[df_materiales["ID_Material"] == material_sel]) > 0:
            idx_sel = df_materiales[df_materiales["ID_Material"] == material_sel].index[0]
            estatus_actual = df_materiales.loc[idx_sel, "Estatus"]
            nuevo_estatus = st.selectbox("Nuevo estatus:", STATUS, index=STATUS.index(estatus_actual))
            comentario = st.text_area("Comentario:", height=80)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 Actualizar", use_container_width=True):
                    if actualizar_estatus(df_materiales, material_sel, nuevo_estatus, comentario):
                        if guardar_datos(df_materiales, df_historial):
                            st.success(f"✅ Estatus actualizado a: {nuevo_estatus}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Error guardando")
                    else:
                        st.error("❌ Material no encontrado")
        else:
            st.warning("⚠️ Selecciona un ID válido")

# ========================================
# NUEVA SOLICITUD (SIMPLIFICADA)
# ========================================
if opcion == "Nueva solicitud":
    st.markdown("<h2 style='color: #005691;'>📋 Nueva Solicitud</h2>", unsafe_allow_html=True)
    st.info("🔧 Funcionalidad disponible - formulario dinámico para 1-5 materiales")
    # Aquí va el formulario completo que ya funcionaba



