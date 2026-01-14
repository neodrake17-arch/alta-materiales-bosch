
 # app.py — Bosch Material Management (Enterprise-ready Streamlit)
# --------------------------------------------------------------
# ✅ Seguridad: bcrypt hashes + roles (prefer st.secrets)
# ✅ Persistencia: SQLite
# ✅ Auditoría: historial completo por cambio de estatus
# ✅ Archivos: versionado + descargas seguras
# ✅ Validaciones: campos obligatorios + reglas básicas
# ✅ UX: estilo Bosch, KPIs con iconos SVG (sin emojis)
# ✅ Tablas: colores por estatus dentro de la tabla (Pandas Styler)
# ✅ Seguimiento: Vista Tabla / Vista Kanban (cards + mover estatus)
# ✅ Dashboard jefa: KPIs + gráficas + exportables + snapshots semanales

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from pathlib import Path
import uuid
import bcrypt
from io import BytesIO
from typing import Dict, Optional

import plotly.express as px

# ---------------------------
# STREAMLIT CONFIG (MUST BE FIRST)
# ---------------------------
st.set_page_config(page_title="Bosch | Material Management", layout="wide")

# ---------------------------
# THEME / CSS (Bosch-like)
# ---------------------------
BOSCH_BLUE = "#005691"
BOSCH_DARK = "#003D6B"
BOSCH_LIGHT = "#EAF3FA"
BOSCH_GRAY = "#F6F7F9"
SUCCESS = "#2E7D32"
WARN = "#F57C00"
DANGER = "#C62828"
INFO = "#6A1B9A"

st.markdown(
    f"""
<style>
:root {{
  --bosch-blue: {BOSCH_BLUE};
  --bosch-dark: {BOSCH_DARK};
  --bosch-light: {BOSCH_LIGHT};
  --bosch-gray: {BOSCH_GRAY};
  --success: {SUCCESS};
  --warn: {WARN};
  --danger: {DANGER};
  --info: {INFO};
}}
h1, h2, h3, h4 {{ color: var(--bosch-blue); font-weight: 800; }}
h1 {{ font-size: 2.2rem; margin-bottom: .75rem; }}

.stButton>button {{
  background: linear-gradient(90deg, var(--bosch-blue), #1976d2) !important;
  color: white !important;
  border: 0 !important;
  border-radius: 10px !important;
  height: 42px !important;
  font-weight: 700 !important;
}}
.stButton>button:hover {{
  background: linear-gradient(90deg, var(--bosch-dark), var(--bosch-blue)) !important;
}}

section[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, var(--bosch-gray), #ffffff);
}}

.card {{
  background: white;
  border-radius: 16px;
  padding: 16px 16px;
  box-shadow: 0 8px 18px rgba(0,0,0,0.08);
  border: 1px solid rgba(0,86,145,0.10);
  margin-bottom: 10px;
}}
.card-title {{
  display:flex; align-items:center; gap:10px;
  font-weight:900; color: var(--bosch-blue); font-size: 1.02rem;
}}
.card-sub {{
  color: #4d4d4d; font-size: .9rem; margin-top: 4px;
}}
.smallhelp {{ color:#5c5c5c; font-size: .86rem; }}

.kpi {{
  background: linear-gradient(135deg, var(--bosch-light), #ffffff);
  border-radius: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(0,86,145,0.12);
  box-shadow: 0 6px 14px rgba(0,0,0,0.06);
  display:flex; justify-content:space-between; align-items:center;
}}
.kpi-left {{ display:flex; align-items:center; gap:10px; }}
.kpi .label {{ color:#3a3a3a; font-weight:800; font-size:.92rem; }}
.kpi .value {{ color: var(--bosch-blue); font-weight:900; font-size: 1.6rem; line-height:1.15; }}

.badge {{
  display:inline-block; padding: 6px 10px; border-radius: 999px; font-weight:900; font-size:.82rem;
}}
.badge-rev {{ background: rgba(0,0,0,0.06); color:#2E2E2E; }}
.badge-cot {{ background: rgba(46,125,50,0.14); color: var(--success); }}
.badge-sap {{ background: rgba(245,124,0,0.18); color: #E65100; }}
.badge-wait {{ background: rgba(245,124,0,0.12); color: var(--warn); }}
.badge-info {{ background: rgba(106,27,154,0.14); color: var(--info); }}
.badge-fin {{ background: rgba(13,71,161,0.14); color: #0D47A1; }}

.login-wrap {{
  background: linear-gradient(135deg, var(--bosch-gray) 0%, #ffffff 55%);
  border-radius: 22px; padding: 34px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.10);
  border: 1px solid rgba(0,86,145,0.10);
  max-width: 560px; margin: 18px auto;
}}
.login-title {{
  font-size: 2.1rem; font-weight: 900; color: var(--bosch-blue); margin: 0 0 8px 0;
}}

.icon {{ width: 18px; height: 18px; display:inline-block; }}
.icon-lg {{ width: 20px; height: 20px; display:inline-block; }}

.kanban-wrap {{
  display: flex;
  gap: 14px;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------
# SVG ICONS (no emojis)
# ---------------------------
def svg_icon(name: str, color: str = BOSCH_BLUE, size: int = 18) -> str:
    icons = {
        "user": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20 21a8 8 0 0 0-16 0"/>
  <circle cx="12" cy="7" r="4"/>
</svg>""",
        "logout": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
  <path d="M16 17l5-5-5-5"/>
  <path d="M21 12H9"/>
</svg>""",
        "pending": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 8v5l3 3"/>
  <circle cx="12" cy="12" r="10"/>
</svg>""",
        "dashboard": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 3h18v18H3z"/>
  <path d="M7 13h3v6H7z"/>
  <path d="M14 7h3v12h-3z"/>
</svg>""",
        "search": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="11" cy="11" r="7"/>
  <path d="M21 21l-4.3-4.3"/>
</svg>""",
        "update": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 12a9 9 0 1 1-2.6-6.4"/>
  <path d="M21 3v6h-6"/>
</svg>""",
        "plus": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 5v14"/>
  <path d="M5 12h14"/>
</svg>""",
        "download": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
  <path d="M7 10l5 5 5-5"/>
  <path d="M12 15V3"/>
</svg>""",
        "file": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
  <path d="M14 2v6h6"/>
</svg>""",
        "chart": f"""
<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 3v18h18"/>
  <path d="M7 14l3-3 4 4 6-7"/>
</svg>""",
    }
    s = icons.get(name, icons["file"])
    if size >= 20:
        s = s.replace('class="icon"', 'class="icon-lg"')
    return s

# ---------------------------
# CONSTANTS
# ---------------------------
APP_DIR = Path(__file__).parent if "__file__" in globals() else Path(".")
DB_PATH = APP_DIR / "bd_materiales.sqlite"
FILES_DIR = APP_DIR / "archivos_materiales"
FILES_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIAS_MATERIAL = ["MAZE", "FHMI", "HIBE"]

STATUS = [
    "En revisión de ingeniería",
    "En cotización",
    "En alta SAP",
    "En espera de InfoRecord",
    "Info record creado",
    "Alta finalizada",
]

STATUS_BADGE_CLASS = {
    "En revisión de ingeniería": "badge-rev",
    "En cotización": "badge-cot",
    "En alta SAP": "badge-sap",
    "En espera de InfoRecord": "badge-wait",
    "Info record creado": "badge-info",
    "Alta finalizada": "badge-fin",
}

FECHA_MAP = {
    "En revisión de ingeniería": "Fecha_Revision",
    "En cotización": "Fecha_Cotizacion",
    "En alta SAP": "Fecha_Alta_SAP",
    "En espera de InfoRecord": "Fecha_InfoRecord",
    "Info record creado": "Fecha_InfoRecord",
    "Alta finalizada": "Fecha_Finalizada",
}

LINEAS_POR_PRACTICANTE = {
    "Jarol": ["DP 02", "SCU 33", "SCU 34", "SCU 48", "SSL1"],
    "Lalo": ["APA 36", "APA 38", "SERVO 10", "SERVO 24"],
    "Jime": ["DP 32", "DP 35", "SENSOR 28", "SENSOR 5"],
    "Niko": ["KGT 22", "KGT 23", "LG 01", "LG 03"],
}
LINEAS = sorted(list(set(sum(LINEAS_POR_PRACTICANTE.values(), []))))

# ---------------------------
# STATUS COLORS (table styling)
# ---------------------------
STATUS_COLOR = {
    "En revisión de ingeniería": {"bg": "#E0E0E0", "fg": "#2E2E2E"},  # gris
    "En cotización": {"bg": "#C8E6C9", "fg": "#1B5E20"},             # verde
    "En alta SAP": {"bg": "#FFE0B2", "fg": "#E65100"},               # naranja
    "En espera de InfoRecord": {"bg": "#FFF9C4", "fg": "#F57C00"},   # ámbar
    "Info record creado": {"bg": "#E1BEE7", "fg": "#6A1B9A"},        # morado
    "Alta finalizada": {"bg": "#BBDEFB", "fg": "#0D47A1"},           # azul (confirmada)
}

def _style_status_cell(val: str) -> str:
    d = STATUS_COLOR.get(str(val), {"bg": "#EEEEEE", "fg": "#333333"})
    return f"background-color: {d['bg']}; color: {d['fg']}; font-weight: 900;"

def style_df_by_status(df: pd.DataFrame, status_col: str = "Estatus", highlight_row: bool = False):
    if df is None or df.empty or status_col not in df.columns:
        return df

    styler = df.style

    if highlight_row:
        def row_style(row):
            d = STATUS_COLOR.get(str(row[status_col]), {"bg": "#FFFFFF", "fg": "#000000"})
            return [f"background-color: {d['bg']}; color: {d['fg']}; font-weight: 650;" for _ in row]
        styler = styler.apply(row_style, axis=1)
    else:
        styler = styler.map(_style_status_cell, subset=[status_col])

    styler = styler.set_properties(**{
        "border": "1px solid rgba(0,0,0,0.06)",
        "font-size": "0.92rem"
    }).set_table_styles([
        {"selector": "th", "props": [("background-color", BOSCH_GRAY), ("color", BOSCH_BLUE), ("font-weight", "900")]},
        {"selector": "td", "props": [("padding", "10px 10px")]},
    ])
    return styler

# ---------------------------
# USERS / AUTH (prefer st.secrets)
# ---------------------------
def _bcrypt_hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def _bcrypt_check(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def load_users() -> Dict[str, Dict[str, str]]:
    try:
        if "users" in st.secrets:
            return dict(st.secrets["users"])  # type: ignore
    except Exception:
        pass

    # Demo fallback (move to secrets for production)
    return {
        "jarol": {"pwd_hash": _bcrypt_hash("jarol123"), "rol": "practicante", "responsable": "Jarol"},
        "lalo":  {"pwd_hash": _bcrypt_hash("lalo123"),  "rol": "practicante", "responsable": "Lalo"},
        "jime":  {"pwd_hash": _bcrypt_hash("jime123"),  "rol": "practicante", "responsable": "Jime"},
        "niko":  {"pwd_hash": _bcrypt_hash("niko123"),  "rol": "practicante", "responsable": "Niko"},
        "admin": {"pwd_hash": _bcrypt_hash("admin123"), "rol": "jefa",        "responsable": "Admin"},
    }

USERS = load_users()

# ---------------------------
# DB LAYER (SQLite)
# ---------------------------
def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS materiales (
            ID_Material TEXT PRIMARY KEY,
            ID_Solicitud TEXT,
            Fecha_Solicitud TEXT,
            Ingeniero TEXT,
            Linea TEXT,
            Prioridad TEXT,
            Comentario_Solicitud TEXT,
            Item TEXT,
            Descripcion TEXT,
            Estacion TEXT,
            Categoria TEXT,
            Frecuencia_Cambio TEXT,
            Cant_Stock_Requerida REAL,
            Cant_Equipos INTEGER,
            Cant_Partes_Equipo INTEGER,
            RP_Sugerido TEXT,
            Manufacturer TEXT,
            Estatus TEXT,
            Practicante_Asignado TEXT,
            Comentario_Estatus TEXT,
            Material_SAP TEXT,
            InfoRecord_SAP TEXT,
            Fecha_Revision TEXT,
            Fecha_Cotizacion TEXT,
            Fecha_Alta_SAP TEXT,
            Fecha_InfoRecord TEXT,
            Fecha_Finalizada TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS historial (
            ID_Evento TEXT PRIMARY KEY,
            ID_Material TEXT,
            Fecha_Evento TEXT,
            Usuario TEXT,
            Rol TEXT,
            Estatus_Anterior TEXT,
            Estatus_Nuevo TEXT,
            Comentario TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS archivos (
            ID_Archivo TEXT PRIMARY KEY,
            ID_Material TEXT,
            Version INTEGER,
            Nombre_Original TEXT,
            Nombre_Almacenado TEXT,
            Mime TEXT,
            Size_Bytes INTEGER,
            Fecha_Subida TEXT,
            Subido_Por TEXT
        )
        """
    )

    conn.commit()
    conn.close()

init_db()

# ---------------------------
# UTILS
# ---------------------------
def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def generar_id_solicitud() -> str:
    return f"SOL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def generar_id_material() -> str:
    return f"MAT-{uuid.uuid4().hex[:8].upper()}"

def iso_week(d: Optional[pd.Timestamp]) -> Optional[str]:
    if d is None or pd.isna(d):
        return None
    try:
        y, w, _ = d.isocalendar()
        return f"{y}-W{int(w):02d}"
    except Exception:
        return None

def badge_html(status: str) -> str:
    cls = STATUS_BADGE_CLASS.get(status, "badge-rev")
    return f'<span class="badge {cls}">{status}</span>'

def safe_to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")

def df_read_materiales() -> pd.DataFrame:
    conn = db()
    df = pd.read_sql_query("SELECT * FROM materiales", conn)
    conn.close()
    if len(df) == 0:
        return df
    for c in ["Fecha_Solicitud", "Fecha_Revision", "Fecha_Cotizacion", "Fecha_Alta_SAP", "Fecha_InfoRecord", "Fecha_Finalizada"]:
        if c in df.columns:
            df[c] = safe_to_datetime(df[c])
    return df

def df_read_historial(material_id: Optional[str] = None) -> pd.DataFrame:
    conn = db()
    if material_id:
        df = pd.read_sql_query(
            "SELECT * FROM historial WHERE ID_Material = ? ORDER BY Fecha_Evento DESC",
            conn,
            params=[material_id],
        )
    else:
        df = pd.read_sql_query("SELECT * FROM historial ORDER BY Fecha_Evento DESC", conn)
    conn.close()
    if len(df) and "Fecha_Evento" in df.columns:
        df["Fecha_Evento"] = safe_to_datetime(df["Fecha_Evento"])
    return df

def df_read_archivos(material_id: str) -> pd.DataFrame:
    conn = db()
    df = pd.read_sql_query(
        "SELECT * FROM archivos WHERE ID_Material = ? ORDER BY Version DESC",
        conn,
        params=[material_id],
    )
    conn.close()
    if len(df) and "Fecha_Subida" in df.columns:
        df["Fecha_Subida"] = safe_to_datetime(df["Fecha_Subida"])
    return df

def insert_materiales(registros: list[dict]) -> None:
    conn = db()
    cur = conn.cursor()
    for r in registros:
        cur.execute(
            """
            INSERT INTO materiales (
                ID_Material, ID_Solicitud, Fecha_Solicitud, Ingeniero, Linea, Prioridad, Comentario_Solicitud,
                Item, Descripcion, Estacion, Categoria, Frecuencia_Cambio, Cant_Stock_Requerida, Cant_Equipos,
                Cant_Partes_Equipo, RP_Sugerido, Manufacturer, Estatus, Practicante_Asignado,
                Comentario_Estatus, Material_SAP, InfoRecord_SAP,
                Fecha_Revision, Fecha_Cotizacion, Fecha_Alta_SAP, Fecha_InfoRecord, Fecha_Finalizada
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                r["ID_Material"], r["ID_Solicitud"], r["Fecha_Solicitud"], r["Ingeniero"], r["Linea"], r["Prioridad"],
                r.get("Comentario_Solicitud",""),
                r.get("Item",""), r["Descripcion"], r.get("Estacion",""), r.get("Categoria",""),
                r.get("Frecuencia_Cambio",""),
                float(r.get("Cant_Stock_Requerida", 0.0)),
                int(r.get("Cant_Equipos", 0)),
                int(r.get("Cant_Partes_Equipo", 0)),
                r.get("RP_Sugerido",""), r.get("Manufacturer",""),
                r.get("Estatus","En revisión de ingeniería"),
                r.get("Practicante_Asignado",""),
                r.get("Comentario_Estatus",""),
                r.get("Material_SAP",""),
                r.get("InfoRecord_SAP",""),
                r.get("Fecha_Revision"),
                r.get("Fecha_Cotizacion"),
                r.get("Fecha_Alta_SAP"),
                r.get("Fecha_InfoRecord"),
                r.get("Fecha_Finalizada"),
            ),
        )
    conn.commit()
    conn.close()

def write_historial_event(id_material: str, estatus_old: str, estatus_new: str, comentario: str, usuario: str, rol: str):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO historial (
            ID_Evento, ID_Material, Fecha_Evento, Usuario, Rol, Estatus_Anterior, Estatus_Nuevo, Comentario
        ) VALUES (?,?,?,?,?,?,?,?)
        """,
        (f"EVT-{uuid.uuid4().hex[:12].upper()}", id_material, now_iso(), usuario, rol, estatus_old, estatus_new, comentario),
    )
    conn.commit()
    conn.close()

def update_estatus_material(
    id_material: str,
    nuevo_estatus: str,
    comentario: str,
    usuario: str,
    rol: str,
    material_sap: Optional[str] = None,
    inforecord_sap: Optional[str] = None,
) -> bool:
    conn = db()
    cur = conn.cursor()
    row = cur.execute("SELECT Estatus FROM materiales WHERE ID_Material = ?", (id_material,)).fetchone()
    if not row:
        conn.close()
        return False

    estatus_old = row["Estatus"]

    fecha_col = FECHA_MAP.get(nuevo_estatus)
    fields = ["Estatus = ?", "Comentario_Estatus = ?"]
    params = [nuevo_estatus, comentario]

    if material_sap is not None:
        fields.append("Material_SAP = ?")
        params.append(material_sap)
    if inforecord_sap is not None:
        fields.append("InfoRecord_SAP = ?")
        params.append(inforecord_sap)

    if fecha_col:
        fields.append(f"{fecha_col} = ?")
        params.append(now_iso())

    params.append(id_material)
    cur.execute(f"UPDATE materiales SET {', '.join(fields)} WHERE ID_Material = ?", params)
    conn.commit()
    conn.close()

    write_historial_event(id_material, estatus_old, nuevo_estatus, comentario, usuario, rol)
    return True

def guardar_archivo_versionado(uploaded_file, id_material: str, usuario: str) -> Optional[dict]:
    if uploaded_file is None:
        return None

    df_arch = df_read_archivos(id_material)
    next_version = 1 if df_arch.empty else int(df_arch["Version"].max()) + 1

    original_name = uploaded_file.name
    ext = Path(original_name).suffix.lower()[:12]
    stored_name = f"{id_material}_v{next_version}{ext}"
    stored_path = FILES_DIR / stored_name

    data = uploaded_file.getbuffer()
    stored_path.write_bytes(data)

    meta = {
        "ID_Archivo": f"FILE-{uuid.uuid4().hex[:12].upper()}",
        "ID_Material": id_material,
        "Version": next_version,
        "Nombre_Original": original_name,
        "Nombre_Almacenado": stored_name,
        "Mime": uploaded_file.type or "",
        "Size_Bytes": int(len(data)),
        "Fecha_Subida": now_iso(),
        "Subido_Por": usuario,
    }

    conn = db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO archivos (
            ID_Archivo, ID_Material, Version, Nombre_Original, Nombre_Almacenado,
            Mime, Size_Bytes, Fecha_Subida, Subido_Por
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            meta["ID_Archivo"], meta["ID_Material"], meta["Version"], meta["Nombre_Original"],
            meta["Nombre_Almacenado"], meta["Mime"], meta["Size_Bytes"], meta["Fecha_Subida"], meta["Subido_Por"]
        ),
    )
    conn.commit()
    conn.close()
    return meta

def excel_bytes_from_dfs(sheets: Dict[str, pd.DataFrame]) -> bytes:
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name[:31], index=False)
    return bio.getvalue()

def template_excel_bytes() -> bytes:
    cols = [
        "Ingeniero", "Linea", "Prioridad", "Comentario_Solicitud",
        "Item", "Descripcion", "Estacion", "Categoria",
        "Frecuencia_Cambio", "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo",
        "RP_Sugerido", "Manufacturer"
    ]
    df = pd.DataFrame(columns=cols)
    info = pd.DataFrame(
        [
            ["INSTRUCCIONES",
             "1) No borres encabezados. 2) 'Descripcion' obligatoria. 3) Categoria: MAZE/FHMI/HIBE.",
             "4) Linea debe existir en catálogo. 5) Prioridad: Alta/Media/Baja. 6) Sube el archivo en 'Excel masivo'."]
        ],
        columns=["Campo", "Regla", "Notas"]
    )
    return excel_bytes_from_dfs({"Template": df, "Guia": info})

def validate_record(r: dict) -> list[str]:
    errors = []
    if not str(r.get("Descripcion","")).strip():
        errors.append("Descripcion obligatoria.")
    if str(r.get("Linea","")) not in LINEAS:
        errors.append("Linea inválida (fuera de catálogo).")
    if str(r.get("Prioridad","")) not in ["Alta","Media","Baja"]:
        errors.append("Prioridad inválida.")
    if str(r.get("Categoria","")) and str(r.get("Categoria","")) not in CATEGORIAS_MATERIAL:
        errors.append("Categoria inválida.")
    try:
        stock = float(r.get("Cant_Stock_Requerida", 0) or 0)
        if stock < 0:
            errors.append("Cant_Stock_Requerida no puede ser negativa.")
    except Exception:
        errors.append("Cant_Stock_Requerida debe ser numérica.")
    return errors

def assign_practicante(linea: str) -> str:
    for resp, lineas in LINEAS_POR_PRACTICANTE.items():
        if linea in lineas:
            return resp
    return ""

def require_login():
    if not st.session_state.get("logged", False):
        st.stop()

def require_role(allowed: list[str]):
    if st.session_state.get("rol") not in allowed:
        st.error("Acceso denegado: no tienes permisos para esta sección.")
        st.stop()

# ---------------------------
# SESSION STATE
# ---------------------------
if "logged" not in st.session_state:
    st.session_state.logged = False

# ---------------------------
# LOGIN
# ---------------------------
if not st.session_state.logged:
    st.markdown(
        f"""
<div class="login-wrap">
  <div class="login-title">Bosch Material Management</div>
  <div class="smallhelp">Acceso seguro · Trazabilidad · Control de flujo</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if "users" not in st.secrets:
        st.warning("Modo demo activo: mover usuarios a st.secrets para producción (Streamlit Cloud).")

    col1, col2 = st.columns([1.2, 1])
    with col1:
        user = st.text_input("Usuario", placeholder="jarol, lalo, jime, niko, admin")
    with col2:
        pwd = st.text_input("Contraseña", type="password", placeholder="••••••••")

    if st.button("Acceder", use_container_width=True):
        u = USERS.get(user)
        if u and _bcrypt_check(pwd, u["pwd_hash"]):
            st.session_state.logged = True
            st.session_state.user = user
            st.session_state.rol = u["rol"]
            st.session_state.responsable = u["responsable"]
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

    st.stop()

# ---------------------------
# HEADER
# ---------------------------
require_login()

h1, h2, h3 = st.columns([3.2, 1.2, 1])
with h1:
    st.markdown("<h1>Bosch Material Management</h1>", unsafe_allow_html=True)
with h2:
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">{svg_icon("user")} Sesión</div>
  <div class="card-sub"><b>{st.session_state.user}</b> · {st.session_state.rol}</div>
</div>
""",
        unsafe_allow_html=True,
    )
with h3:
    if st.button("Cerrar sesión", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ---------------------------
# LOAD DATA
# ---------------------------
df_materiales = df_read_materiales()

# ---------------------------
# UI HELPERS
# ---------------------------
def kpi_row(df: pd.DataFrame):
    if df is None or df.empty:
        st.info("No hay datos para mostrar.")
        return
    counts = {s: int((df["Estatus"] == s).sum()) for s in STATUS}

    items = [
        ("Revisión", counts["En revisión de ingeniería"], "search", "#2E2E2E"),
        ("Cotización", counts["En cotización"], "dashboard", SUCCESS),
        ("Alta SAP", counts["En alta SAP"], "file", "#E65100"),
        ("Espera InfoRecord", counts["En espera de InfoRecord"], "pending", WARN),
        ("InfoRecord creado", counts["Info record creado"], "update", INFO),
        ("Finalizado", counts["Alta finalizada"], "chart", "#0D47A1"),
    ]

    cols = st.columns(6)
    for col, (label, val, icon, ic_color) in zip(cols, items):
        col.markdown(
            f"""
<div class="kpi">
  <div class="kpi-left">
    {svg_icon(icon, color=ic_color, size=20)}
    <div class="label">{label}</div>
  </div>
  <div class="value">{val}</div>
</div>
""",
            unsafe_allow_html=True,
        )

def render_legend():
    chips = []
    for s in STATUS:
        d = STATUS_COLOR[s]
        chips.append(
            f"<span style='display:inline-block;margin:4px 6px;padding:6px 10px;border-radius:999px;"
            f"background:{d['bg']};color:{d['fg']};font-weight:900;font-size:.82rem;'>{s}</span>"
        )
    st.markdown("<div class='card'><div class='card-title'>Leyenda de estatus</div>" + "".join(chips) + "</div>", unsafe_allow_html=True)

def render_table(df: pd.DataFrame, compact: bool, highlight_row: bool = False):
    if df.empty:
        st.info("No hay registros.")
        return

    if compact:
        cols = ["ID_Solicitud", "Linea", "Descripcion", "Prioridad", "Estatus"]
        cols = [c for c in cols if c in df.columns]
        df_disp = df[cols].copy()
    else:
        cols = [
            "Fecha_Solicitud", "Ingeniero", "Linea", "Prioridad",
            "Item", "Descripcion", "Estacion", "Frecuencia_Cambio",
            "Cant_Stock_Requerida", "Cant_Equipos", "Cant_Partes_Equipo",
            "RP_Sugerido", "Manufacturer", "Estatus"
        ]
        cols = [c for c in cols if c in df.columns]
        df_disp = df[cols].copy()

    if "Fecha_Solicitud" in df_disp.columns:
        df_disp["Fecha_Solicitud"] = pd.to_datetime(df_disp["Fecha_Solicitud"], errors="coerce")

    st.markdown(
        f"""
<div class="card">
  <div class="card-title">{svg_icon("file")} Tabla</div>
  <div class="card-sub">Estatus coloreado por proceso · Ordena y filtra</div>
</div>
""",
        unsafe_allow_html=True,
    )
    render_legend()

    styled = style_df_by_status(df_disp, status_col="Estatus", highlight_row=highlight_row)
    st.dataframe(styled, use_container_width=True, hide_index=True)

def seguimiento_update_block(df_scope: pd.DataFrame):
    st.markdown(
        f"""
<div class="card">
  <div class="card-title">{svg_icon("update")} Actualizar estatus</div>
  <div class="card-sub">Auditoría: cada cambio requiere comentario.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if df_scope.empty:
        st.info("No hay materiales para actualizar en este alcance.")
        return

    id_material = st.selectbox("Material", df_scope["ID_Material"].tolist())

    row = df_scope[df_scope["ID_Material"] == id_material].iloc[0]
    estatus_actual = row["Estatus"]

    st.markdown(
        f"<div class='card'><div class='card-title'>Estatus actual</div>"
        f"<div style='margin-top:8px'>{badge_html(estatus_actual)}</div></div>",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1.2])
    with c1:
        nuevo_estatus = st.selectbox("Nuevo estatus", STATUS, index=STATUS.index(estatus_actual))
        comentario = st.text_area("Comentario (obligatorio)", height=90, placeholder="Ej. Cotización enviada / Falta InfoRecord / Alta completada…")
    with c2:
        st.markdown("<div class='card'><div class='card-title'>Campos SAP / InfoRecord</div><div class='card-sub'>Opcional</div></div>", unsafe_allow_html=True)
        mat_sap = st.text_input("Material SAP", value=str(row.get("Material_SAP","") or ""))
        ir_sap = st.text_input("InfoRecord SAP", value=str(row.get("InfoRecord_SAP","") or ""))

        up_file = st.file_uploader("Adjuntar archivo (versionado)", type=["png","jpg","jpeg","pdf"], key=f"upl_{id_material}")

    b1, b2, b3 = st.columns([1, 1, 1])
    with b1:
        if st.button("Guardar cambio", use_container_width=True):
            if not comentario.strip():
                st.error("El comentario es obligatorio.")
            else:
                ok = update_estatus_material(
                    id_material=id_material,
                    nuevo_estatus=nuevo_estatus,
                    comentario=comentario.strip(),
                    usuario=st.session_state.user,
                    rol=st.session_state.rol,
                    material_sap=mat_sap.strip(),
                    inforecord_sap=ir_sap.strip(),
                )
                if up_file is not None:
                    guardar_archivo_versionado(up_file, id_material, st.session_state.user)

                if ok:
                    st.success(f"Estatus actualizado a: {nuevo_estatus}")
                    st.rerun()
                else:
                    st.error("No se pudo actualizar.")

    with b2:
        if st.button("Ver historial", use_container_width=True):
            df_h = df_read_historial(id_material)
            st.dataframe(df_h, use_container_width=True, hide_index=True)

    with b3:
        if st.button("Ver archivos", use_container_width=True):
            df_a = df_read_archivos(id_material)
            if df_a.empty:
                st.info("Sin archivos.")
            else:
                st.dataframe(df_a[["Version","Nombre_Original","Fecha_Subida","Subido_Por","Size_Bytes"]], use_container_width=True, hide_index=True)
                latest = df_a.iloc[0]
                p = FILES_DIR / latest["Nombre_Almacenado"]
                if p.exists():
                    st.download_button(
                        "Descargar última versión",
                        data=p.read_bytes(),
                        file_name=latest["Nombre_Original"],
                        mime=latest["Mime"] or "application/octet-stream",
                        use_container_width=True
                    )

def kanban_view(df: pd.DataFrame):
    if df.empty:
        st.info("No hay registros para mostrar.")
        return

    # filtros rápidos
    c1, c2 = st.columns([1.2, 1])
    with c1:
        q = st.text_input("Buscar en Kanban", placeholder="ID / Solicitud / Descripción / Item")
    with c2:
        pr = st.multiselect("Prioridad", ["Alta","Media","Baja"], default=["Alta","Media","Baja"], key="kanban_pri")

    dfx = df.copy()
    dfx = dfx[dfx["Prioridad"].isin(pr)].copy()
    if q.strip():
        ql = q.strip().lower()
        dfx = dfx[
            dfx["ID_Material"].astype(str).str.lower().str.contains(ql)
            | dfx["ID_Solicitud"].astype(str).str.lower().str.contains(ql)
            | dfx["Descripcion"].astype(str).str.lower().str.contains(ql)
            | dfx["Item"].astype(str).str.lower().str.contains(ql)
        ].copy()

    cols = st.columns(len(STATUS))
    for i, status in enumerate(STATUS):
        col = cols[i]
        d = STATUS_COLOR[status]
        col.markdown(
            f"""
<div class="card" style="border-left:8px solid {d['fg']}; background: linear-gradient(135deg, {d['bg']}, #ffffff);">
  <div class="card-title">{status}</div>
  <div class="card-sub"><b>{int((dfx["Estatus"]==status).sum())}</b> items</div>
</div>
""",
            unsafe_allow_html=True,
        )

        items = dfx[dfx["Estatus"] == status].sort_values(["Prioridad","Fecha_Solicitud"], ascending=[True, False]).head(25)

        for _, r in items.iterrows():
            col.markdown(
                f"""
<div class="card" style="padding:12px 12px;margin-top:10px;">
  <div style="display:flex;justify-content:space-between;gap:10px;">
    <div style="font-weight:900;color:{BOSCH_BLUE};">{r["ID_Material"]}</div>
    <div style="font-weight:800;color:#333;">{r["Prioridad"]}</div>
  </div>
  <div style="margin-top:6px;font-weight:800;color:#2d2d2d;">{str(r["Descripcion"])[:85]}</div>
  <div class="smallhelp" style="margin-top:6px;">
    Solicitud: <b>{r["ID_Solicitud"]}</b><br/>
    Línea: <b>{r["Linea"]}</b> · Item: <b>{str(r["Item"])[:20]}</b>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

            move_to = col.selectbox("Mover a", STATUS, index=STATUS.index(status), key=f"mv_{r['ID_Material']}")
            comment = col.text_input("Comentario", placeholder="Motivo del cambio", key=f"cm_{r['ID_Material']}")
            if col.button("Aplicar", key=f"ap_{r['ID_Material']}"):
                if not comment.strip():
                    col.error("Comentario obligatorio.")
                else:
                    ok = update_estatus_material(
                        id_material=r["ID_Material"],
                        nuevo_estatus=move_to,
                        comentario=comment.strip(),
                        usuario=st.session_state.user,
                        rol=st.session_state.rol
                    )
                    if ok:
                        col.success("Actualizado.")
                        st.rerun()
                    else:
                        col.error("No se pudo actualizar.")

def charts_dashboard(df: pd.DataFrame):
    if df.empty:
        st.info("No hay datos.")
        return

    dfx = df.copy()
    dfx["Fecha_Solicitud"] = pd.to_datetime(dfx["Fecha_Solicitud"], errors="coerce")
    dfx["Semana_ISO"] = dfx["Fecha_Solicitud"].apply(iso_week)

    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.pie(dfx, names="Estatus", title="Distribución por estatus")
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        weekly = dfx[dfx["Semana_ISO"].notna()].groupby(["Semana_ISO","Estatus"]).size().reset_index(name="Cantidad")
        fig2 = px.bar(weekly, x="Semana_ISO", y="Cantidad", color="Estatus", title="Conteo semanal por estatus (ISO)")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div class='card'><div class='card-title'>Pendientes por practicante</div></div>", unsafe_allow_html=True)
    pend = dfx[dfx["Estatus"] != "Alta finalizada"].groupby(["Practicante_Asignado","Estatus"]).size().reset_index(name="Cantidad")
    fig3 = px.bar(pend, x="Practicante_Asignado", y="Cantidad", color="Estatus", title="Pendientes por practicante y estatus")
    st.plotly_chart(fig3, use_container_width=True)

# ---------------------------
# SIDEBAR NAV
# ---------------------------
with st.sidebar:
    st.markdown("### Menú")

    if st.session_state.rol == "practicante":
        lineas_usuario = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
        df_my = df_materiales[df_materiales["Linea"].isin(lineas_usuario)].copy() if len(df_materiales) else pd.DataFrame()
        pendientes = int((df_my["Estatus"] != "Alta finalizada").sum()) if len(df_my) else 0

        st.markdown(
            f"""
<div class="card">
  <div class="card-title">{svg_icon("pending", color=DANGER)} Pendientes</div>
  <div class="card-sub"><span style="font-size:1.6rem;font-weight:900;color:{DANGER};">{pendientes}</span></div>
  <div class="smallhelp">Líneas: {", ".join(lineas_usuario) if lineas_usuario else "—"}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        opcion = st.radio("Secciones", ["Mis pendientes", "Seguimiento (BETA)", "Nueva solicitud"], index=0)
    else:
        opcion = st.radio("Secciones", ["Dashboard ejecutivo", "Seguimiento", "Nueva solicitud"], index=0)

# ---------------------------
# PRACTICANTE: MIS PENDIENTES
# ---------------------------
if opcion == "Mis pendientes":
    require_role(["practicante"])

    st.markdown(f"## Mis pendientes · {st.session_state.responsable}")

    lineas_usuario = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_my = df_materiales[df_materiales["Linea"].isin(lineas_usuario)].copy() if len(df_materiales) else pd.DataFrame()
    df_pend = df_my[df_my["Estatus"] != "Alta finalizada"].copy() if len(df_my) else pd.DataFrame()

    f1, f2, f3 = st.columns([1, 1, 1.2])
    with f1:
        pr = st.multiselect("Prioridad", ["Alta","Media","Baja"], default=["Alta","Media","Baja"])
    with f2:
        stt = st.multiselect("Estatus", STATUS, default=STATUS)
    with f3:
        q = st.text_input("Buscar", placeholder="ID / Item / Descripción / Estación")

    if not df_pend.empty:
        df_f = df_pend[df_pend["Prioridad"].isin(pr) & df_pend["Estatus"].isin(stt)].copy()
        if q.strip():
            ql = q.strip().lower()
            df_f = df_f[
                df_f["ID_Material"].astype(str).str.lower().str.contains(ql)
                | df_f["ID_Solicitud"].astype(str).str.lower().str.contains(ql)
                | df_f["Item"].astype(str).str.lower().str.contains(ql)
                | df_f["Descripcion"].astype(str).str.lower().str.contains(ql)
                | df_f["Estacion"].astype(str).str.lower().str.contains(ql)
            ].copy()

        kpi_row(df_f)
        render_table(df_f.sort_values(["Prioridad","Fecha_Solicitud"], ascending=[True, False]), compact=False, highlight_row=False)

        exp = df_f.copy()
        exp["Semana_ISO"] = exp["Fecha_Solicitud"].apply(iso_week)
        st.download_button(
            "Descargar mis pendientes (Excel)",
            data=excel_bytes_from_dfs({"Mis_Pendientes": exp}),
            file_name=f"mis_pendientes_{st.session_state.responsable}_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.success("Sin pendientes.")

# ---------------------------
# PRACTICANTE: SEGUIMIENTO (BETA) + VISTA TABLA / KANBAN + UPDATE
# ---------------------------
if opcion == "Seguimiento (BETA)":
    require_role(["practicante"])

    st.markdown("## Seguimiento (BETA)")

    lineas_usuario = LINEAS_POR_PRACTICANTE.get(st.session_state.responsable, [])
    df_scope = df_materiales[df_materiales["Linea"].isin(lineas_usuario)].copy() if len(df_materiales) else pd.DataFrame()

    if not df_scope.empty:
        kpi_row(df_scope)

    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        linea = st.selectbox("Línea", ["Todas"] + lineas_usuario)
    with c2:
        estatus = st.selectbox("Estatus", ["Todos"] + STATUS)
    with c3:
        b = st.text_input("Buscar", placeholder="SOL-... / descripción...")

    df_f = df_scope.copy()
    if linea != "Todas":
        df_f = df_f[df_f["Linea"] == linea]
    if estatus != "Todos":
        df_f = df_f[df_f["Estatus"] == estatus]
    if b.strip():
        bl = b.strip().lower()
        df_f = df_f[
            df_f["ID_Solicitud"].astype(str).str.lower().str.contains(bl)
            | df_f["Descripcion"].astype(str).str.lower().str.contains(bl)
        ].copy()

    view = st.radio("Vista", ["Tabla", "Kanban"], horizontal=True)

    if view == "Tabla":
        render_table(df_f.sort_values(["Fecha_Solicitud"], ascending=False), compact=True, highlight_row=False)
    else:
        kanban_view(df_f)

    st.markdown("---")
    seguimiento_update_block(df_scope)

# ---------------------------
# NUEVA SOLICITUD (Practicante + Jefa)
# ---------------------------
if opcion == "Nueva solicitud":
    if st.session_state.rol not in ["practicante", "jefa"]:
        st.error("Acceso denegado.")
        st.stop()

    st.markdown("## Nueva solicitud")

    c1, c2, c3 = st.columns(3)
    ingeniero = c1.text_input("Ingeniero solicitante", value=st.session_state.user)
    linea_sel = c2.selectbox("Línea", LINEAS)
    prioridad_sel = c3.selectbox("Prioridad", ["Alta", "Media", "Baja"])

    tabs = st.tabs(["Formulario (1–5)", "Excel masivo (>5)"])

    with tabs[0]:
        num = st.slider("Número de materiales", 1, 5, 1)
        with st.form("form_solicitud"):
            mats = []
            for i in range(num):
                st.markdown(f"### Material {i+1}")
                a, b = st.columns([1.15, 1])
                with a:
                    item = st.text_input("Item/Nº parte", key=f"item_{i}")
                    desc = st.text_input("Descripción (obligatorio)", key=f"desc_{i}")
                    est = st.text_input("Estación/Máquina", key=f"est_{i}")
                    cat = st.selectbox("Categoría", [""] + CATEGORIAS_MATERIAL, key=f"cat_{i}")
                    freq = st.text_input("Frecuencia de cambio", key=f"freq_{i}")
                with b:
                    stock = st.number_input("Stock requerido", min_value=0.0, value=0.0, step=0.5, key=f"stock_{i}")
                    equipos = st.number_input("Cantidad de equipos", min_value=0, value=0, step=1, key=f"eq_{i}")
                    partes = st.number_input("Partes por equipo", min_value=0, value=0, step=1, key=f"part_{i}")
                    rp = st.text_input("RP sugerido", key=f"rp_{i}")
                    manu = st.text_input("Manufacturer / Proveedor", key=f"manu_{i}")

                up = st.file_uploader("Adjunto (opcional)", type=["png","jpg","jpeg","pdf"], key=f"file_{i}")

                mats.append({
                    "Ingeniero": ingeniero,
                    "Linea": linea_sel,
                    "Prioridad": prioridad_sel,
                    "Item": item,
                    "Descripcion": desc,
                    "Estacion": est,
                    "Categoria": cat,
                    "Frecuencia_Cambio": freq,
                    "Cant_Stock_Requerida": stock,
                    "Cant_Equipos": equipos,
                    "Cant_Partes_Equipo": partes,
                    "RP_Sugerido": rp,
                    "Manufacturer": manu,
                    "Archivo": up
                })

            comentario_general = st.text_area("Comentario general", height=90)
            submitted = st.form_submit_button("Guardar solicitud", use_container_width=True)

        if submitted:
            id_sol = generar_id_solicitud()
            registros = []
            errors_all = []
            for m in mats:
                rec = dict(m)
                rec["Comentario_Solicitud"] = comentario_general
                rec["ID_Solicitud"] = id_sol
                rec["ID_Material"] = generar_id_material()
                rec["Fecha_Solicitud"] = now_iso()
                rec["Estatus"] = "En revisión de ingeniería"
                rec["Practicante_Asignado"] = assign_practicante(rec["Linea"])
                rec["Comentario_Estatus"] = ""
                rec["Material_SAP"] = ""
                rec["InfoRecord_SAP"] = ""
                rec["Fecha_Revision"] = None
                rec["Fecha_Cotizacion"] = None
                rec["Fecha_Alta_SAP"] = None
                rec["Fecha_InfoRecord"] = None
                rec["Fecha_Finalizada"] = None

                errs = validate_record(rec)
                if errs:
                    errors_all.append((rec["ID_Material"], errs))
                    continue
                registros.append(rec)

            if errors_all:
                st.error("Errores detectados en algunos materiales (no se guardaron esos registros):")
                for mid, errs in errors_all:
                    st.write(f"{mid} → " + "; ".join(errs))

            if registros:
                insert_materiales(registros)
                for r in registros:
                    write_historial_event(r["ID_Material"], "CREADO", r["Estatus"], "Solicitud creada", st.session_state.user, st.session_state.rol)
                    if r.get("Archivo") is not None:
                        guardar_archivo_versionado(r["Archivo"], r["ID_Material"], st.session_state.user)

                st.success(f"Solicitud {id_sol} guardada con {len(registros)} materiales.")
                st.rerun()

    with tabs[1]:
        st.markdown(
            f"""
<div class="card">
  <div class="card-title">{svg_icon("download")} Carga masiva (Excel)</div>
  <div class="card-sub">Descarga el template, llena los materiales y súbelo aquí.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.download_button(
            "Descargar template (Critical Evaluation)",
            data=template_excel_bytes(),
            file_name="Template_Carga_Masiva_Bosch.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        up_xlsx = st.file_uploader("Subir Excel de carga masiva", type=["xlsx"])
        if up_xlsx is not None:
            try:
                xls = pd.ExcelFile(up_xlsx)
                if "Template" not in xls.sheet_names:
                    st.error("El Excel debe contener la hoja 'Template' del archivo descargado.")
                else:
                    df_up = pd.read_excel(xls, "Template").dropna(how="all")
                    if df_up.empty:
                        st.warning("El archivo no contiene filas.")
                    else:
                        required_cols = [
                            "Ingeniero","Linea","Prioridad","Comentario_Solicitud",
                            "Item","Descripcion","Estacion","Categoria","Frecuencia_Cambio",
                            "Cant_Stock_Requerida","Cant_Equipos","Cant_Partes_Equipo","RP_Sugerido","Manufacturer"
                        ]
                        missing = [c for c in required_cols if c not in df_up.columns]
                        if missing:
                            st.error("Faltan columnas: " + ", ".join(missing))
                        else:
                            df_up["Ingeniero"] = df_up["Ingeniero"].fillna(ingeniero)
                            df_up["Linea"] = df_up["Linea"].fillna(linea_sel)
                            df_up["Prioridad"] = df_up["Prioridad"].fillna(prioridad_sel)

                            id_sol = generar_id_solicitud()
                            registros = []
                            errors_all = []
                            for _, row in df_up.iterrows():
                                rec = row.to_dict()
                                rec["ID_Solicitud"] = id_sol
                                rec["ID_Material"] = generar_id_material()
                                rec["Fecha_Solicitud"] = now_iso()
                                rec["Estatus"] = "En revisión de ingeniería"
                                rec["Practicante_Asignado"] = assign_practicante(str(rec.get("Linea","")))
                                rec["Comentario_Estatus"] = ""
                                rec["Material_SAP"] = ""
                                rec["InfoRecord_SAP"] = ""
                                rec["Fecha_Revision"] = None
                                rec["Fecha_Cotizacion"] = None
                                rec["Fecha_Alta_SAP"] = None
                                rec["Fecha_InfoRecord"] = None
                                rec["Fecha_Finalizada"] = None

                                errs = validate_record(rec)
                                if errs:
                                    errors_all.append((rec["ID_Material"], errs, str(rec.get("Descripcion",""))[:60]))
                                else:
                                    registros.append(rec)

                            if errors_all:
                                st.error("Errores detectados (revisa estos registros):")
                                for mid, errs, d in errors_all[:40]:
                                    st.write(f"{mid} · {d} → " + "; ".join(errs))
                                if len(errors_all) > 40:
                                    st.caption(f"… y {len(errors_all)-40} más.")

                            if registros:
                                insert_materiales(registros)
                                for r in registros:
                                    write_historial_event(r["ID_Material"], "CREADO", r["Estatus"], "Solicitud masiva creada", st.session_state.user, st.session_state.rol)
                                st.success(f"Solicitud masiva {id_sol} guardada con {len(registros)} materiales.")
                                st.rerun()

            except Exception as e:
                st.error("No se pudo leer el archivo. Verifica el formato.")
                st.caption(str(e))

# ---------------------------
# JEFA/ADMIN: DASHBOARD + CHARTS + EXPORTS
# ---------------------------
if opcion == "Dashboard ejecutivo":
    require_role(["jefa"])
    st.markdown("## Dashboard ejecutivo")

    if df_materiales.empty:
        st.info("Aún no hay datos.")
    else:
        kpi_row(df_materiales)
        charts_dashboard(df_materiales)

        df_trend = df_materiales.copy()
        df_trend["Semana_ISO"] = df_trend["Fecha_Solicitud"].apply(iso_week)
        trend = df_trend.groupby(["Semana_ISO","Estatus"], dropna=False).size().reset_index(name="Cantidad")
        trend = trend[trend["Semana_ISO"].notna()].copy()

        st.markdown(
            f"""
<div class="card">
  <div class="card-title">{svg_icon("chart")} Conteo por semana (ISO)</div>
  <div class="card-sub">Comparación semanal (ej. semana 15 vs 16 vs 17).</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.dataframe(trend.sort_values(["Semana_ISO","Estatus"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown(
            f"""
<div class="card">
  <div class="card-title">{svg_icon("download")} Exportables</div>
  <div class="card-sub">Materiales + historial + archivos + semanal.</div>
</div>
""",
            unsafe_allow_html=True,
        )

        df_h = df_read_historial()
        conn = db()
        df_a = pd.read_sql_query("SELECT * FROM archivos", conn)
        conn.close()
        if len(df_a) and "Fecha_Subida" in df_a.columns:
            df_a["Fecha_Subida"] = safe_to_datetime(df_a["Fecha_Subida"])

        all_bytes = excel_bytes_from_dfs({
            "Materiales": df_materiales.copy(),
            "Historial": df_h.copy(),
            "Archivos": df_a.copy(),
            "Semanal": trend.copy(),
        })

        st.download_button(
            "Descargar reporte completo (Excel)",
            data=all_bytes,
            file_name=f"Bosch_Material_Management_Reporte_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.markdown("<div class='card'><div class='card-title'>Snapshot por semana</div><div class='card-sub'>Selecciona semana ISO y descarga el corte.</div></div>", unsafe_allow_html=True)
        weeks = sorted([w for w in df_trend["Semana_ISO"].dropna().unique().tolist()])
        sel_week = st.selectbox("Semana", weeks if weeks else ["—"])

        if weeks:
            snap = df_trend[df_trend["Semana_ISO"] == sel_week].copy()
            snap_ids = snap["ID_Material"].unique().tolist()
            df_hs = df_h[df_h["ID_Material"].isin(snap_ids)].copy()

            st.download_button(
                f"Descargar snapshot {sel_week} (Excel)",
                data=excel_bytes_from_dfs({"Materiales": snap, "Historial": df_hs}),
                file_name=f"Snapshot_{sel_week}_{date.today().isoformat()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# ---------------------------
# JEFA/ADMIN: SEGUIMIENTO + TABLA / KANBAN + UPDATE
# ---------------------------
if opcion == "Seguimiento":
    require_role(["jefa"])
    st.markdown("## Seguimiento")

    if df_materiales.empty:
        st.info("No hay datos.")
    else:
        kpi_row(df_materiales)

        c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2])
        with c1:
            linea = st.selectbox("Línea", ["Todas"] + LINEAS)
        with c2:
            pract = st.selectbox("Practicante", ["Todos"] + list(LINEAS_POR_PRACTICANTE.keys()))
        with c3:
            est = st.selectbox("Estatus", ["Todos"] + STATUS)
        with c4:
            q = st.text_input("Buscar", placeholder="ID / solicitud / descripción")

        df_f = df_materiales.copy()
        if linea != "Todas":
            df_f = df_f[df_f["Linea"] == linea]
        if pract != "Todos":
            df_f = df_f[df_f["Practicante_Asignado"] == pract]
        if est != "Todos":
            df_f = df_f[df_f["Estatus"] == est]
        if q.strip():
            ql = q.strip().lower()
            df_f = df_f[
                df_f["ID_Material"].astype(str).str.lower().str.contains(ql)
                | df_f["ID_Solicitud"].astype(str).str.lower().str.contains(ql)
                | df_f["Descripcion"].astype(str).str.lower().str.contains(ql)
                | df_f["Item"].astype(str).str.lower().str.contains(ql)
            ].copy()

        view = st.radio("Vista", ["Tabla", "Kanban"], horizontal=True, key="view_jefa")

        if view == "Tabla":
            render_table(df_f.sort_values(["Fecha_Solicitud"], ascending=False), compact=True, highlight_row=False)
        else:
            kanban_view(df_f)

        st.markdown("---")
        seguimiento_update_block(df_f)

        st.download_button(
            "Descargar vista filtrada (Excel)",
            data=excel_bytes_from_dfs({"Seguimiento_Filtrado": df_f.copy()}),
            file_name=f"seguimiento_filtrado_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
