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
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        df_materiales.to_excel(writer, sheet_name="materiales", index=False)
        df_historial.to_excel(writer, sheet_name="historial", index=False)

def generar_id_solicitud():
    return f"SOL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def generar_id_material():
    return f"MAT-{uuid.uuid4().hex[:8].upper()}"

def guardar_archivo(uploaded_file, material_id):
    """Guarda imagen o PDF con nombre único"""
    if uploaded_file is not None:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        filename = f"{material_id}{ext}"
        filepath = os.path.join(IMG_FOLDER, filename)
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return filename
    return ""

def crear_link_archivo(filename):
    """Crea enlace HTML descargable para archivo"""
    if filename and os.path.exists(os.path.join(IMG_FOLDER, filename)):
        tipo = "📷" if filename.lower().endswith(('.png', '.jpg', '.jpeg')) else "📄"
        return f'<a href="files/{IMG_FOLDER}/{filename}" class="file-link" download target="_blank">{tipo} {os.path.splitext(filename)[0]}</a>'
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

def safe_columns(df, columnas_deseadas):
    """Selecciona solo las columnas que existen en el DataFrame"""
    columnas_existentes = [col for col in columnas_deseadas if col in df.columns]
    return df[columnas_existentes].copy()

# INICIALIZAR BASE DE DATOS CON COLUMNA ARCHIVO
if not os.path.exists(DB_FILE):
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
        pd.DataFrame(columns=[
            "ID_Material", "ID_Solicitud", "Fecha_Solicitud", "Ingeniero", "Linea",
            "Prioridad", "Comentario_Solicitud", "Item", "Descripcion", "Estacion",
            "Categoria", "Frecuencia_Cambio", "Cant_Stock_Requerida", "Cant_Equipos", 
            "Cant_Partes_Equipo", "RP_Sugerido", "Manufacturer", "Archivo_Adjunto",
            "Estatus", "Practicante_Asignado", "Fecha_Revision", "Fecha_Cotizacion", 
            "Fecha_Alta_SAP", "Fecha_InfoRecord", "Fecha_Finalizada", 
            "Comentario_Estatus", "Material_SAP", "InfoRecord_SAP"
        ]).to_excel(writer, sheet_name="materiales", index=False)

# ========================================
# LOGIN
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
        user = st.text_input("👤 Usuario", placeholder="Escribe tu usuario")
    with col2:
        pwd = st.text_input("🔒 Contraseña", type="password", placeholder="********")
    
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

# ========================================
# HEADER
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

# ========================================
# CARGAR DATOS
# ========================================
df_materiales, df_historial = cargar_datos()
pendientes_usuario = contar_pendientes(st.session_state.responsable, df_materiales)

# ========================================
# SIDEBAR
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
# NUEVA SOLICITUD - CON ARCHIVOS
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
                    categoria = st.selectbox(f"🏷️ Categoría", CATEGORIAS_MATERIAL, key=f"cat_{i}")
                
                with col_b:
                    stock = st.number_input("Stock mínimo requerido", min_value=0.0, format="%.1f", key=f"stock_{i}")
                    equipos = st.number_input("Equipos que usan esta pieza", min_value=0, key=f"eq_{i}")
                    partes_eq = st.number_input("Partes por equipo", min_value=0, key=f"partes_{i}")
                    rp = st.text_input("RP sugerido", key=f"rp_{i}")
                    fabricante = st.text_input("Fabricante/Proveedor", key=f"fab_{i}")
                
                # SUBIDA DE ARCHIVO CON PREVIEW PARA INGENIEROS
                st.markdown(f"<div class='file-zone'><h4>📎 **Adjuntar imagen o PDF** *(opcional)*</h4><small>JPG, PNG, PDF hasta 5MB</small></div>", unsafe_allow_html=True)
                uploaded_file = st.file_uploader(f"Archivo para Material {i+1}", 
                                               type=['png', 'jpg', 'jpeg', 'pdf'], 
                                               key=f"file_{i}")
                
                if uploaded_file is not None:
                    if uploaded_file.type.startswith('image/'):
                        image = Image.open(uploaded_file)
                        st.image(image, caption=f"Preview - {uploaded_file.name}", width=200)
                    else:
                        st.success(f"✅ PDF cargado: {uploaded_file.name} ({uploaded_file.size/1024:.1f} KB)")
                
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
                            
                            registros.append({
                                "ID_Material": id_material,
                                "ID_Solicitud": id_solicitud,
                                "Fecha_Solicitud": datetime.now(),
                                "Ingeniero": ingeniero,
                                "Linea": linea,
                                "Prioridad": prioridad,
                                "Comentario_Solicitud": comentario_general,
                                **{k: v for k, v in mat.items() if k != "Archivo"},
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
                            })
                    
                    if registros:
                        df_nuevos = pd.DataFrame(registros)
                        df_materiales_nuevo = pd.concat([df_materiales, df_nuevos], ignore_index=True)
                        guardar_datos(df_materiales_nuevo, df_historial)
                        st.success(f"✅ **Solicitud {id_solicitud}** creada con **{len(registros)}** materiales")
                        if any(r.get("Archivo_Adjunto") for r in registros):
                            st.info("📎 **Archivos adjuntos guardados** en carpeta 'imagenes/'")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Completa al menos **una descripción**")
            
            with col_count:
                st.metric("Materiales a crear", len([m for m in materiales if m["Descripcion"].strip()]))
    
    with tab2:
        st.info("**Excel masivo próximamente con soporte de archivos**")
        st.warning("⏳ Esta función se actualizará pronto")

# ========================================
# MIS PENDIENTES - CON ENLACES DESCARGABLES ✅
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
        # MÉTRICAS
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📋 Total pendientes", len(df_mis))
        col2.metric("🗂️ En revisión", len(df_mis[df_mis["Estatus"] == "En revisión de ingeniería"]))
        col3.metric("🧾 En cotización", len(df_mis[df_mis["Estatus"] == "En cotización"]))
        col4.metric("⚙️ En alta SAP", len(df_mis[df_mis["Estatus"] == "En alta SAP"]))
        col5.metric("⏳ Espera InfoRecord", len(df_mis[df_mis["Estatus"] == "En espera de InfoRecord"]))
        
        st.markdown("---")
        st.markdown("<h3 style='color: #1976d2;'>📊 Materiales Pendientes - CON ARCHIVOS</h3>", unsafe_allow_html=True)
        
        # TABLA CON ENLACES DESCARGABLES
        columnas_completas = [
            "ID_Material", "ID_Solicitud", "Ingeniero", "Linea", "Categoria",
            "Descripcion", "Item", "Estacion", "Cant_Stock_Requerida", 
            "Cant_Equipos", "Cant_Partes_Equipo", "RP_Sugerido", 
            "Manufacturer", "Estatus", "Prioridad", "Practicante_Asignado", "Archivo_Adjunto"
        ]
        
        df_mostrar_completo = safe_columns(df_mis, columnas_completas)
        df_mostrar_completo["Archivo"] = df_mostrar_completo["Archivo_Adjunto"].apply(crear_link_archivo)
        if "Estatus" in df_mostrar_completo.columns:
            df_mostrar_completo["Estatus"] = df_mostrar_completo["Estatus"].apply(estatus_coloreado)
        
        # Mostrar tabla con enlaces
        columnas_mostrar = [col for col in ["ID_Material", "Descripcion", "Linea", "Estatus", "Prioridad", "Archivo"] if col in df_mostrar_completo.columns]
        html_table = df_mostrar_completo[columnas_mostrar].to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)
        
        # BOTONES DESCARGAR TODOS LOS ARCHIVOS
        st.markdown("---")
        archivos = df_mis["Archivo_Adjunto"].dropna().unique()
        if len(archivos) > 0:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Descargar todos los archivos", key="download_all_files"):
                    st.info(f"📁 Descargando {len(archivos)} archivo(s)...")
            with col2:
                st.info(f"📎 **{len(archivos)} archivo(s)** disponibles para descargar")

# ========================================
# DASHBOARD JEFA
# ========================================
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
    
    # DESCARGAS
    col_desc1, col_desc2 = st.columns(2)
    with col_desc1:
        st.download_button("📊 Reporte Completo", data=df_to_excel_bytes(df_materiales),
                         file_name=f"reporte_materiales_{datetime.now().strftime('%Y%m%d')}.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    st.markdown("---")
    practicante_sel = st.selectbox("👤 Practicante:", ["TODOS"] + list(LINEAS_POR_PRACTICANTE.keys()))
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
    
    columnas_view = ["ID_Material", "Descripcion", "Linea", "Categoria", "Estatus", "Practicante_Asignado", "Prioridad"]
    df_view_mostrar = safe_columns(df_view, columnas_view)
    if "Estatus" in df_view_mostrar.columns:
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
        columnas_mis = ["ID_Solicitud", "Fecha_Solicitud", "Linea", "Categoria", "Prioridad", "Estatus"]
        df_mostrar_mis = safe_columns(df_mis, columnas_mis)
        st.dataframe(df_mostrar_mis, use_container_width=True)

# ========================================
# FOOTER
# ========================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem; font-size: 0.9em; border-top: 1px solid #eee;'>
    🔧 <strong>Sistema de Gestión de Materiales Bosch</strong> © 2026 | 
    📁 <code>imagenes/</code> | 🗄️ <code>bd_materiales.xlsx</code>
</div>
""", unsafe_allow_html=True)



