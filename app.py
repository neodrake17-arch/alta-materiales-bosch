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
        except Exception as e:
            st.error(f"Error guardando archivo: {e}")
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

def procesar_excel_masivo(uploaded_file):
    """Procesa Excel masivo de ingenieros"""
    try:
        df_excel = pd.read_excel(uploaded_file)
        columnas_requeridas = ["Item", "Descripcion", "Estacion", "Categoria", 
                              "Cant_Stock_Requerida", "Cant_Equipos", 
                              "Cant_Partes_Equipo", "RP_Sugerido", "Manufacturer"]
        
        # Validar columnas mínimas
        cols_presentes = [col for col in columnas_requeridas if col in df_excel.columns]
        if len(cols_presentes) < 3:
            return None, "❌ Faltan columnas obligatorias: Descripcion es requerida"
        
        # Limpiar y validar datos
        df_excel = df_excel.dropna(subset=["Descripcion"])
        df_excel["Categoria"] = df_excel["Categoria"].fillna("MAZE")
        df_excel["Cant_Stock_Requerida"] = pd.to_numeric(df_excel["Cant_Stock_Requerida"], errors='coerce').fillna(0)
        df_excel["Cant_Equipos"] = pd.to_numeric(df_excel["Cant_Equipos"], errors='coerce').fillna(0)
        df_excel["Cant_Partes_Equipo"] = pd.to_numeric(df_excel["Cant_Partes_Equipo"], errors='coerce').fillna(0)
        
        return df_excel, f"✅ {len(df_excel)} materiales procesados correctamente"
    except Exception as e:
        return None, f"❌ Error procesando Excel: {str(e)}"

# ✅ INICIALIZAR BASE DE DATOS CON TODAS LAS COLUMNAS
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
    st.success("✅ Base de datos inicializada correctamente")

# ========================================
# SESSION STATE
# ========================================
if "logged" not in st.session_state:
    st.session_state.logged = False

# ========================================
# LOGIN
# ========================================
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
            st.success("✅ ¡Bienvenido!")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    
    st.markdown("</div></div></div>", unsafe_allow_html=True)
    st.stop()

# ========================================
# HEADER Y SIDEBAR
# ========================================
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

# Sidebar
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
        opcion = st.radio("Navegar:", ["Mis pendientes", "Seguimiento completo", "Actualizar estatus", "Nueva solicitud"])
    elif st.session_state.rol == "jefa":
        st.metric("📊 Total pendientes sistema", pendientes_usuario)
        opcion = st.radio("Navegar:", ["Dashboard", "Seguimiento", "Nueva solicitud"])
    else:
        opcion = st.radio("Navegar:", ["Nueva solicitud", "Mis solicitudes"])

# ========================================
# NUEVA SOLICITUD - FORMULARIO MEJORADO ✅
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
                
                st.markdown(f"<div class='file-zone'><h4>📎 **Adjuntar imagen o PDF** *(opcional)*</h4><small>JPG, PNG, PDF hasta 5MB</small></div>", unsafe_allow_html=True)
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
                                "




