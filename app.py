import base64
import pathlib
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st

import engine as eng
from data import ARCHIVOS_ESCUDOS, CABEZAS_DE_SERIE, FIXTURE_CUADRANGULARES, GRUPOS, PTS_FASE_REGULAR, RATINGS_INICIALES

# Imagen del título: guarda un archivo "trofeo.png" (o .jpg/.webp/.svg) junto a app.py
_MIME_TROFEO = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}
_TROFEO = next((p for e in _MIME_TROFEO if (p := pathlib.Path(__file__).parent / f"trofeo{e}").exists()), None)

st.set_page_config(page_title="Simulador de Cuadrangulares 2026-II", page_icon=str(_TROFEO) if _TROFEO else "⚽", layout="wide")
if _TROFEO:
    _src = f"data:{_MIME_TROFEO[_TROFEO.suffix]};base64,{base64.b64encode(_TROFEO.read_bytes()).decode()}"
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:16px;margin-bottom:8px">'
        f'<img src="{_src}" style="height:72px;object-fit:contain">'
        f'<h1 style="margin:0;padding:0">Simulador de Cuadrangulares 2026-II</h1></div>',
        unsafe_allow_html=True,
    )
else:
    st.title("⚽ Simulador de Cuadrangulares 2026-II")


# ---------------- Estilos (incluye vista de celular) ----------------
st.markdown(
    """
<style>
.eq { text-align:center; line-height:1.15; }
.eq-escudo { height:46px; max-width:60px; object-fit:contain; display:inline-block; }
.eq-nombre { font-weight:700; font-size:.95rem; margin-top:4px; }

/* Solo las filas INTERNAS de cada partido (marcador y botones) no se apilan en celular.
   Las columnas Grupo A | Grupo B sí se apilan: 1 partido por fila en celular, 2x2 en computador. */
div[data-testid="stHorizontalBlock"]:has([class*="st-key-gl_"]):not(:has(div[data-testid="stHorizontalBlock"])),
div[data-testid="stHorizontalBlock"]:has([class*="st-key-b_Local_"]):not(:has(div[data-testid="stHorizontalBlock"])) {
    flex-wrap: nowrap !important;
    gap: .5rem !important;
}
div[data-testid="stHorizontalBlock"]:has([class*="st-key-gl_"]):not(:has(div[data-testid="stHorizontalBlock"])) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has([class*="st-key-b_Local_"]):not(:has(div[data-testid="stHorizontalBlock"])) > div[data-testid="stColumn"] {
    min-width: 0 !important;
}

@media (max-width: 640px) {
    .block-container { padding-left: .8rem !important; padding-right: .8rem !important; }
    .eq-escudo { height:42px; max-width:52px; }
    .eq-nombre { font-size:.82rem; }
    [class*="st-key-gl_"] [data-testid="stNumberInputStepUp"],
    [class*="st-key-gl_"] [data-testid="stNumberInputStepDown"],
    [class*="st-key-gv_"] [data-testid="stNumberInputStepUp"],
    [class*="st-key-gv_"] [data-testid="stNumberInputStepDown"] { display:none; }
    [class*="st-key-gl_"] input, [class*="st-key-gv_"] input { text-align:center; padding-left:.2rem; padding-right:.2rem; }
    [class*="st-key-b_"] button { padding:.35rem .2rem; font-size:.8rem; min-height:0; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Sidebar: ratings y semilla ----------------
st.sidebar.header("⚙️ Configuración")
seed = st.sidebar.number_input("Semilla (0 = aleatoria)", min_value=0, value=0, step=1)
st.sidebar.subheader("Ratings de los equipos")
if "ratings" not in st.session_state:
    st.session_state.ratings = pd.DataFrame({"Equipo": list(RATINGS_INICIALES), "Elo": list(RATINGS_INICIALES.values())})
ed = st.sidebar.data_editor(st.session_state.ratings, hide_index=True, width="stretch", disabled=["Equipo"], height=600)
ELO = dict(zip(ed["Equipo"], ed["Elo"].astype(float)))
SEMILLAS = set(CABEZAS_DE_SERIE)  # tienen el "punto invisible"
if st.sidebar.button("Restablecer ratings"):
    del st.session_state["ratings"]
    st.rerun()



# ---------------- Escudos ----------------
CARPETA_ESCUDOS = pathlib.Path(__file__).parent / "escudos"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".svg": "image/svg+xml"}


def _slug(texto):
    return unicodedata.normalize("NFD", str(texto).lower()).encode("ascii", "ignore").decode().replace(" ", "_")


@st.cache_data
def escudo(equipo):
    """Devuelve el escudo como data-URI, o None si no hay archivo para ese equipo."""
    for nombre in [_slug(equipo), *ARCHIVOS_ESCUDOS.get(equipo, [])]:
        for ext, mime in MIME.items():
            ruta = CARPETA_ESCUDOS / f"{nombre}{ext}"
            if ruta.exists():
                return f"data:{mime};base64,{base64.b64encode(ruta.read_bytes()).decode()}"
    return None


def con_escudos(df):
    df = df.copy()
    if "Equipo" in df.columns and "Escudo" not in df.columns:
        df.insert(df.columns.get_loc("Equipo"), "Escudo", df["Equipo"].map(escudo))
    return df


def tabla_ui(df, caja=st, **kw):
    """Como st.dataframe, pero con columna de escudo. `caja` = st o una columna (c1, c2...)."""
    if isinstance(df, pd.DataFrame):
        if "Equipo" not in df.columns and df.index.dtype == object:
            df = df.rename_axis("Equipo").reset_index()
        df = con_escudos(df)
        kw.setdefault("hide_index", "Equipo" in df.columns)
    else:  # Styler (ya trae escudos agregados)
        kw.setdefault("hide_index", True)
    return caja.dataframe(df, column_config={"Escudo": st.column_config.ImageColumn("", width="small")}, width="stretch", **kw)


def get_rng():
    return np.random.default_rng(seed or None)


def mostrar_final(res):
    f = res["final"]
    (l1, g1, g2, v1), (l2, g3, g4, v2) = f["ida"], f["vuelta"]
    c1, c2 = st.columns(2)
    c1.metric("Final · Ida", f"{l1} {g1} - {g2} {v1}")
    c2.metric("Final · Vuelta", f"{l2} {g3} - {g4} {v2}")
    txt = f"Global: {f['global'][0]}-{f['global'][1]}" + (f" · definió por penales: **{f['penales']}**" if f["penales"] else "")
    st.caption(txt)
    st.success(f"🏆 Campeón: **{res['campeon']}**")


# ---------------- Cuadrangulares 2026-II ----------------

def equipo_html(nombre):
    src = escudo(nombre)
    img = f'<img class="eq-escudo" src="{src}">' if src else '<div class="eq-escudo"></div>'
    return f'<div class="eq">{img}<div class="eq-nombre">{nombre}</div></div>'


def fijar(i, goles_l, goles_v):
    """Callback de los botones: escribe el marcador en las casillas del partido i."""
    st.session_state[f"gl_{i}"] = goles_l
    st.session_state[f"gv_{i}"] = goles_v

def botones_resultado(i, gl, gv):
    res = None if gl is None or gv is None else ("Local" if gl > gv else "Visitante" if gv > gl else "Empate")
    opciones = {"Local": (1, 0), "Empate": (1, 1), "Visitante": (0, 1)}
    cols = st.columns([1, 1, 1, 0.45])
    for col, (nombre, (a_, b_)) in zip(cols, opciones.items()):
        col.button(nombre, key=f"b_{nombre}_{i}", width="stretch", on_click=fijar, args=(i, a_, b_),
                   type="primary" if res == nombre else "secondary")
    cols[3].button("↺", key=f"b_clear_{i}", width="stretch", on_click=fijar, args=(i, None, None), help="Limpiar marcador")

resultados = {}  # índice del partido -> (gl, gv)
tabs_fecha = st.tabs([f"Fecha {n}" for n in range(1, 7)])
for n, tf in enumerate(tabs_fecha, start=1):
    with tf:
        cols_grupo = st.columns(2)
        for col, g in zip(cols_grupo, GRUPOS):
            with col:
                for i, (fecha, grupo, loc, vis) in enumerate(FIXTURE_CUADRANGULARES):
                    if fecha != n or grupo != g:
                        continue
                    with st.container(border=True):
                        st.markdown(f"<div style='text-align:center;opacity:.7;font-size:.85rem'>Fecha {fecha} · Grupo {grupo}</div>", unsafe_allow_html=True)
                        c_l, c_gl, c_sep, c_gv, c_v = st.columns([2.2, 1.5, 0.3, 1.5, 2.2], vertical_alignment="center")
                        c_l.markdown(equipo_html(loc), unsafe_allow_html=True)
                        gl = c_gl.number_input("Goles local", min_value=0, max_value=20, value=None, step=1, placeholder="-", key=f"gl_{i}", label_visibility="collapsed")
                        c_sep.markdown("<div style='text-align:center;font-size:1.4rem'>:</div>", unsafe_allow_html=True)
                        gv = c_gv.number_input("Goles visitante", min_value=0, max_value=20, value=None, step=1, placeholder="-", key=f"gv_{i}", label_visibility="collapsed")
                        c_v.markdown(equipo_html(vis), unsafe_allow_html=True)
                        botones_resultado(i, gl, gv)
                    resultados[i] = (gl, gv)

def partidos(grupo):
    out = []
    for i, (fecha, g, loc, vis) in enumerate(FIXTURE_CUADRANGULARES):
        if g == grupo:
            gl, gv = resultados[i]
            out.append((loc, vis, gl, gv))
    return out

GP = {g: partidos(g) for g in GRUPOS}
jugados = sum(1 for p in GP.values() for m in p if m[2] is not None and m[3] is not None)
st.progress(jugados / 24, text=f"{jugados}/24 partidos jugados")

# --- Simulación: se guarda junto con los marcadores con los que se hizo ---
firma = repr(GP)
c1, c2 = st.columns(2)
if c1.button("▶️ Simular lo que falta", type="primary", width="stretch"):
    st.session_state.una = (firma, eng.fase_final(get_rng(), ELO, GP, SEMILLAS, PTS_FASE_REGULAR))
if c2.button("↩️ Ver tabla con resultados reales", width="stretch"):
    st.session_state.pop("una", None)

una = st.session_state.get("una")
sim = una[1] if una and una[0] == firma else None  # si cambias un marcador, la simulación vieja se descarta

# --- Tablas: reales, o proyectadas si se simuló ---
st.subheader("Tabla proyectada (simulación)" if sim else "Tabla actual")
st.caption(f"Punto invisible: {' y '.join(CABEZAS_DE_SERIE)} (cabezas de serie) ganan el desempate si igualan en puntos en el 1.er lugar de su grupo.")
cols = st.columns(2)
for c, g in zip(cols, GRUPOS):
    if sim:
        tab, orden = sim["tablas"][g]
    else:
        tab = eng.tabla(GP[g])
        orden = sorted(tab, key=lambda t: (tab[t]["PTS"] + (0.5 if t in SEMILLAS else 0), tab[t]["GF"] - tab[t]["GC"], tab[t]["GF"]), reverse=True)
    c.markdown(f"**Grupo {g}**")
    tabla_ui(eng.a_df(tab, orden), caja=c)

if sim:
    st.caption("Los partidos que faltaban fueron simulados; los que ya tienen marcador se respetan.")
    st.subheader("Final")
    mostrar_final(sim)
