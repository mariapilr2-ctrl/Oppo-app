# ══════════════════════════════════════════════════════════════════════
#  OpoMaestro — Versión Final
#  Fases 1 + 2 + 3 integradas
#  ─────────────────────────────────────────────────────────────────────
#  Funciones:
#  · Base de datos JSON local con migración automática
#  · Repaso espaciado (1·3·5·7·30 días)
#  · Selector de tiempo "Vida Real" + priorización de Huesos
#  · Monitor Invisible (detecta Puntos Débiles, reprograma automáticamente)
#  · Simulador de Voz: Web Speech API (micrófono nativo del navegador)
#    + modo escrito como fallback
#  · Feedback por Conceptos Clave detectados / omitidos
#  · Diccionario de Trampas del Examinador por artículo
#  · Lector OCR de imágenes (pytesseract)
#  · Diseño oceánico azul, móvil-friendly
# ══════════════════════════════════════════════════════════════════════

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json, os, re, math
from datetime import datetime, date, timedelta

# ── OCR opcional ────────────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    import io as _io
    OCR_OK = True
except ImportError:
    OCR_OK = False

# ════════════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="OpoMaestro · Final",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

INTERVALOS = [1, 3, 5, 7, 30]   # SM-2 simplificado
DB_FILE    = "oposiciones_final_db.json"

# Palabras vacías en español para el análisis de conceptos
STOPWORDS = {
    "el","la","los","las","un","una","unos","unas","de","del","al","a",
    "en","con","por","para","que","se","su","sus","le","les","lo","y",
    "o","e","pero","sino","mas","si","no","ni","es","son","ser","estar",
    "ha","han","fue","era","será","será","este","esta","estos","estas",
    "ese","esa","esos","esas","aquel","aquella","aquellos","aquellas",
    "dicho","dicha","dichos","dichas","todo","toda","todos","todas",
    "otro","otra","otros","otras","mismo","misma","mismos","mismas",
    "cuyo","cuya","cuyos","cuyas","cuál","cuáles","cual","cuales",
    "sobre","entre","hasta","desde","hacia","ante","bajo","cabe","contra",
    "durante","mediante","según","sin","so","tras","versus","vía",
    "como","cuando","donde","mientras","aunque","porque","pues","ya",
    "así","también","además","incluso","salvo","excepto","mediante",
    "dentro","fuera","antes","después","siempre","nunca","jamás",
    "muy","más","menos","tan","tanto","cuanto","algo","nada","alguien",
    "nadie","cada","ambos","ambas","sendos","sendas","respectivo","dicho",
    "presente","siguiente","anterior","posterior","correspondiente",
    "establecido","previsto","señalado","indicado","referido","citado",
}


# ════════════════════════════════════════════════════════════════════
#  CSS  — Paleta oceánica azul profundo + mobile-first
# ════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;500;600&display=swap');

/* ── Variables ─────────────────────────────────────────── */
:root {
  --ocean:   #061526;
  --deep:    #0a1f3d;
  --mid:     #0f3460;
  --cobalt:  #1a4fa0;
  --sky:     #2980d4;
  --cyan:    #0dc5e5;
  --ice:     #d6eeff;
  --cream:   #eaf3fc;
  --white:   #f5faff;
  --muted:   #7ba3cc;
  --border:  #bad2ee;
  --red:     #e53e3e;
  --orange:  #dd6b20;
  --green:   #276749;
  --amber:   #b7791f;
  --purple:  #553c9a;
  --r:       14px;
  --sh:      0 4px 24px rgba(6,21,38,.13);
}

/* ── Base ──────────────────────────────────────────────── */
html,body,[class*="css"]   { font-family:'Inter',sans-serif; }
.main                       { background:var(--cream)!important; }
.block-container            { padding-top:1.4rem!important; max-width:1200px; }

/* ── Sidebar ───────────────────────────────────────────── */
section[data-testid="stSidebar"]      { background:var(--ocean)!important; }
section[data-testid="stSidebar"] *    { color:#c8dff5!important; }
section[data-testid="stSidebar"] hr   { border-color:rgba(255,255,255,.08)!important; }
section[data-testid="stSidebar"] .stRadio label {
  font-size:1.05rem!important; padding:.6rem .9rem!important;
  border-radius:10px; transition:background .15s;
}
section[data-testid="stSidebar"] .stRadio label:hover {
  background:rgba(255,255,255,.07)!important;
}

/* ── Header ────────────────────────────────────────────── */
.app-header {
  background:linear-gradient(135deg,var(--ocean) 0%,var(--mid) 55%,var(--cobalt) 100%);
  border-radius:var(--r); padding:1.8rem 2.4rem; margin-bottom:1.8rem;
  box-shadow:0 10px 40px rgba(6,21,38,.28);
  display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:1rem;
}
.app-header h1 {
  font-family:'Playfair Display',serif!important;
  font-size:2.3rem!important; color:var(--cyan)!important;
  margin:0!important; padding:0!important; line-height:1.05!important;
}
.app-header p { color:var(--muted)!important; font-size:.9rem!important; margin:.3rem 0 0!important; }
.header-chip  {
  background:rgba(13,197,229,.14); border:1px solid rgba(13,197,229,.3);
  border-radius:24px; padding:.4rem 1.1rem; font-size:.83rem; color:var(--cyan)!important;
}

/* ── Títulos de sección ─────────────────────────────────── */
.sec-title {
  font-family:'Playfair Display',serif; font-size:1.6rem; color:var(--deep);
  border-left:5px solid var(--sky); padding-left:.85rem; margin-bottom:1.5rem;
}

/* ── Botones GRANDES (mobile-friendly) ─────────────────── */
.stButton>button {
  background:linear-gradient(135deg,var(--cobalt),var(--mid))!important;
  color:#e8f4ff!important; border:none!important; border-radius:12px!important;
  font-weight:600!important; font-size:1.05rem!important;
  padding:.75rem 2rem!important; min-height:48px!important;
  transition:opacity .18s, transform .1s!important; letter-spacing:.02em!important;
}
.stButton>button:hover   { opacity:.86!important; transform:translateY(-1px)!important; }
.stButton>button:active  { transform:translateY(0)!important; }

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap:.5rem; }
.stTabs [data-baseweb="tab"] {
  border-radius:10px!important; padding:.5rem 1.2rem!important;
  font-weight:500!important; font-size:.95rem!important;
}
.stTabs [aria-selected="true"] { background:var(--cobalt)!important; color:#fff!important; }

/* ── Slider ─────────────────────────────────────────────── */
.stSlider>div>div>div>div { background:var(--sky)!important; }
.stSlider [data-testid="stThumbValue"] { font-size:1rem!important; font-weight:700!important; }

/* ── Panel de tiempo ─────────────────────────────────────── */
.time-panel {
  background:linear-gradient(135deg,var(--deep),var(--mid));
  border-radius:var(--r); padding:1.5rem 2rem; margin-bottom:1.8rem;
  box-shadow:var(--sh);
}
.time-panel h3 { color:#93d4f5!important; font-size:1rem!important; margin:0 0 .5rem!important; text-transform:uppercase; letter-spacing:.08em; }

/* ── Modo sesión ─────────────────────────────────────────── */
.mode-pill {
  display:inline-flex; align-items:center; gap:.5rem;
  border-radius:30px; padding:.5rem 1.3rem; font-weight:600; font-size:.9rem;
  margin-bottom:1rem;
}
.mode-urgente { background:#fff5f5; color:#9b2c2c; border:1px solid #feb2b2; }
.mode-normal  { background:#ebf8ff; color:#2b6cb0; border:1px solid #bee3f8; }
.mode-amplio  { background:#f0fff4; color:#276749; border:1px solid #9ae6b4; }

/* ── Tarjetas ────────────────────────────────────────────── */
.art-card {
  background:var(--white); border-radius:var(--r); padding:1.4rem 1.7rem;
  border:1px solid var(--border); margin-bottom:.9rem; box-shadow:var(--sh);
  position:relative; overflow:hidden;
  transition:box-shadow .2s, transform .15s;
}
.art-card:hover { box-shadow:0 8px 28px rgba(6,21,38,.16); transform:translateY(-2px); }
.art-card::before {
  content:''; position:absolute; left:0; top:0; bottom:0;
  width:5px; border-radius:5px 0 0 5px;
}
.art-card.facil::before  { background:var(--green); }
.art-card.hueso::before  { background:var(--red); }
.art-card.debil::before  { background:var(--orange); animation:pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:1;}50%{opacity:.35;} }

.card-hdr { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:.6rem; flex-wrap:wrap; gap:.4rem; }
.card-id  { font-family:'Playfair Display',serif; font-size:1.05rem; color:var(--deep); font-weight:700; }
.badges   { display:flex; gap:.35rem; flex-wrap:wrap; }
.card-txt { color:#374151; font-size:.93rem; line-height:1.65; overflow:hidden;
            display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; }
.card-meta { margin-top:.55rem; font-size:.76rem; color:var(--muted); display:flex; gap:1rem; flex-wrap:wrap; }

/* ── Badges ──────────────────────────────────────────────── */
.badge         { padding:.2rem .7rem; border-radius:20px; font-size:.73rem; font-weight:600; letter-spacing:.04em; }
.b-facil       { background:#c6f6d5; color:#22543d; }
.b-hueso       { background:#fed7d7; color:#822727; }
.b-debil       { background:#feebc8; color:#7b341e; }
.b-imagen      { background:#bee3f8; color:#2a4365; }
.b-gancho      { background:#fefcbf; color:#744210; }
.b-historia    { background:#e9d8fd; color:#44337a; }
.b-hoy         { background:#c3dafe; color:#3c366b; }
.b-ok          { background:#c6f6d5; color:#22543d; }
.b-atrasado    { background:#fed7d7; color:#822727; }
.b-trampa      { background:#fed7d7; color:#822727; }
.b-maestro     { background:#fefcbf; color:#744210; }

/* ── Métricas ────────────────────────────────────────────── */
.met-row { display:flex; gap:.85rem; margin-bottom:1.4rem; flex-wrap:wrap; }
.met-box {
  background:var(--white); border:1px solid var(--border); border-radius:var(--r);
  padding:.9rem 1.3rem; flex:1; min-width:105px; text-align:center;
  box-shadow:0 2px 10px rgba(6,21,38,.07);
}
.met-num { font-family:'Playfair Display',serif; font-size:1.85rem; font-weight:900; display:block; color:var(--deep); }
.met-lbl { font-size:.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:.07em; }

/* ── Simulador de Voz ────────────────────────────────────── */
.voice-panel {
  background:linear-gradient(135deg,var(--deep) 0%,#0a2a5c 100%);
  border-radius:var(--r); padding:1.6rem 2rem; margin-bottom:1.5rem;
  border:1px solid rgba(13,197,229,.25); box-shadow:var(--sh);
}
.voice-panel h4 { color:var(--cyan)!important; font-family:'Playfair Display',serif; margin-top:0; font-size:1.25rem; }
.voice-panel p  { color:#7ba3cc!important; font-size:.88rem; margin:.3rem 0 0; }

/* ── Barra de precisión ──────────────────────────────────── */
.precision-bar {
  background:#0a1f3d; border-radius:8px; height:18px; overflow:hidden;
  margin:.6rem 0 .3rem;
}
.precision-fill {
  height:100%; border-radius:8px;
  transition:width .7s cubic-bezier(.4,0,.2,1);
}
.pf-alto  { background:linear-gradient(90deg,#2ecc71,#27ae60); }
.pf-medio { background:linear-gradient(90deg,#f39c12,#e67e22); }
.pf-bajo  { background:linear-gradient(90deg,#e74c3c,#c0392b); }

/* ── Conceptos ───────────────────────────────────────────── */
.concepto-ok  { background:#f0fff4; border:1px solid #9ae6b4; border-radius:8px; padding:.4rem .9rem; display:inline-flex; align-items:center; gap:.4rem; font-size:.88rem; color:#22543d; margin:.25rem; }
.concepto-err { background:#fff5f5; border:1px solid #fc8181; border-radius:8px; padding:.4rem .9rem; display:inline-flex; align-items:center; gap:.4rem; font-size:.88rem; color:#822727; margin:.25rem; }

/* ── Trampa ──────────────────────────────────────────────── */
.trampa-box {
  background:#fff5f5; border:1.5px solid #fc8181; border-radius:10px;
  padding:.9rem 1.2rem; margin-top:.8rem;
}
.trampa-box h5 { color:#c53030!important; margin:0 0 .3rem; font-size:.9rem; }
.trampa-txt    { color:#742a2a; font-size:.88rem; line-height:1.5; }

/* ── Monitor Invisible ───────────────────────────────────── */
.monitor-alert {
  background:linear-gradient(135deg,#1a0a00,#3d1a00);
  border:1px solid var(--orange); border-radius:var(--r);
  padding:1rem 1.4rem; margin-bottom:1rem;
}
.monitor-alert h5 { color:#fbd38d!important; margin:0 0 .3rem; }
.monitor-alert p  { color:#f6ad55!important; font-size:.87rem; margin:0; }

/* ── Barra progreso sesión ───────────────────────────────── */
.prog-wrap  { background:#d6eeff; border-radius:8px; height:12px; overflow:hidden; margin:.4rem 0 1rem; }
.prog-fill  { height:100%; border-radius:8px; background:linear-gradient(90deg,var(--sky),var(--cyan)); transition:width .4s ease; }

/* ── OCR panel ───────────────────────────────────────────── */
.ocr-panel {
  background:linear-gradient(135deg,var(--deep),#0c2461);
  border-radius:var(--r); padding:1.4rem 1.8rem; margin-bottom:1.4rem;
  border:1px solid var(--cobalt);
}
.ocr-panel h4 { color:#90cdf4!important; font-family:'Playfair Display',serif; margin-top:0; }
.ocr-panel p  { color:var(--muted)!important; font-size:.87rem; margin:0; }

/* ── Estado vacío ────────────────────────────────────────── */
.empty { text-align:center; padding:3.5rem 1rem; color:var(--muted); }
.empty .ico { font-size:3.2rem; display:block; margin-bottom:1rem; }

/* ── Responsive ──────────────────────────────────────────── */
@media (max-width:640px){
  .app-header h1 { font-size:1.7rem!important; }
  .met-num       { font-size:1.5rem; }
  .stButton>button { font-size:1rem!important; padding:.7rem 1.4rem!important; }
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  BASE DE DATOS
# ════════════════════════════════════════════════════════════════════

def _vacio():
    return pd.DataFrame(columns=[
        "id","ley","articulo","texto","dificultad","mnemotecnia","fecha",
        "ultimo_repaso","intervalo_actual","proxima_revision",
        "veces_repasado","veces_fallado","punto_debil",
        "trampas","precision_media",
    ])

def cargar_db():
    if not os.path.exists(DB_FILE):
        return _vacio()
    with open(DB_FILE,"r",encoding="utf-8") as f:
        data = json.load(f)
    if not data:
        return _vacio()
    df = pd.DataFrame(data)
    defaults = {
        "ultimo_repaso":   None,
        "intervalo_actual": 1,
        "proxima_revision": date.today().isoformat(),
        "veces_repasado":   0,
        "veces_fallado":    0,
        "punto_debil":      False,
        "trampas":          "",
        "precision_media":  None,
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
    return df

def guardar_db(df):
    with open(DB_FILE,"w",encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=2)

def agregar_articulo(ley, articulo, texto, dificultad, mnemotecnia, trampas=""):
    df = cargar_db()
    nid = f"{ley.strip()}, Art. {articulo.strip()}"
    if not df.empty and nid in df["id"].values:
        return False, "⚠️ Ya existe ese ID."
    fila = {
        "id": nid, "ley": ley.strip(), "articulo": articulo.strip(),
        "texto": texto.strip(), "dificultad": dificultad,
        "mnemotecnia": mnemotecnia, "trampas": trampas.strip(),
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "ultimo_repaso": None, "intervalo_actual": 1,
        "proxima_revision": date.today().isoformat(),
        "veces_repasado": 0, "veces_fallado": 0,
        "punto_debil": False, "precision_media": None,
    }
    df = pd.concat([df, pd.DataFrame([fila])], ignore_index=True)
    guardar_db(df)
    return True, "✅ Artículo guardado."

def eliminar_articulo(aid):
    df = cargar_db()
    guardar_db(df[df["id"] != aid])

def actualizar_campo(aid, campo, valor):
    df = cargar_db()
    idx = df[df["id"] == aid].index
    if idx.empty:
        return
    df.at[idx[0], campo] = valor
    guardar_db(df)


# ════════════════════════════════════════════════════════════════════
#  ALGORITMO REPASO ESPACIADO + MONITOR INVISIBLE
# ════════════════════════════════════════════════════════════════════

def registrar_repaso(aid: str, resultado: str, precision: float = None):
    """
    resultado: 'bien' | 'regular' | 'mal'
    precision: float 0-100 (del simulador de voz)
    """
    df = cargar_db()
    idx = df[df["id"] == aid].index
    if idx.empty:
        return
    i = idx[0]
    hoy = date.today()

    intervalo = int(df.at[i,"intervalo_actual"] or 1)
    vr = int(df.at[i,"veces_repasado"] or 0)
    vf = int(df.at[i,"veces_fallado"]  or 0)
    prec_prev = df.at[i,"precision_media"]

    # Actualizar precisión media
    if precision is not None:
        prec_prev = float(prec_prev) if prec_prev not in (None,"") else precision
        nueva_prec = round((prec_prev * 0.6) + (precision * 0.4), 1)
        df.at[i,"precision_media"] = nueva_prec
    else:
        nueva_prec = float(prec_prev) if prec_prev not in (None,"") else None

    # Decidir cambio de intervalo
    if resultado == "bien":
        pos = INTERVALOS.index(intervalo) if intervalo in INTERVALOS else 0
        nuevo_int = INTERVALOS[min(pos+1, len(INTERVALOS)-1)]
        vr += 1
        df.at[i,"punto_debil"] = False
    elif resultado == "regular":
        nuevo_int = intervalo
        vr += 1
    else:  # mal
        pos = INTERVALOS.index(intervalo) if intervalo in INTERVALOS else 1
        nuevo_int = INTERVALOS[max(pos-1, 0)]
        vf += 1

    # ── Monitor Invisible ─────────────────────────────────────────
    # Activa Punto Débil si: 2+ fallos O precisión < 50 %
    es_punto_debil = (
        vf >= 2 or
        (nueva_prec is not None and nueva_prec < 50)
    )
    if es_punto_debil:
        df.at[i,"punto_debil"] = True
        df.at[i,"dificultad"]  = "Hueso 🦴"
        nuevo_int = 1                         # repaso mañana forzado
    else:
        df.at[i,"punto_debil"] = bool(df.at[i,"punto_debil"])

    df.at[i,"intervalo_actual"]  = nuevo_int
    df.at[i,"proxima_revision"]  = (hoy + timedelta(days=nuevo_int)).isoformat()
    df.at[i,"ultimo_repaso"]     = hoy.isoformat()
    df.at[i,"veces_repasado"]    = vr
    df.at[i,"veces_fallado"]     = vf
    guardar_db(df)


# ════════════════════════════════════════════════════════════════════
#  ANÁLISIS DE CONCEPTOS CLAVE (motor del simulador de voz)
# ════════════════════════════════════════════════════════════════════

def extraer_conceptos(texto: str, n_max: int = 20):
    """Extrae sustantivos y términos jurídicos relevantes del artículo."""
    palabras = re.findall(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{4,}", texto)
    freq = {}
    for p in palabras:
        pl = p.lower()
        if pl not in STOPWORDS:
            freq[pl] = freq.get(pl, 0) + 1
    # Ordenar por frecuencia, devolver los más importantes
    ordenados = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [p for p, _ in ordenados[:n_max]]

def analizar_recitacion(texto_articulo: str, recitacion: str):
    """
    Devuelve dict con:
      - precision (0-100)
      - detectados: lista de conceptos encontrados
      - omitidos:   lista de conceptos no mencionados
    """
    conceptos = extraer_conceptos(texto_articulo)
    if not conceptos:
        return {"precision": 100, "detectados": [], "omitidos": []}

    rec_lower = recitacion.lower()
    detectados = [c for c in conceptos if c in rec_lower]
    omitidos   = [c for c in conceptos if c not in rec_lower]
    precision  = round(len(detectados) / len(conceptos) * 100)
    return {"precision": precision, "detectados": detectados, "omitidos": omitidos}

def nivel_precision(p: float):
    if p >= 75:
        return "alto",  "#27ae60", "pf-alto",  "🏆 Excelente"
    elif p >= 45:
        return "medio", "#e67e22", "pf-medio", "⚠️ Mejorable"
    else:
        return "bajo",  "#e74c3c", "pf-bajo",  "❌ Punto Débil"


# ════════════════════════════════════════════════════════════════════
#  SELECTOR DE SESIÓN + PRIORIZACIÓN
# ════════════════════════════════════════════════════════════════════

def sesion_articulos(df: pd.DataFrame, minutos: int):
    if df.empty:
        return df
    hoy = date.today().isoformat()

    def score(row):
        s = 0
        prox = str(row.get("proxima_revision") or hoy)
        if prox <= hoy:
            s += 100
        try:
            dias = (date.today() - date.fromisoformat(prox)).days
            s += max(0, dias) * 12
        except Exception:
            pass
        if row.get("punto_debil"):             s += 80
        if row.get("dificultad") == "Hueso 🦴": s += 50
        if not row.get("ultimo_repaso"):        s += 30
        s += int(row.get("veces_fallado") or 0) * 15
        prec = row.get("precision_media")
        if prec not in (None, "") and float(prec) < 50:
            s += 40
        return s

    df = df.copy()
    df["_score"] = df.apply(score, axis=1)
    df = df.sort_values("_score", ascending=False).reset_index(drop=True)

    mpa = 5 if minutos <= 15 else 8
    n   = max(1, minutos // mpa)

    if minutos <= 15:
        prio = df[
            df.get("punto_debil", False) |
            (df["dificultad"] == "Hueso 🦴") |
            (df["_score"] >= 100)
        ].head(n)
        return prio if not prio.empty else df.head(n)
    return df.head(n)

def modo_sesion(min_):
    if min_ <= 15:
        return "urgente", "🚨 Modo Urgente — Solo Huesos y Puntos Débiles"
    elif min_ <= 45:
        return "normal",  "🎯 Modo Estándar — Mezcla equilibrada"
    return "amplio",  "🌊 Modo Completo — Repaso profundo"


# ════════════════════════════════════════════════════════════════════
#  OCR
# ════════════════════════════════════════════════════════════════════

def ocr_imagen(img_bytes: bytes) -> str:
    if not OCR_OK:
        return ""
    img = Image.open(_io.BytesIO(img_bytes)).convert("L")
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    try:
        return pytesseract.image_to_string(img, lang="eng", config="--psm 6").strip()
    except Exception:
        return pytesseract.image_to_string(img, config="--psm 6").strip()


# ════════════════════════════════════════════════════════════════════
#  COMPONENTE WEB SPEECH API  (grabación nativa del navegador)
# ════════════════════════════════════════════════════════════════════

VOICE_COMPONENT = """
<div id="voice-box" style="font-family:Inter,sans-serif;">
  <button id="btn-rec"
    onclick="toggleRec()"
    style="
      width:100%; padding:1rem; font-size:1.1rem; font-weight:600;
      background:linear-gradient(135deg,#0f3460,#1a4fa0);
      color:#e8f4ff; border:none; border-radius:12px; cursor:pointer;
      transition:opacity .2s; margin-bottom:1rem;
    ">
    🎙️ Pulsa para grabar
  </button>
  <div id="status"
    style="font-size:.88rem; color:#7ba3cc; margin-bottom:.7rem; min-height:1.2rem;">
    Esperando…
  </div>
  <textarea id="transcript" rows="6"
    placeholder="La transcripción aparecerá aquí mientras hablas…"
    style="
      width:100%; padding:.9rem; font-size:.95rem; border-radius:10px;
      border:1px solid #bad2ee; background:#f5faff; color:#1a202c;
      resize:vertical; box-sizing:border-box;
    "></textarea>
  <br/><br/>
  <button onclick="enviar()"
    style="
      width:100%; padding:.85rem; font-size:1rem; font-weight:600;
      background:linear-gradient(135deg,#276749,#2f855a);
      color:#fff; border:none; border-radius:12px; cursor:pointer;
    ">
    ✅ Analizar recitación
  </button>
</div>

<script>
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec, recording = false;

function toggleRec(){
  if(!SpeechRec){
    document.getElementById('status').textContent = '⚠️ Tu navegador no soporta reconocimiento de voz. Usa Chrome.';
    return;
  }
  if(recording){
    rec.stop(); return;
  }
  rec = new SpeechRec();
  rec.lang = 'es-ES';
  rec.continuous = true;
  rec.interimResults = true;
  rec.onstart = () => {
    recording = true;
    document.getElementById('btn-rec').textContent = '⏹️ Detener grabación';
    document.getElementById('btn-rec').style.background = 'linear-gradient(135deg,#822727,#c53030)';
    document.getElementById('status').textContent = '🔴 Grabando…';
  };
  rec.onresult = e => {
    let final = '';
    for(let i=e.resultIndex; i<e.results.length; i++){
      if(e.results[i].isFinal) final += e.results[i][0].transcript + ' ';
    }
    if(final) document.getElementById('transcript').value += final;
  };
  rec.onerror = e => {
    document.getElementById('status').textContent = '⚠️ Error: ' + e.error;
  };
  rec.onend = () => {
    recording = false;
    document.getElementById('btn-rec').textContent = '🎙️ Pulsa para grabar';
    document.getElementById('btn-rec').style.background = 'linear-gradient(135deg,#0f3460,#1a4fa0)';
    document.getElementById('status').textContent = '✅ Grabación finalizada. Revisa el texto y pulsa Analizar.';
  };
  rec.start();
}

function enviar(){
  const txt = document.getElementById('transcript').value.trim();
  if(!txt){ alert('No hay texto que analizar. Graba algo primero.'); return; }
  // Comunicar con Streamlit via query param trick
  const url = new URL(window.location.href);
  // Escribir en el input oculto de streamlit usando el parent frame
  try {
    window.parent.postMessage({type:'voice_result', text: txt}, '*');
  } catch(e){}
  // Fallback: copiar al portapapeles + aviso
  navigator.clipboard.writeText(txt).then(()=>{
    document.getElementById('status').textContent =
      '📋 Texto copiado al portapapeles. Pégalo abajo si el análisis no se lanzó automáticamente.';
  }).catch(()=>{
    document.getElementById('status').textContent =
      '✅ Listo. Copia el texto del área de arriba y pégalo en el campo de análisis.';
  });
}
</script>
"""


# ════════════════════════════════════════════════════════════════════
#  HELPERS UI
# ════════════════════════════════════════════════════════════════════

def badge_estado(row):
    hoy = date.today().isoformat()
    prox = str(row.get("proxima_revision") or "")
    if row.get("punto_debil"):
        return '<span class="badge b-debil">🔥 Punto Débil</span>'
    if prox <= hoy and prox:
        return '<span class="badge b-hoy">🔵 Toca hoy</span>'
    if prox > hoy:
        return f'<span class="badge b-ok">📅 {prox}</span>'
    return '<span class="badge b-atrasado">⚠️ Atrasado</span>'

def render_card(row, show_trampas=False):
    dif_cls   = "facil" if str(row.get("dificultad","")) == "Fácil" else "hueso"
    debil_cls = " debil" if row.get("punto_debil") else ""
    bd        = "b-facil" if dif_cls == "facil" else "b-hueso"
    mk        = str(row.get("mnemotecnia","imagen")).split()[0].lower()
    txt_corto = str(row.get("texto",""))[:270] + ("…" if len(str(row.get("texto",""))) > 270 else "")
    vr = int(row.get("veces_repasado") or 0)
    vf = int(row.get("veces_fallado")  or 0)
    prec = row.get("precision_media")
    prec_txt = f"🎙️ Precisión: {prec:.0f}%" if prec not in (None,"") else "🎙️ Sin datos voz"
    int_act  = int(row.get("intervalo_actual") or 1)
    maestro  = '<span class="badge b-maestro">🏆 Maestro</span>' if int_act == 30 else ""

    trampa_html = ""
    if show_trampas and row.get("trampas","").strip():
        trampa_html = f"""
        <div class="trampa-box">
            <h5>🚩 Trampas del examinador</h5>
            <p class="trampa-txt">{row['trampas']}</p>
        </div>"""

    return f"""
    <div class="art-card {dif_cls}{debil_cls}">
        <div class="card-hdr">
            <span class="card-id">{row['id']}</span>
            <span class="badges">
                <span class="badge {bd}">{row.get('dificultad','')}</span>
                <span class="badge b-{mk}">{row.get('mnemotecnia','')}</span>
                {badge_estado(row)}
                {maestro}
            </span>
        </div>
        <p class="card-txt">{txt_corto}</p>
        <div class="card-meta">
            <span>✅ {vr} repasos</span>
            <span>❌ {vf} fallos</span>
            <span>🔄 Cada {int_act}d</span>
            <span>{prec_txt}</span>
        </div>
        {trampa_html}
    </div>"""


# ════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.4rem 0 1rem;
                border-bottom:1px solid rgba(255,255,255,.08);margin-bottom:1rem;">
        <span style="font-family:'Playfair Display',serif;font-size:1.55rem;
                     color:#0dc5e5!important;">📚 OpoMaestro</span>
        <small style="display:block;font-size:.68rem;color:#7ba3cc!important;
                      text-transform:uppercase;letter-spacing:.12em;margin-top:.2rem;">
            Versión Final · IA Jurídica
        </small>
    </div>
    """, unsafe_allow_html=True)

    seccion = st.radio("nav", [
        "⏱️ Sesión de Hoy",
        "🎙️ Simulador de Voz",
        "📥 Cargar Temario",
        "🧳 Mi Baúl de Memoria",
    ], label_visibility="collapsed")

    st.markdown("---")
    _df = cargar_db()
    _hoy = date.today().isoformat()
    _t   = len(_df)
    _ph  = len(_df[_df["proxima_revision"].fillna("") <= _hoy]) if _t else 0
    _hu  = len(_df[_df["dificultad"] == "Hueso 🦴"]) if _t else 0
    _pd  = len(_df[_df["punto_debil"].fillna(False).astype(bool)]) if _t else 0
    _ma  = len(_df[_df["intervalo_actual"].fillna(0).astype(int) == 30]) if _t else 0

    st.markdown(f"""
    <div style="font-size:.76rem;color:#7ba3cc;text-transform:uppercase;
                letter-spacing:.1em;margin-bottom:.55rem;">Estado de hoy</div>
    <div style="display:flex;flex-direction:column;gap:.42rem;">
      <div style="display:flex;justify-content:space-between;padding:.38rem .7rem;
                  background:rgba(13,197,229,.1);border-radius:8px;">
        <span>🔵 Para hoy</span>
        <strong style="color:#0dc5e5!important;">{_ph}</strong>
      </div>
      <div style="display:flex;justify-content:space-between;padding:.38rem .7rem;
                  background:rgba(221,107,32,.15);border-radius:8px;">
        <span style="color:#fbd38d!important;">🔥 Puntos débiles</span>
        <strong style="color:#fbd38d!important;">{_pd}</strong>
      </div>
      <div style="display:flex;justify-content:space-between;padding:.38rem .7rem;
                  background:rgba(229,62,62,.12);border-radius:8px;">
        <span style="color:#fc8181!important;">🦴 Huesos</span>
        <strong style="color:#fc8181!important;">{_hu}</strong>
      </div>
      <div style="display:flex;justify-content:space-between;padding:.38rem .7rem;
                  background:rgba(255,255,255,.05);border-radius:8px;">
        <span>📄 Total</span><strong>{_t}</strong>
      </div>
      <div style="display:flex;justify-content:space-between;padding:.38rem .7rem;
                  background:rgba(22,163,74,.12);border-radius:8px;">
        <span style="color:#6ee7a0!important;">🏆 Maestros</span>
        <strong style="color:#6ee7a0!important;">{_ma}</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  CABECERA
# ════════════════════════════════════════════════════════════════════

hoy_fmt = datetime.now().strftime("%A, %d de %B").capitalize()
st.markdown(f"""
<div class="app-header">
  <div>
    <h1>📚 OpoMaestro</h1>
    <p>Tu academia de IA jurídica · Memoriza · Practica · Aprueba</p>
  </div>
  <span class="header-chip">📅 {hoy_fmt}</span>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  SECCIÓN: SESIÓN DE HOY
# ════════════════════════════════════════════════════════════════════
if seccion == "⏱️ Sesión de Hoy":
    st.markdown('<p class="sec-title">⏱️ Sesión de Hoy</p>', unsafe_allow_html=True)

    # ── Selector de tiempo ──────────────────────────────────────────
    st.markdown("""
    <div style="font-size:.83rem;color:#64748b;text-transform:uppercase;
                letter-spacing:.08em;margin-bottom:.5rem;">
        ¿De cuántos minutos dispones hoy?
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([3,2])
    with c1:
        minutos = st.slider("Tiempo", 5, 120, 30, 5, format="%d min", label_visibility="collapsed")
    with c2:
        p1,p2,p3,p4 = st.columns(4)
        for btn_lbl, btn_val, col in [("⚡10'",10,p1),("🎯30'",30,p2),("📖60'",60,p3),("🌊90'",90,p4)]:
            with col:
                if st.button(btn_lbl, key=f"p_{btn_val}"):
                    minutos = btn_val

    modo, modo_txt = modo_sesion(minutos)
    st.markdown(f'<div class="mode-pill mode-{modo}">{modo_txt}</div>', unsafe_allow_html=True)

    df_all = cargar_db()
    if df_all.empty:
        st.markdown('<div class="empty"><span class="ico">📭</span><p>Sin artículos. Carga tu temario primero.</p></div>', unsafe_allow_html=True)
    else:
        df_ses = sesion_articulos(df_all, minutos)
        n_tot  = len(df_ses)

        if "rep_ses" not in st.session_state:
            st.session_state.rep_ses = set()
        n_hecho = len(st.session_state.rep_ses)
        pct = int(n_hecho/n_tot*100) if n_tot else 0

        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem;">
          <span style="font-size:.85rem;color:#64748b;">Progreso de sesión</span>
          <strong style="color:#2980d4;">{n_hecho}/{n_tot} · {pct}%</strong>
        </div>
        <div class="prog-wrap"><div class="prog-fill" style="width:{pct}%;"></div></div>
        """, unsafe_allow_html=True)

        # Monitor Invisible: alerta
        debiles = df_ses[df_ses["punto_debil"].fillna(False).astype(bool)]
        if not debiles.empty:
            st.markdown(f"""
            <div class="monitor-alert">
              <h5>🕵️ Monitor Invisible — {len(debiles)} Punto(s) Débil(es) detectado(s)</h5>
              <p>Artículos con fallos repetidos o baja precisión vocal. Reprogramados a mañana automáticamente.</p>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"**{n_tot}** artículos seleccionados para **{minutos} min**")
        st.markdown("---")

        for _, row in df_ses.iterrows():
            aid = row["id"]
            hecho = aid in st.session_state.rep_ses
            cc, ca = st.columns([3,1])
            with cc:
                st.markdown(render_card(row), unsafe_allow_html=True)
            with ca:
                st.markdown("<br>", unsafe_allow_html=True)
                if hecho:
                    st.markdown("✅ **Completado**")
                else:
                    r1,r2,r3 = st.columns(3)
                    with r1:
                        if st.button("😊", key=f"b_{aid}", help="Lo sé bien"):
                            registrar_repaso(aid,"bien")
                            st.session_state.rep_ses.add(aid)
                            st.rerun()
                    with r2:
                        if st.button("😐", key=f"r_{aid}", help="Regular"):
                            registrar_repaso(aid,"regular")
                            st.session_state.rep_ses.add(aid)
                            st.rerun()
                    with r3:
                        if st.button("😣", key=f"m_{aid}", help="No lo recuerdo"):
                            registrar_repaso(aid,"mal")
                            st.session_state.rep_ses.add(aid)
                            st.rerun()

        if n_hecho == n_tot and n_tot > 0:
            st.success("🎉 ¡Sesión completada!")
            st.balloons()
            if st.button("🔄 Nueva sesión"):
                st.session_state.rep_ses = set()
                st.rerun()


# ════════════════════════════════════════════════════════════════════
#  SECCIÓN: SIMULADOR DE VOZ
# ════════════════════════════════════════════════════════════════════
elif seccion == "🎙️ Simulador de Voz":
    st.markdown('<p class="sec-title">🎙️ Simulador de Voz</p>', unsafe_allow_html=True)

    df_voz = cargar_db()
    if df_voz.empty:
        st.markdown('<div class="empty"><span class="ico">🎤</span><p>Carga artículos para practicar la recitación.</p></div>', unsafe_allow_html=True)
        st.stop()

    # Selector de artículo
    art_ids = df_voz["id"].tolist()
    sel_id  = st.selectbox("📄 Selecciona el artículo a practicar", art_ids)
    sel_row = df_voz[df_voz["id"] == sel_id].iloc[0]

    col_art, col_info = st.columns([3,2])
    with col_art:
        with st.expander("📖 Ver texto del artículo", expanded=False):
            st.markdown(f"""
            <div style="background:#f5faff;border-radius:10px;padding:1.2rem 1.4rem;
                        border:1px solid #bad2ee;font-size:.95rem;line-height:1.7;color:#1a202c;">
                {sel_row['texto']}
            </div>""", unsafe_allow_html=True)
        if sel_row.get("trampas","").strip():
            st.markdown(f"""
            <div class="trampa-box">
              <h5>🚩 Trampas del examinador</h5>
              <p class="trampa-txt">{sel_row['trampas']}</p>
            </div>""", unsafe_allow_html=True)
    with col_info:
        prec = sel_row.get("precision_media")
        prec_disp = f"{float(prec):.0f}%" if prec not in (None,"") else "Sin datos"
        st.markdown(f"""
        <div style="background:var(--white,#f5faff);border:1px solid #bad2ee;
                    border-radius:12px;padding:1.1rem 1.4rem;">
            <div style="font-size:.75rem;color:#7ba3cc;text-transform:uppercase;letter-spacing:.07em;margin-bottom:.5rem;">Estado del artículo</div>
            <div style="display:flex;flex-direction:column;gap:.4rem;font-size:.9rem;color:#1a202c;">
                <span>🎙️ Precisión media: <strong>{prec_disp}</strong></span>
                <span>✅ Repasos: <strong>{int(sel_row.get('veces_repasado') or 0)}</strong></span>
                <span>❌ Fallos: <strong>{int(sel_row.get('veces_fallado') or 0)}</strong></span>
                <span>🔄 Intervalo: <strong>{int(sel_row.get('intervalo_actual') or 1)} días</strong></span>
                <span>🔥 Punto débil: <strong>{'Sí' if sel_row.get('punto_debil') else 'No'}</strong></span>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Tabs de entrada: Micrófono | Texto escrito ──────────────────
    tab_mic, tab_txt = st.tabs(["🎙️ Grabar con micrófono", "✍️ Recitar por escrito"])

    with tab_mic:
        st.markdown("""
        <div class="voice-panel">
          <h4>🎙️ Grabación de voz</h4>
          <p>Funciona en Chrome y Edge (escritorio y móvil).<br>
             Pulsa el botón, recita el artículo de memoria y detén la grabación.<br>
             Luego copia el texto transcrito al campo de análisis.</p>
        </div>""", unsafe_allow_html=True)

        components.html(VOICE_COMPONENT, height=340)

        st.markdown("""
        <div style="background:#eff6ff;border:1px solid #bee3f8;border-radius:10px;
                    padding:.8rem 1.2rem;margin-top:.5rem;font-size:.88rem;color:#1e40af;">
            <strong>💡 Tip:</strong> Tras grabar, copia el texto transcrito y pégalo 
            en la pestaña <strong>✍️ Recitar por escrito</strong> para analizarlo.
        </div>""", unsafe_allow_html=True)

    with tab_txt:
        recitacion = st.text_area(
            "Escribe o pega aquí tu recitación del artículo de memoria:",
            placeholder="Recita el artículo como si estuvieras en el examen…\n\n(También puedes pegar la transcripción del micrófono.)",
            height=200,
            key="rec_txt",
        )

        if st.button("🔍 Analizar recitación", use_container_width=True, key="btn_analizar"):
            if not recitacion.strip():
                st.warning("⚠️ Escribe o pega tu recitación antes de analizar.")
            else:
                res  = analizar_recitacion(sel_row["texto"], recitacion)
                prec = res["precision"]
                niv, color, pf_cls, niv_txt = nivel_precision(prec)

                # ── Barra de precisión ──────────────────────────────
                st.markdown(f"""
                <div style="margin:.8rem 0 .3rem;font-size:.83rem;color:#64748b;
                            text-transform:uppercase;letter-spacing:.07em;">
                    Precisión jurídica
                </div>
                <div class="precision-bar">
                  <div class="precision-fill {pf_cls}" style="width:{prec}%;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                  <strong style="font-size:2rem;color:{color};">{prec}%</strong>
                  <span style="font-size:1.1rem;font-weight:600;color:{color};">{niv_txt}</span>
                </div>""", unsafe_allow_html=True)

                # ── Conceptos detectados / omitidos ─────────────────
                c_ok, c_er = st.columns(2)
                with c_ok:
                    st.markdown("**✅ Conceptos clave detectados**")
                    if res["detectados"]:
                        st.markdown(
                            "".join(f'<span class="concepto-ok">✅ {c}</span>' for c in res["detectados"]),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown("_Ninguno detectado_")
                with c_er:
                    st.markdown("**❌ Conceptos clave omitidos**")
                    if res["omitidos"]:
                        st.markdown(
                            "".join(f'<span class="concepto-err">❌ {c}</span>' for c in res["omitidos"]),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.success("¡No falta ningún concepto!")

                # ── Monitor Invisible actúa ─────────────────────────
                st.markdown("---")
                if prec < 50:
                    registrar_repaso(sel_id, "mal", precision=prec)
                    st.markdown(f"""
                    <div class="monitor-alert">
                      <h5>🕵️ Monitor Invisible activado</h5>
                      <p>Precisión {prec}% — Este artículo queda marcado como
                         <strong>Punto Débil</strong> y reprogramado para <strong>mañana</strong>.</p>
                    </div>""", unsafe_allow_html=True)
                elif prec < 75:
                    registrar_repaso(sel_id, "regular", precision=prec)
                    st.info(f"💪 {prec}% — Mejorable. El artículo mantiene su intervalo actual.")
                else:
                    registrar_repaso(sel_id, "bien", precision=prec)
                    df_up = cargar_db()
                    nv = int(df_up[df_up["id"]==sel_id]["intervalo_actual"].values[0])
                    st.success(f"🏆 {prec}% — ¡Excelente! Próximo repaso en **{nv} días**.")

                # ── Consejo personalizado ───────────────────────────
                if res["omitidos"]:
                    top3 = ", ".join(res["omitidos"][:3])
                    st.markdown(f"""
                    <div style="background:#eff6ff;border:1px solid #bee3f8;border-radius:10px;
                                padding:.9rem 1.2rem;margin-top:.6rem;font-size:.9rem;color:#1e40af;">
                        <strong>📌 Consejo:</strong> Enfócate en los conceptos 
                        <strong>{top3}</strong>. Crea una imagen mental o historia que 
                        los conecte.
                    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
#  SECCIÓN: CARGAR TEMARIO
# ════════════════════════════════════════════════════════════════════
elif seccion == "📥 Cargar Temario":
    st.markdown('<p class="sec-title">📥 Cargar nuevo artículo</p>', unsafe_allow_html=True)

    tab_man, tab_ocr = st.tabs(["✍️ Manual", "📸 OCR desde imagen"])

    with tab_man:
        c1,c2 = st.columns([2,1])
        with c1:
            ley = st.text_input("Nombre de la Ley", placeholder="Ej: Ley 39/2015, CE Art. 14…")
        with c2:
            art = st.text_input("Número de Artículo", placeholder="Ej: 1, 23-bis…")

        texto = st.text_area("Texto del artículo", placeholder="Pega el artículo completo…", height=190, key="txt_man")

        c3,c4 = st.columns(2)
        with c3:
            dif = st.selectbox("Dificultad", ["Fácil","Hueso 🦴"])
        with c4:
            mn  = st.selectbox("Mnemotecnia", ["Imagen 🖼️","Gancho 🎣","Historia 📖"])

        trampas = st.text_area(
            "🚩 Trampas del examinador (opcional)",
            placeholder="Ej: Confunde el plazo de 10 días con 15. El artículo 47 dice 'podrá', no 'deberá'…",
            height=90,
            key="trampas_man",
        )

        if st.button("💾 Guardar artículo", use_container_width=True, key="btn_man"):
            if not ley or not art or not texto:
                st.error("⚠️ Rellena ley, artículo y texto.")
            else:
                ok, msg = agregar_articulo(ley, art, texto, dif, mn, trampas)
                (st.success(msg) if ok else st.warning(msg))
                if ok: st.balloons()

        if ley or art or texto:
            st.markdown("---")
            st.markdown("#### 👁️ Previsualización")
            _dc = "facil" if dif == "Fácil" else "hueso"
            _bd = "b-facil" if _dc == "facil" else "b-hueso"
            _mk = mn.split()[0].lower()
            st.markdown(f"""
            <div class="art-card {_dc}">
              <div class="card-hdr">
                <span class="card-id">{ley or '…'}, Art. {art or '…'}</span>
                <span class="badges">
                  <span class="badge {_bd}">{dif}</span>
                  <span class="badge b-{_mk}">{mn}</span>
                </span>
              </div>
              <p class="card-txt">{texto or '<em>Sin texto aún…</em>'}</p>
              {'<div class="trampa-box"><h5>🚩 Trampas del examinador</h5><p class="trampa-txt">'+trampas+'</p></div>' if trampas.strip() else ''}
            </div>""", unsafe_allow_html=True)

    with tab_ocr:
        st.markdown("""
        <div class="ocr-panel">
          <h4>📸 Lector OCR de imágenes</h4>
          <p>Sube una foto de tu libro o apuntes. Funciona mejor con imágenes nítidas y bien iluminadas.</p>
        </div>""", unsafe_allow_html=True)

        if not OCR_OK:
            st.warning("⚠️ pytesseract no disponible. Instala: `pip install pytesseract Pillow`")
        else:
            img_f = st.file_uploader("Imagen (JPG, PNG, WEBP…)", type=["jpg","jpeg","png","webp","bmp"], label_visibility="collapsed")
            if img_f:
                ci, ct = st.columns([1,1])
                with ci:
                    st.image(img_f, caption="Imagen original", use_container_width=True)
                with ct:
                    with st.spinner("🔍 Extrayendo texto…"):
                        txt_ocr = ocr_imagen(img_f.read())
                    if txt_ocr:
                        st.success(f"✅ {len(txt_ocr)} caracteres extraídos")
                        txt_ed = st.text_area("Texto extraído (edítalo si hay errores)", value=txt_ocr, height=220, key="txt_ocr")
                    else:
                        st.warning("Sin texto detectado. Prueba con imagen más nítida.")
                        txt_ed = ""

                if txt_ocr:
                    st.markdown("---")
                    oo1,oo2 = st.columns([2,1])
                    with oo1: ley_o = st.text_input("Ley", key="ley_o")
                    with oo2: art_o = st.text_input("Art.", key="art_o")
                    od1,od2 = st.columns(2)
                    with od1: dif_o = st.selectbox("Dificultad", ["Fácil","Hueso 🦴"], key="dif_o")
                    with od2: mn_o  = st.selectbox("Mnemotecnia", ["Imagen 🖼️","Gancho 🎣","Historia 📖"], key="mn_o")
                    trap_o = st.text_area("🚩 Trampas (opcional)", key="trap_o", height=80)
                    if st.button("💾 Guardar desde OCR", use_container_width=True, key="btn_ocr"):
                        if not ley_o or not art_o or not txt_ed:
                            st.error("⚠️ Completa ley, artículo y texto.")
                        else:
                            ok, msg = agregar_articulo(ley_o, art_o, txt_ed, dif_o, mn_o, trap_o)
                            (st.success(msg) if ok else st.warning(msg))
                            if ok: st.balloons()


# ════════════════════════════════════════════════════════════════════
#  SECCIÓN: MI BAÚL DE MEMORIA
# ════════════════════════════════════════════════════════════════════
elif seccion == "🧳 Mi Baúl de Memoria":
    st.markdown('<p class="sec-title">🧳 Mi Baúl de Memoria</p>', unsafe_allow_html=True)

    df = cargar_db()
    if df.empty:
        st.markdown('<div class="empty"><span class="ico">🗄️</span><p>Tu baúl está vacío. Carga tu primer artículo.</p></div>', unsafe_allow_html=True)
        st.stop()

    hoy_iso  = date.today().isoformat()
    t        = len(df)
    n_hoy    = len(df[df["proxima_revision"].fillna("") <= hoy_iso])
    n_facil  = len(df[df["dificultad"] == "Fácil"])
    n_hueso  = len(df[df["dificultad"] == "Hueso 🦴"])
    n_debil  = len(df[df["punto_debil"].fillna(False).astype(bool)])
    n_leyes  = df["ley"].nunique()

    st.markdown(f"""
    <div class="met-row">
      <div class="met-box"><span class="met-num">{t}</span><span class="met-lbl">Total</span></div>
      <div class="met-box"><span class="met-num" style="color:#2980d4;">{n_hoy}</span><span class="met-lbl">Para hoy</span></div>
      <div class="met-box"><span class="met-num" style="color:#276749;">{n_facil}</span><span class="met-lbl">Fáciles</span></div>
      <div class="met-box"><span class="met-num" style="color:#c53030;">{n_hueso}</span><span class="met-lbl">Huesos 🦴</span></div>
      <div class="met-box"><span class="met-num" style="color:#dd6b20;">{n_debil}</span><span class="met-lbl">Débiles 🔥</span></div>
      <div class="met-box"><span class="met-num" style="color:#553c9a;">{n_leyes}</span><span class="met-lbl">Leyes</span></div>
    </div>""", unsafe_allow_html=True)

    # ── Filtros ──────────────────────────────────────────────────────
    ff1,ff2,ff3,ff4 = st.columns([3,1,1,1])
    with ff1: buscar   = st.text_input("🔍 Buscar", placeholder="Ley, artículo, texto…")
    with ff2: f_dif    = st.selectbox("Dificultad", ["Todas","Fácil","Hueso 🦴"])
    with ff3: f_mn     = st.selectbox("Mnemotecnia", ["Todas","Imagen 🖼️","Gancho 🎣","Historia 📖"])
    with ff4: f_estado = st.selectbox("Estado", ["Todos","Para hoy","Punto Débil","Maestros"])

    df_f = df.copy()
    if buscar:
        m = (
            df_f["ley"].str.contains(buscar, case=False, na=False) |
            df_f["texto"].str.contains(buscar, case=False, na=False) |
            df_f["id"].str.contains(buscar, case=False, na=False)
        )
        df_f = df_f[m]
    if f_dif != "Todas":
        df_f = df_f[df_f["dificultad"] == f_dif]
    if f_mn != "Todas":
        df_f = df_f[df_f["mnemotecnia"] == f_mn]
    if f_estado == "Para hoy":
        df_f = df_f[df_f["proxima_revision"].fillna("") <= hoy_iso]
    elif f_estado == "Punto Débil":
        df_f = df_f[df_f["punto_debil"].fillna(False).astype(bool)]
    elif f_estado == "Maestros":
        df_f = df_f[df_f["intervalo_actual"].fillna(0).astype(int) == 30]

    st.caption(f"**{len(df_f)}** artículo(s) mostrado(s)")

    vista = st.radio("Vista", ["🃏 Tarjetas","📊 Tabla"], horizontal=True)

    if vista == "🃏 Tarjetas":
        show_trampas = st.checkbox("🚩 Mostrar trampas del examinador en las tarjetas", value=True)
        for _, row in df_f.iterrows():
            aid = row["id"]
            cc, ca = st.columns([11,1])
            with cc:
                st.markdown(render_card(row, show_trampas=show_trampas), unsafe_allow_html=True)
            with ca:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{aid}", help="Eliminar"):
                    eliminar_articulo(aid)
                    st.rerun()
    else:
        cols_t = ["id","ley","articulo","dificultad","mnemotecnia",
                  "proxima_revision","precision_media","veces_repasado","veces_fallado","punto_debil"]
        cols_t = [c for c in cols_t if c in df_f.columns]
        st.dataframe(
            df_f[cols_t].rename(columns={
                "id":"ID","ley":"Ley","articulo":"Art.","dificultad":"Dificultad",
                "mnemotecnia":"Mnemotecnia","proxima_revision":"Próx. revisión",
                "precision_media":"Precisión %","veces_repasado":"Repasos",
                "veces_fallado":"Fallos","punto_debil":"Punto Débil",
            }),
            use_container_width=True, hide_index=True,
        )
        csv = df_f.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV", data=csv, file_name="temario_final.csv", mime="text/csv")

    # ── Editar trampas inline ────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### ✏️ Editar trampas de un artículo")
    ed_ids = df["id"].tolist()
    ed_sel = st.selectbox("Artículo a editar", ed_ids, key="ed_sel")
    ed_row = df[df["id"] == ed_sel].iloc[0]
    nueva_trampa = st.text_area(
        "🚩 Trampas del examinador",
        value=str(ed_row.get("trampas","") or ""),
        height=100,
        key="ed_trampa",
    )
    if st.button("💾 Guardar trampas", key="btn_ed_trampa"):
        actualizar_campo(ed_sel, "trampas", nueva_trampa)
        st.success("✅ Trampas actualizadas.")
        st.rerun()
