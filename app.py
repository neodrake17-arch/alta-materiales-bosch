import streamlit as st
import pandas as pd
from datetime import datetime
import os
import uuid
from io import BytesIO
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
                        else:
                            st.error("❌ Error al guardar en la base de datos")
                    else:
                        st.error("❌ Completa al menos **una descripción**")
            
            with col_count:
                st.metric("Materiales a crear", len([m for m in materiales if m["Descripcion"].strip()]))
    
    with tab2:
        st.info("**📊 Sube tu Excel masivo con +50 materiales**")
        st.markdown("""
        **Formato Excel requerido:**
        - Descripcion (obligatorio)
        - Item, Estacion, Categoria (MAZE/FHMI/HIBE)
        - Cant_Stock_Requerida, Cant_Equipos, Cant_Partes_Equipo
        - RP_Sugerido, Manufacturer
        """)
        
        uploaded_excel = st.file_uploader("📁 Subir Excel masivo", type="xlsx")
        if uploaded_excel is not None:
            df_procesado, mensaje = procesar_excel_masivo(uploaded_excel)
            st.info(mensaje)
            
            if df_procesado is not None:
                st.dataframe(df_procesado.head())
                
                if st.button("💾 Crear solicitud masiva", type="primary"):
                    registros = []
                    id_solicitud = generar_id_solicitud()
                    
                    for idx, row in df_procesado.iterrows():
                        id_material = generar_id_material()
                        registro = {
                            "ID_Material": id_material,
                            "ID_Solicitud": id_solicitud,
                            "Fecha_Solicitud": datetime.now(),
                            "Ingeniero": ingeniero,
                            "Linea": linea,
                            "Prioridad": prioridad,
                            "Comentario_Solicitud": "Solicitud masiva via Excel",
                            "Item": row.get("Item", ""),
                            "Descripcion": row["Descripcion"],
                            "Estacion": row.get("Estacion", ""),
                            "Categoria": row["Categoria"],
                            "Cant_Stock_Requerida": row["Cant_Stock_Requerida"],
                            "Cant_Equipos": row["Cant_Equipos"],
                            "Cant_Partes_Equipo": row["Cant_Partes_Equipo"],
                            "RP_Sugerido": row.get("RP_Sugerido", ""),
                            "Manufacturer": row.get("Manufacturer", ""),
                            "Archivo_Adjunto": "",
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
                    
                    df_nuevos = pd.DataFrame(registros)
                    df_materiales_nuevo = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                    if guardar_datos(df_materiales_nuevo, df_historial):
                        st.success(f"✅ **Solicitud masiva {id_solicitud}** con **{len(registros)}** materiales creada")
                        st.balloons()
                        st.rerun()

# ========================================
# MIS PENDIENTES ✅ TABLA COMPLETA CON TODOS LOS DATOS
# ========================================
elif opcion == "Mis pendientes":
    st.markdown(f"<h2 style='color: #005691;'>📋 Materiales Pendientes - {st.session_state.responsable}</h2>", unsafe_allow_html=True)
    
    mis_lineas = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_mis = df_materiales[
        (df_materiales["Linea"].isin(mis_lineas)) & 
        (df_materiales["Estatus"] != "Alta finalizada")
    ].copy()
    
    if df_mis.empty:
        st.markdown("## 🎉 ¡Felicidades!")
        st.success("**No tienes materiales pendientes.** ✅")
    else:
        # MÉTRICAS
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📋 Total pendientes", len(df_mis))
        col2.metric("🗂️ En revisión", len(df_mis[df_mis["Estatus"] == "En revisión de ingeniería"]))
        col3.metric("🧾 En cotización", len(df_mis[df_mis["Estatus"] == "En cotización"]))
        col4.metric("⚙️ En alta SAP", len(df_mis[df_mis["Estatus"] == "En alta SAP"]))
        col5.metric("⏳ Espera InfoRecord", len(df_mis[df_mis["Estatus"] == "En espera de InfoRecord"]))
        
        st.markdown("---")
        
        # ✅ TABLA COMPLETA CON TODOS LOS DATOS DE INGENIEROS
        columnas_completas = [
            "ID_Material", "ID_Solicitud", "Ingeniero", "Linea", "Prioridad",
            "Item", "Descripcion", "Estacion", "Categoria", 
            "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo", 
            "RP_Sugerido", "Manufacturer", "Archivo_Adjunto", "Estatus"
        ]
        
        df_mostrar = safe_columns(df_mis, columnas_completas)
        df_mostrar["Archivo"] = df_mostrar["Archivo_Adjunto"].apply(crear_link_archivo)
        
        if "Estatus" in df_mostrar.columns:
            df_mostrar["Estatus"] = df_mostrar["Estatus"].apply(estatus_coloreado)
        
        # Mostrar TODAS las columnas importantes
        columnas_mostrar = ["ID_Material", "Ingeniero", "Linea", "Prioridad", "Item", 
                           "Descripcion", "Estacion", "Categoria", "Cant_Stock_Requerida",
                           "RP_Sugerido", "Manufacturer", "Estatus", "Archivo"]
        columnas_finales = [col for col in columnas_mostrar if col in df_mostrar.columns]
        
        html_table = df_mostrar[columnas_finales].to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)

# ========================================
# ACTUALIZAR ESTATUS ✅ NUEVA FUNCIONALIDAD
# ========================================
elif opcion == "Actualizar estatus":
    st.markdown("<h2 style='color: #005691;'>🔄 Actualizar Estatus de Materiales</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        filtro_linea = st.selectbox("🏭 Filtrar por línea:", ["Mis líneas"] + LINEAS)
    with col2:
        filtro_estatus = st.selectbox("📋 Mostrar solo:", ["Todos"] + STATUS)
    
    if filtro_linea == "Mis líneas":
        lineas_filtro = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
        df_edit = df_materiales[df_materiales["Linea"].isin(lineas_filtro)].copy()
    else:
        df_edit = df_materiales[df_materiales["Linea"] == filtro_linea].copy()
    
    if filtro_estatus != "Todos":
        df_edit = df_edit[df_edit["Estatus"] == filtro_estatus].copy()
    
    if df_edit.empty:
        st.warning("No hay materiales para mostrar")
    else:
        st.markdown("**Selecciona materiales y actualiza su estatus:**")
        
        for idx, row in df_edit.iterrows():
            with st.expander(f"🔧 {row['ID_Material']} - {row['Descripcion'][:50]}... | {row['Linea']} | {row['Estatus']}"):
                col1, col2, col3 = st.columns([1, 2, 2])
                
                with col1:
                    nuevo_estatus = st.selectbox(
                        "Nuevo estatus:", STATUS, 
                        index=STATUS.index(row["Estatus"]) if row["Estatus"] in STATUS else 0,
                        key=f"status_{row['ID_Material']}",
                        help="Cambiará el color automáticamente"
                    )
                
                with col2:
                    comentario = st.text_input(
                        "Comentario:", 
                        value=row.get("Comentario_Estatus", ""),
                        key=f"comment_{row['ID_Material']}"
                    )
                
                with col3:
                    if st.button(f"✅ Actualizar {row['ID_Material']}", key=f"update_{row['ID_Material']}"):
                        # Actualizar registro
                        mask = df_materiales["ID_Material"] == row["ID_Material"]
                        df_materiales.loc[mask, "Estatus"] = nuevo_estatus
                        
                        if nuevo_estatus != row["Estatus"]:
                            fecha_col = FECHA_MAP.get(nuevo_estatus)
                            if fecha_col:
                                df_materiales.loc[mask, fecha_col] = datetime.now()
                        
                        df_materiales.loc[mask, "Comentario_Estatus"] = comentario
                        df_materiales.loc[mask, "Practicante_Asignado"] = st.session_state.responsable
                        
                        if guardar_datos(df_materiales, df_historial):
                            st.success(f"✅ {row['ID_Material']} actualizado a **{nuevo_estatus}**")
                            st.rerun()
                        else:
                            st.error("❌ Error guardando cambios")

# ========================================
# DASHBOARD JEFA ✅ CON GRÁFICOS COMPLETOS
# ========================================
elif opcion == "Dashboard":
    st.markdown("<h2 style='color: #005691;'>📈 Dashboard Ejecutivo</h2>", unsafe_allow_html=True)
    
    # MÉTRICAS PRINCIPALES
    col1, col2, col3, col4 = st.columns(4)
    total_materiales = len(df_materiales)
    pendientes_total = len(df_materiales[df_materiales["Estatus"] != "Alta finalizada"])
    finalizados = len(df_materiales[df_materiales["Estatus"] == "Alta finalizada"])
    
    col1.metric("📦 Total materiales", total_materiales)
    col2.metric("⏳ Pendientes", pendientes_total)
    col3.metric("✅ Finalizados", finalizados)
    col4.metric("📊 % Completado", f"{finalizados/total_materiales*100:.1f}%" if total_materiales > 0 else "0%")
    
    st.markdown("---")
    
    # GRÁFICO 1: ESTATUS DE MATERIALES
    st.subheader("📊 Distribución por Estatus")
    df_estatus = df_materiales["Estatus"].value_counts().reset_index()
    df_estatus.columns = ["Estatus", "Cantidad"]
    
    fig_pie = px.pie(df_estatus, values="Cantidad", names="Estatus", 
                     color_discrete_sequence=["#666666", "#ff9800", "#1976d2", "#f57c00", "#8e24aa", "#388e3c"],
                     title="Estatus Actual de Materiales")
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(height=400)
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # GRÁFICO 2: POR PRACTICANTE
    st.subheader("👥 Materiales por Practicante")
    df_pract = df_materiales.groupby("Practicante_Asignado")["Practicante_Asignado"].count().reset_index(name="Cantidad")
    df_pract["Practicante_Asignado"] = df_pract["Practicante_Asignado"].fillna("Sin asignar")
    
    fig_bar = px.bar(df_pract, x="Practicante_Asignado", y="Cantidad", 
                     title="Distribución de Materiales por Practicante",
                     color="Cantidad", color_continuous_scale="Viridis")
    fig_bar.update_layout(height=400)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # GRÁFICO 3: AVANCE POR LÍNEA
    st.subheader("🏭 Avance por Línea de Producción")
    avance_linea = df_materiales.groupby("Linea").agg({
        "Estatus": lambda x: ("Alta finalizada" in x.values).sum()
    }).rename(columns={"Estatus": "Finalizados"})
    avance_linea["Total"] = df_materiales["Linea"].value_counts()
    avance_linea["Porcentaje"] = (avance_linea["Finalizados"] / avance_linea["Total"] * 100).round(1)
    
    fig_linea = px.bar(avance_linea.reset_index(), x="Linea", y="Porcentaje",
                       title="Avance % por Línea",
                       color="Porcentaje", color_continuous_scale="RdYlGn")
    fig_linea.update_layout(height=400)
    st.plotly_chart(fig_linea, use_container_width=True)
    
    # BOTONES DE DESCARGA
    col_desc1, col_desc2 = st.columns(2)
    with col_desc1:
        st.download_button("📊 Reporte Completo", 
                          data=df_to_excel_bytes(df_materiales),
                          file_name=f"reporte_materiales_{datetime.now().strftime('%Y%m%d')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    practicante_sel = st.selectbox("👤 Ver detalle por practicante:", ["TODOS"] + list(LINEAS_POR_PRACTICANTE.keys()))
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
    if filtro_linea != "Todas": 
        df_view = df_view[df_view["Linea"] == filtro_linea]
    if filtro_estatus != "Todos": 
        df_view = df_view[df_view["Estatus"] == filtro_estatus]
    if filtro_pract: 
        df_view = df_view[df_view["Practicante_Asignado"].str.contains(filtro_pract, case=False, na=False)]
    
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
    ✅ <strong>Dashboard + Estatus + Excel Masivo ACTIVOS</strong>
</div>
""", unsafe_allow_html=True)




