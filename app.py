"""
Menú del día – Cafetería CC
Pantalla para TV de 80" (incluye Android TV: RCA, TCL…) y vista para celulares.

Uso:
  Misma dirección para todos: https://menu-cafeteria-cc.streamlit.app/
  La app mira la PANTALLA del equipo: horizontal y grande = TV; vertical = celular.
  Forzar vista:   ?vista=tv   o   ?vista=celular   (recomendado guardar en la TV: ?vista=tv)
  Control de platos (agotado/disponible): ?admin=1  (clave en Settings → Secrets: CLAVE_ADMIN)
  Probar otro día: ?fecha=2026-10-19   (se puede combinar: ?fecha=2026-10-19&vista=celular)
  TV lenta:       ?calidad=1080

Cada día se agrega una carpeta en  menus/AAAA-MM-DD/  con:
  tv.html       menú VECTORIAL animado para TV (se dibuja en vivo, nitidez total)
  celular.html  menú VECTORIAL animado para celulares
  celular.png   imagen vertical en alta resolución (para descargar)
  (Si una carpeta antigua solo tiene tv_4k.mp4 / tv_1080.mp4 / celular.mp4, se usan esos.)
  *.mp3         (opcional) canciones solo para ese día
Música: TODOS los .mp3 de menus/ suenan en orden alfabético y se repiten sin fin.
  (Si la carpeta del día tiene sus propios .mp3, se usan esos ese día.)
La app muestra sola el menú de HOY (hora de Ecuador). Si aún no se subió,
muestra el último menú disponible. Video y música se repiten sin parar.
"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_js_eval import streamlit_js_eval
import re
import threading

PLATOS = [("sopa", "Sopa"), ("seco1", "Seco opción 1"), ("seco2", "Seco opción 2"), ("dieta", "Dieta")]


@st.cache_resource
def estado_compartido():
    """Estado de 'agotado' compartido por TODOS los equipos conectados (memoria del servidor)."""
    return {"fecha": None, "agotados": set(), "lock": threading.Lock()}


def agotados_de(fecha):
    e = estado_compartido()
    with e["lock"]:
        if e["fecha"] != fecha:          # cada día nuevo empieza con todo DISPONIBLE
            e["fecha"], e["agotados"] = fecha, set()
        return set(e["agotados"])


def marcar_plato(fecha, plato, agotado):
    e = estado_compartido()
    with e["lock"]:
        if e["fecha"] != fecha:
            e["fecha"], e["agotados"] = fecha, set()
        (e["agotados"].add if agotado else e["agotados"].discard)(plato)

ZONA = ZoneInfo("America/Guayaquil")
CARPETA_MENUS = Path(__file__).parent / "menus"
WHATSAPP = "https://wa.me/593968515340"
PLATAFORMA = "https://comedor.itb.edu.ec/login"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FONDO = "#0B0B0E"

st.set_page_config(page_title="Menú del día – Cafetería CC", page_icon="☕",
                   layout="wide", initial_sidebar_state="collapsed")

# Estilos base: pantalla completa, sin barras de Streamlit.
st.markdown(f"""
<style>
  header[data-testid="stHeader"], footer, #MainMenu,
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"], [data-testid="stSidebar"] {{ display: none !important; }}
  html, body, .stApp, [data-testid="stAppViewContainer"] {{ background: {FONDO} !important; }}
  .block-container {{ padding: 0 !important; max-width: 100% !important; }}
  [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
  iframe[title="streamlit_autorefresh.st_autorefresh"],
  iframe[title="streamlit_js_eval.streamlit_js_eval"] {{ display: none; }}
  [data-testid="stElementContainer"]:has(iframe[title^="streamlit_"]) {{ display: none; }}
  [data-testid="stAudio"], audio {{ position: fixed !important; width: 1px !important; height: 1px !important;
       opacity: 0 !important; pointer-events: none !important; bottom: 0; left: 0; }}
  .aviso {{ color: #F7C948; font-family: sans-serif; text-align: center; padding: 40vh 4vw 0;
           font-size: 3.2vw; font-weight: 700; }}
  .botones {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; padding: 16px; }}
  .botones a {{ text-decoration: none; font-family: sans-serif; font-weight: 800; font-size: 18px;
               padding: 14px 22px; border-radius: 14px; border: 3px solid #fff; color: #fff; }}
  .wa {{ background: #1E9E4A; }}  .pl {{ background: #C8102E; }}
</style>
""", unsafe_allow_html=True)

# ---------- ¿TV o celular? ----------
# Las TV Android (RCA, TCL…) se presentan como "celular" en su navegador, por eso no
# se puede confiar en ese dato. Se mira la pantalla: horizontal y de al menos 500 px
# de alto = TV o computadora; vertical o pequeña = celular.
params = st.query_params
vista = params.get("vista", "").lower()
if "admin" in params:
    vista = "admin"
elif vista not in ("tv", "celular"):
    if "vista_detectada" not in st.session_state:
        pantalla = streamlit_js_eval(js_expressions="[screen.width, screen.height]", key="pantalla")
        if not pantalla:
            st.markdown('<div class="aviso">☕ Cargando el menú del día…</div>', unsafe_allow_html=True)
            st.stop()
        sw, sh = float(pantalla[0] or 0), float(pantalla[1] or 0)
        es_tv = sw > sh and min(sw, sh) >= 500
        st.session_state.vista_detectada = "tv" if es_tv else "celular"
    vista = st.session_state.vista_detectada
calidad = params.get("calidad", "4k").lower()

# Revisa cada 10 minutos si hay un menú nuevo (por ejemplo, al cambiar el día).
st_autorefresh(interval=10 * 60 * 1000, key="refresco")

if vista == "tv":
    st.markdown("""<style>
      [data-testid="stVideo"], video { width: 100vw !important; height: 100vh !important;
         max-height: 100vh !important; object-fit: contain; background: #0B0B0E; display: block; }
      .stApp { overflow: hidden; }
      video::-webkit-media-controls, video::-webkit-media-controls-panel { display: none !important; }
    </style>""", unsafe_allow_html=True)


def fecha_larga(d):
    return f"{DIAS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_de_hoy():
    """Hoy en Ecuador. Para PROBAR otro día se puede simular la fecha con
    ?fecha=AAAA-MM-DD en la dirección (ej. ?fecha=2026-10-19)."""
    simulada = params.get("fecha", "")
    if simulada:
        try:
            return datetime.strptime(simulada, "%Y-%m-%d").date()
        except ValueError:
            pass
    return datetime.now(ZONA).date()


def buscar_menu():
    """Devuelve (carpeta, fecha, es_de_hoy) del menú de hoy o el último disponible."""
    hoy = fecha_de_hoy()
    if not CARPETA_MENUS.exists():
        return None, None, False
    fechas = []
    for c in CARPETA_MENUS.iterdir():
        if not c.is_dir():
            continue
        try:
            fechas.append((datetime.strptime(c.name, "%Y-%m-%d").date(), c))
        except ValueError:
            continue
    validas = sorted([f for f in fechas if f[0] <= hoy], reverse=True)
    if not validas:
        return None, None, False
    fecha, carpeta = validas[0]
    return carpeta, fecha, fecha == hoy


carpeta, fecha, es_hoy = buscar_menu()


def nombres_platos(carpeta):
    """Nombres de los 4 platos tomados del menú del día (para la página de control)."""
    for nombre in ("tv.html", "celular.html"):
        archivo = carpeta / nombre
        if archivo.exists():
            encontrados = re.findall(r'color: #16110D; text-transform: uppercase">([^<]+)</div>', archivo.read_text(encoding="utf-8"))
            if len(encontrados) >= 4:
                return encontrados[:4]
    return [etiqueta for _, etiqueta in PLATOS]


def imagenes_menu(carpeta):
    """Logo y fotos de los platos tomados del menú del día (para mostrarlos en el panel)."""
    archivo = carpeta / "tv.html"
    if not archivo.exists():
        archivo = carpeta / "celular.html"
    if not archivo.exists():
        return {}
    return {alt: src for src, alt in re.findall(r'<img src="(data:image/[^"]+)" alt="([^"]*)"', archivo.read_text(encoding="utf-8"))}


def pagina_control():
    imgs = imagenes_menu(carpeta) if carpeta else {}
    logo = imgs.get("Logo Coffee and CC", "")
    st.markdown("""<style>
      @import url('https://fonts.googleapis.com/css2?family=Anton&family=Barlow+Condensed:wght@600;700;800&display=swap');
      html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: radial-gradient(1200px 600px at 10% -10%, #3B1466 0%, transparent 60%),
                    radial-gradient(900px 500px at 110% 10%, #7A0F2E 0%, transparent 55%), #0B0B0E !important; }
      .block-container { padding: 18px 14px 70px !important; max-width: 640px !important; margin: 0 auto; }
      [data-testid="stVerticalBlock"] { gap: 10px !important; }
      [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 10px !important; }
      [data-testid="stHorizontalBlock"] > div { min-width: 0 !important; flex: 1 1 0 !important; }
      .cc-cab { display: flex; align-items: center; gap: 14px; padding: 14px; border-radius: 22px;
        background: linear-gradient(135deg, rgba(247,201,72,.16), rgba(255,255,255,.04));
        border: 1px solid rgba(247,201,72,.45); box-shadow: 0 10px 30px rgba(0,0,0,.35); }
      .cc-cab img { width: 92px; border-radius: 12px; box-shadow: 0 0 0 3px #0B0B0E, 0 0 0 5px #D4A62A; }
      .cc-cab h1 { font-family: Anton, Impact, sans-serif; font-size: 30px; line-height: 1; margin: 0; color: #FFFFFF; letter-spacing: 1px; }
      .cc-cab p { margin: 4px 0 0; font-family: 'Barlow Condensed', sans-serif; font-size: 18px; color: #F7C948; font-weight: 700; }
      .cc-resumen { display: flex; gap: 8px; margin: 6px 0 2px; }
      .cc-pill { flex: 1; text-align: center; font-family: 'Barlow Condensed', sans-serif; font-weight: 800; font-size: 18px;
        padding: 8px; border-radius: 999px; color: #FFFFFF; }
      .cc-pill.v { background: rgba(47,180,87,.18); border: 1px solid #2FB457; }
      .cc-pill.r { background: rgba(255,59,78,.16); border: 1px solid #FF3B4E; }
      .cc-card { display: flex; align-items: center; gap: 14px; padding: 14px; border-radius: 22px; margin-top: 10px;
        background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.12); box-shadow: 0 8px 24px rgba(0,0,0,.35); }
      .cc-card.agot { background: linear-gradient(135deg, rgba(208,2,27,.28), rgba(255,255,255,.03)); border-color: rgba(255,59,78,.7); }
      .cc-card img { width: 78px; height: 78px; border-radius: 50%; object-fit: cover; flex: 0 0 auto;
        border: 4px solid #2FB457; box-shadow: 0 0 18px rgba(47,180,87,.45); }
      .cc-card.agot img { border-color: #FF3B4E; box-shadow: 0 0 18px rgba(255,59,78,.55); filter: grayscale(.45); }
      .cc-tag { font-family: 'Barlow Condensed', sans-serif; font-size: 14px; font-weight: 800; letter-spacing: 3px; color: #F7C948; text-transform: uppercase; }
      .cc-nom { font-family: 'Barlow Condensed', sans-serif; font-size: 22px; font-weight: 800; color: #FFFFFF; line-height: 1.05; margin: 2px 0 6px; }
      .cc-est { display: inline-flex; align-items: center; gap: 8px; font-family: 'Barlow Condensed', sans-serif; font-weight: 800;
        font-size: 15px; letter-spacing: 2px; padding: 4px 12px; border-radius: 999px; }
      .cc-est.v { color: #7CF0A0; background: rgba(47,180,87,.18); }
      .cc-est.r { color: #FF8A95; background: rgba(255,59,78,.18); }
      .cc-pto { width: 10px; height: 10px; border-radius: 50%; animation: ccPto 1.2s ease-in-out infinite; }
      .cc-est.v .cc-pto { background: #2FB457; box-shadow: 0 0 10px #2FB457; }
      .cc-est.r .cc-pto { background: #FF3B4E; box-shadow: 0 0 10px #FF3B4E; }
      @keyframes ccPto { 50% { transform: scale(.6); opacity: .5; } }
      div.stButton > button { width: 100%; min-height: 58px; border-radius: 16px; font-family: 'Barlow Condensed', sans-serif;
        font-size: 19px; font-weight: 800; letter-spacing: 1px; transition: transform .12s ease, box-shadow .2s ease; }
      div.stButton > button:active { transform: scale(.97); }
      .cc-nota { text-align: center; font-family: 'Barlow Condensed', sans-serif; color: rgba(255,255,255,.65); font-size: 15px; margin-top: 14px; }
      .cc-login { text-align: center; padding: 26px 18px 10px; border-radius: 24px; margin-top: 30px;
        background: linear-gradient(160deg, rgba(247,201,72,.14), rgba(255,255,255,.03)); border: 1px solid rgba(247,201,72,.45); }
      .cc-login img { width: 150px; border-radius: 16px; box-shadow: 0 0 0 3px #0B0B0E, 0 0 0 6px #D4A62A, 0 0 30px rgba(247,201,72,.4); }
      .cc-login h2 { font-family: Anton, Impact, sans-serif; color: #FFFFFF; font-size: 30px; margin: 16px 0 4px; letter-spacing: 1px; }
      .cc-login p { font-family: 'Barlow Condensed', sans-serif; color: #F7C948; font-size: 18px; font-weight: 700; margin: 0; }
      [data-testid="stTextInput"] input { min-height: 54px; font-size: 22px; text-align: center; letter-spacing: 6px; border-radius: 14px; }
      [data-testid="stTextInput"] label p { color: #FFFFFF !important; font-family: 'Barlow Condensed', sans-serif; font-size: 16px; }
      .st-key-entrar button { background: linear-gradient(135deg, #F7C948, #D4A62A) !important; color: #16110D !important; border: 0 !important;
        box-shadow: 0 8px 22px rgba(247,201,72,.35); }
    </style>""", unsafe_allow_html=True)
    try:
        clave = str(st.secrets["CLAVE_ADMIN"])
    except Exception:
        st.error("Falta configurar la clave: en Streamlit, Settings → Secrets, escriba  CLAVE_ADMIN = \"su clave\"")
        st.stop()
    if not st.session_state.get("admin_ok"):
        st.markdown(f'<div class="cc-login">{"<img src=" + chr(34) + logo + chr(34) + ">" if logo else ""}'
                    '<h2>PANEL DE PLATOS</h2><p>Cafetería CC · Solo personal autorizado</p></div>', unsafe_allow_html=True)
        intento = st.text_input("Clave de acceso", type="password", placeholder="••••")
        if st.button("ENTRAR", key="entrar", width="stretch"):
            if intento == clave:
                st.session_state.admin_ok = True
                st.rerun()
            st.error("Clave incorrecta")
        st.stop()
    if carpeta is None:
        st.warning("Todavía no hay ningún menú publicado.")
        st.stop()
    agot = agotados_de(fecha)
    nombres = nombres_platos(carpeta)
    st.markdown(f'<div class="cc-cab">{"<img src=" + chr(34) + logo + chr(34) + ">" if logo else ""}'
                f'<div><h1>PANEL DE PLATOS</h1><p>{fecha_larga(fecha)}</p></div></div>'
                f'<div class="cc-resumen"><div class="cc-pill v">🟢 {4 - len(agot)} disponibles</div>'
                f'<div class="cc-pill r">🔴 {len(agot)} agotados</div></div>', unsafe_allow_html=True)
    estilos = []

    def al_cambiar(codigo):
        valor = st.session_state.get(f"seg_{codigo}")
        if valor:
            marcar_plato(fecha, codigo, valor == "AGOTADO")
            etiqueta = dict(PLATOS)[codigo]
            st.toast(("🔴 " if valor == "AGOTADO" else "🟢 ") + f"{etiqueta}: {valor.lower()}")

    for (codigo, etiqueta), nombre in zip(PLATOS, nombres):
        esta_agotado = codigo in agot
        foto = imgs.get(nombre, "")
        actual = "AGOTADO" if esta_agotado else "DISPONIBLE"
        st.session_state[f"seg_{codigo}"] = actual          # siempre muestra el estado real compartido
        with st.container(key=f"card_{codigo}"):
            st.markdown(
                f'<div class="cc-card {"agot" if esta_agotado else ""}">'
                f'{"<img src=" + chr(34) + foto + chr(34) + ">" if foto else ""}'
                f'<div><div class="cc-tag">{etiqueta}</div><div class="cc-nom">{nombre}</div>'
                + ('<span class="cc-est r"><span class="cc-pto"></span>AGOTADO</span>' if esta_agotado
                   else '<span class="cc-est v"><span class="cc-pto"></span>DISPONIBLE</span>')
                + '</div></div>', unsafe_allow_html=True)
            st.segmented_control(f"Estado de {etiqueta}", ["DISPONIBLE", "AGOTADO"], required=True,
                                 format_func=lambda v: ("● " + v), key=f"seg_{codigo}",
                                 on_change=al_cambiar, args=(codigo,), label_visibility="collapsed",
                                 width="stretch")
        color = "#FF3B4E" if esta_agotado else "#2FB457"
        oscuro = "#B3001B" if esta_agotado else "#17803A"
        estilos.append(
            f".st-key-card_{codigo} {{ border-radius: 22px; padding: 14px 14px 16px; margin-top: 6px;"
            f" background: {'linear-gradient(135deg, rgba(208,2,27,.26), rgba(255,255,255,.03))' if esta_agotado else 'rgba(255,255,255,.05)'};"
            f" border: 1px solid {'rgba(255,59,78,.7)' if esta_agotado else 'rgba(255,255,255,.13)'}; box-shadow: 0 10px 26px rgba(0,0,0,.35); }}"
            f".st-key-seg_{codigo} [role='radiogroup'] {{ background: rgba(0,0,0,.35); border-radius: 999px; padding: 4px; gap: 4px;"
            f" border: 1px solid rgba(255,255,255,.12); width: 100%; }}"
            f".st-key-seg_{codigo} button {{ flex: 1 1 0; min-height: 40px; border-radius: 999px !important; border: 0 !important;"
            f" background: transparent !important; color: rgba(255,255,255,.55) !important; font-family: 'Barlow Condensed', sans-serif;"
            f" font-weight: 800; letter-spacing: 2px; font-size: 15px; transition: all .25s ease; }}"
            f".st-key-seg_{codigo} button[aria-checked='true'] p {{ color: #FFFFFF !important; }}"
            f".st-key-seg_{codigo} button p {{ font-size: 15px !important; font-weight: 800 !important; letter-spacing: 2px; }}"
            f".st-key-seg_{codigo} button[aria-checked='true'] {{"
            f" background: linear-gradient(135deg, {color}, {oscuro}) !important; color: #FFFFFF !important;"
            f" box-shadow: 0 0 0 2px rgba(255,255,255,.18) inset, 0 6px 18px {color}88; animation: ccBrillo 2.4s ease-in-out infinite; }}"
        )
    estilos.append("@keyframes ccBrillo { 50% { filter: brightness(1.15); } }")
    estilos.append(".cc-card { margin: 0 0 10px !important; padding: 0 !important; background: transparent !important; border: 0 !important; box-shadow: none !important; }")
    st.markdown("<style>" + "\n".join(estilos) + "</style>", unsafe_allow_html=True)
    st.markdown('<div class="cc-nota">Los cambios aparecen en todas las TV y celulares en 2–3 segundos.</div>',
                unsafe_allow_html=True)
    st.stop()


if vista == "admin":
    pagina_control()


@st.fragment(run_every=2)
def sellos_en_vivo(fecha):
    """Cada 2 segundos aplica el estado de 'agotado' sin recargar el menú ni cortar la música."""
    agot = agotados_de(fecha)
    reglas = "".join(f".cc-agotado-{p}{{display:flex !important}}" for p in sorted(agot))
    st.markdown(f"<style>{reglas}</style>", unsafe_allow_html=True)
if carpeta is None:
    st.markdown('<div class="aviso">☕ Cafetería CC<br>El menú del día se publicará pronto.</div>',
                unsafe_allow_html=True)
    st.stop()

# Música: lista de reproducción con TODOS los .mp3 de la carpeta del día
# (menus/AAAA-MM-DD/*.mp3) o, si no hay, todos los de menus/*.mp3.
# Suenan en orden ALEATORIO; al terminar todas se vuelven a barajar y siguen sin parar.
mp3_del_dia = sorted(carpeta.glob("*.mp3"), key=lambda f: f.name.lower())
canciones = mp3_del_dia or sorted(CARPETA_MENUS.glob("*.mp3"), key=lambda f: f.name.lower())


def sonido_siempre_activo(hay_musica):
    """La música está SIEMPRE activada (sin botón). Reproduce la lista de canciones en
    orden y la repite sin fin. Si el navegador bloquea el sonido automático, empieza al
    primer toque, clic o botón del control remoto. Cada segundo revisa que todo siga sonando."""
    st.html(f"""
<script>
(function () {{
  var musicaAparte = {'true' if hay_musica else 'false'};
  /* Orden ALEATORIO: se barajan todas las canciones; al terminar la ultima se vuelven
     a barajar (sin repetir seguida la misma) y la musica nunca para. */
  function barajar(n, evitar) {{
    var a = []; while (a.length !== n) a.push(a.length);
    for (var i = n - 1; i > 0; i--) {{ var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }}
    if (n > 1 && a[0] === evitar) {{ var t2 = a[0]; a[0] = a[n - 1]; a[n - 1] = t2; }}
    return a;
  }}
  function aviso(mostrar) {{
    var a = document.getElementById('cc-aviso-sonido');
    if (!a && mostrar) {{
      a = document.createElement('div'); a.id = 'cc-aviso-sonido';
      a.textContent = '🔊 Toque la pantalla para escuchar la música';
      var abajo = innerWidth > innerHeight;
      a.style.cssText = 'position:fixed;left:50%;' + (abajo ? 'bottom:2vh;' : 'top:1.5vh;') + 'transform:translateX(-50%);z-index:99999;' +
        'background:rgba(0,0,0,.65);color:#F7C948;border:2px solid #F7C948;border-radius:999px;' +
        'padding:8px 20px;font:700 clamp(13px,1.4vw,30px) sans-serif;pointer-events:none;';
      document.body.appendChild(a);
    }}
    if (a) a.style.display = mostrar ? 'block' : 'none';
  }}
  function canciones() {{ return Array.prototype.slice.call(document.querySelectorAll('audio')); }}
  function actual() {{ var l = canciones(); if (!l.length) return null;
    if (!window.__ccOrden || window.__ccOrden.length !== l.length) {{ window.__ccOrden = barajar(l.length, -1); window.__ccPos = 0; }}
    return l[window.__ccOrden[window.__ccPos]]; }}
  function tocar(el, conSonido) {{
    var p = el.play();
    if (p && p.catch) p.catch(function () {{
      if (el.tagName === 'VIDEO') {{ el.muted = true; el.play().catch(function () {{}}); }}
      if (conSonido) aviso(true);
    }});
  }}
  function revisar() {{
    document.querySelectorAll('video').forEach(function (v) {{
      v.loop = true; v.autoplay = true; v.setAttribute('playsinline', ''); v.playsInline = true;
      if (!v.dataset.ccListo) {{ v.dataset.ccListo = '1'; v.muted = musicaAparte; }}
      if (v.paused || v.ended) tocar(v, !musicaAparte);
    }});
    if (!musicaAparte) return;
    var l = canciones(), cur = actual();
    l.forEach(function (a) {{ a.loop = false; a.muted = false; a.volume = 1; a.preload = 'auto';
      if (a !== cur && !a.paused) a.pause(); }});
    if (cur && (cur.paused || cur.ended)) {{ if (cur.ended) cur.currentTime = 0; tocar(cur, true); }}
  }}
  function siguiente() {{
    var l = canciones(); if (!l.length) return;
    var antes = actual(); if (antes) {{ antes.pause(); }}
    window.__ccPos = (window.__ccPos || 0) + 1;
    if (window.__ccPos >= l.length) {{ var ultima = window.__ccOrden[l.length - 1]; window.__ccOrden = barajar(l.length, ultima); window.__ccPos = 0; }}
    var cur = actual(); cur.currentTime = 0; tocar(cur, true);
  }}
  function activar() {{
    var cur = actual(); if (cur) {{ cur.muted = false; tocar(cur, false); }}
    document.querySelectorAll('video').forEach(function (v) {{ if (!musicaAparte) v.muted = false; v.play().catch(function () {{}}); }});
    aviso(false);
  }}
  if (!window.__ccListeners) {{
    window.__ccListeners = true;
    ['pointerdown', 'touchstart', 'keydown', 'click'].forEach(function (ev) {{
      document.addEventListener(ev, activar, {{ capture: true, passive: true }});
    }});
    document.addEventListener('visibilitychange', function () {{ if (!document.hidden) revisar(); }});
    document.addEventListener('ended', function (e) {{
      var el = e.target;
      if (el && el.tagName === 'AUDIO') siguiente();
      else if (el && el.play) {{ el.currentTime = 0; el.play().catch(function () {{}}); }}
    }}, true);
  }}
  /* Mantener la pantalla encendida (TV y celulares) mientras la pagina este abierta. */
  function pantallaEncendida() {{
    if ('wakeLock' in navigator && !window.__ccWL) {{
      navigator.wakeLock.request('screen').then(function (l) {{ window.__ccWL = l; l.addEventListener('release', function () {{ window.__ccWL = null; }}); }}).catch(function () {{}});
    }}
  }}
  pantallaEncendida();
  if (!window.__ccWLListener) {{
    window.__ccWLListener = true;
    document.addEventListener('visibilitychange', function () {{ if (!document.hidden) pantallaEncendida(); }});
    ['pointerdown', 'keydown'].forEach(function (ev) {{ document.addEventListener(ev, pantallaEncendida, {{ passive: true }}); }});
  }}
  if (window.__ccTimer) clearInterval(window.__ccTimer);
  window.__ccTimer = setInterval(revisar, 1000);
  revisar();
}})();
</script>""", unsafe_allow_javascript=True)


def poner_musica():
    for cancion in canciones:
        st.audio(str(cancion), format="audio/mpeg")


def mostrar_menu_vectorial(archivo):
    """Menú dibujado en vivo (vectorial): se ajusta a cualquier pantalla con nitidez total."""
    contenido = archivo.read_text(encoding="utf-8")
    # El dibujo y su script de ajuste se envían por separado: Streamlit solo ejecuta
    # el JavaScript de forma fiable cuando el bloque contiene únicamente el script.
    corte = contenido.rfind("<script>")
    if corte == -1:
        st.html(contenido)
    else:
        st.html(contenido[:corte])
        st.html(contenido[corte:], unsafe_allow_javascript=True)


if vista == "celular":
    html_menu = carpeta / "celular.html"
    if html_menu.exists():
        mostrar_menu_vectorial(html_menu)
    elif (carpeta / "celular.mp4").exists():
        st.video(str(carpeta / "celular.mp4"), loop=True, autoplay=True, muted=True)
    elif (carpeta / "celular.png").exists():
        st.image(str(carpeta / "celular.png"), width="stretch")
    poner_musica()
    sonido_siempre_activo(bool(canciones))
    sellos_en_vivo(fecha)
    st.markdown(f"""<div class="botones">
        <a class="wa" href="{WHATSAPP}" target="_blank">📲 Pedir por WhatsApp</a>
        <a class="pl" href="{PLATAFORMA}" target="_blank">🛒 Pedir en la plataforma</a></div>""",
                unsafe_allow_html=True)
    if (carpeta / "celular.png").exists():
        with open(carpeta / "celular.png", "rb") as f:
            st.download_button("⬇️ Descargar imagen del menú", f, file_name=f"menu_{fecha}.png",
                               mime="image/png", width="stretch")
else:
    html_menu = carpeta / "tv.html"
    if html_menu.exists():
        mostrar_menu_vectorial(html_menu)
    else:
        nombre = "tv_1080.mp4" if calidad == "1080" else "tv_4k.mp4"
        video = carpeta / nombre
        if not video.exists():
            video = carpeta / ("tv_4k.mp4" if nombre == "tv_1080.mp4" else "tv_1080.mp4")
        if video.exists():
            st.video(str(video), loop=True, autoplay=True, muted=True)
        else:
            st.markdown('<div class="aviso">Falta el menú de TV en la carpeta del día.</div>',
                        unsafe_allow_html=True)
    poner_musica()
    sonido_siempre_activo(bool(canciones))
    sellos_en_vivo(fecha)
