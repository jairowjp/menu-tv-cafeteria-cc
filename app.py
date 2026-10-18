"""
Menú del día – Cafetería CC
Pantalla para TV de 80" (incluye Android TV: RCA, TCL…) y vista para celulares.

Uso:
  Misma dirección para todos: https://menu-cafeteria-cc.streamlit.app/
  La app mira la PANTALLA del equipo: horizontal y grande = TV; vertical = celular.
  Forzar vista:   ?vista=tv   o   ?vista=celular   (recomendado guardar en la TV: ?vista=tv)
  Probar otro día: ?fecha=2026-10-19   (se puede combinar: ?fecha=2026-10-19&vista=celular)
  TV lenta:       ?calidad=1080

Cada día se agrega una carpeta en  menus/AAAA-MM-DD/  con:
  tv.html       menú VECTORIAL animado para TV (se dibuja en vivo, nitidez total)
  celular.html  menú VECTORIAL animado para celulares
  celular.png   imagen vertical en alta resolución (para descargar)
  (Si una carpeta antigua solo tiene tv_4k.mp4 / tv_1080.mp4 / celular.mp4, se usan esos.)
  musica.mp3    (opcional) música solo para ese día
Música general para todos los días:  menus/musica.mp3
La app muestra sola el menú de HOY (hora de Ecuador). Si aún no se subió,
muestra el último menú disponible. Video y música se repiten sin parar.
"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_js_eval import streamlit_js_eval

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
  div.stButton {{ position: fixed !important; top: 12px; right: 12px; z-index: 9999; width: auto !important; }}
  div.stButton > button {{ width: auto !important; opacity: 0.35; background: #222; color: #fff; border: 1px solid #555; }}
  div.stButton > button:hover, div.stButton > button:focus {{ opacity: 1; }}
</style>
""", unsafe_allow_html=True)

# ---------- ¿TV o celular? ----------
# Las TV Android (RCA, TCL…) se presentan como "celular" en su navegador, por eso no
# se puede confiar en ese dato. Se mira la pantalla: horizontal y de al menos 500 px
# de alto = TV o computadora; vertical o pequeña = celular.
params = st.query_params
vista = params.get("vista", "").lower()
if vista not in ("tv", "celular"):
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
if carpeta is None:
    st.markdown('<div class="aviso">☕ Cafetería CC<br>El menú del día se publicará pronto.</div>',
                unsafe_allow_html=True)
    st.stop()

# Música: la del día (menus/AAAA-MM-DD/musica.mp3) o la general (menus/musica.mp3).
musica = next((m for m in (carpeta / "musica.mp3", CARPETA_MENUS / "musica.mp3") if m.exists()), None)


def sonido_siempre_activo(hay_musica):
    """La música está SIEMPRE activada (sin botón). Se intenta reproducir con sonido
    desde el inicio; en equipos con reproducción automática permitida (navegador
    kiosko en la TV) suena sola. Si el navegador lo bloquea, suena al primer toque,
    clic o botón del control remoto en cualquier parte de la pantalla.
    Además, cada segundo revisa que música y animación sigan sonando sin parar."""
    st.html(f"""
<script>
(function () {{
  var musicaAparte = {'true' if hay_musica else 'false'};
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
  function lleva(el) {{ return musicaAparte ? el.tagName === 'AUDIO' : el.tagName === 'VIDEO'; }}
  function reproducir(el) {{
    var p = el.play();
    if (p && p.catch) p.catch(function () {{
      if (el.tagName === 'VIDEO') {{ el.muted = true; el.play().catch(function () {{}}); }}
      if (lleva(el)) aviso(true);
    }});
  }}
  function revisar() {{
    document.querySelectorAll('video, audio').forEach(function (el) {{
      el.loop = true; el.autoplay = true; el.preload = 'auto';
      if (el.tagName === 'VIDEO') {{ el.setAttribute('playsinline', ''); el.playsInline = true; }}
      if (!el.dataset.ccListo) {{ el.dataset.ccListo = '1'; el.muted = !lleva(el); el.volume = 1; reproducir(el); }}
      else if (el.paused || el.ended) {{ reproducir(el); }}
    }});
  }}
  function activar() {{
    document.querySelectorAll('video, audio').forEach(function (el) {{
      if (lleva(el)) {{ el.muted = false; el.volume = 1; }}
      el.play().catch(function () {{}});
    }});
    aviso(false);
  }}
  if (!window.__ccListeners) {{
    window.__ccListeners = true;
    ['pointerdown', 'touchstart', 'keydown', 'click'].forEach(function (ev) {{
      document.addEventListener(ev, activar, {{ capture: true, passive: true }});
    }});
    document.addEventListener('visibilitychange', function () {{ if (!document.hidden) revisar(); }});
    document.addEventListener('ended', function (e) {{
      var el = e.target; if (el && el.play) {{ el.currentTime = 0; el.play().catch(function () {{}}); }}
    }}, true);
  }}
  if (window.__ccTimer) clearInterval(window.__ccTimer);
  window.__ccTimer = setInterval(revisar, 1000);
  revisar();
}})();
</script>""", unsafe_allow_javascript=True)


def poner_musica():
    if musica:
        st.audio(str(musica), format="audio/mpeg", loop=True, autoplay=True)


def mostrar_menu_vectorial(archivo):
    """Menú dibujado en vivo (vectorial): se ajusta a cualquier pantalla con nitidez total."""
    st.html(archivo.read_text(encoding="utf-8"), unsafe_allow_javascript=True)


if vista == "celular":
    html_menu = carpeta / "celular.html"
    if html_menu.exists():
        mostrar_menu_vectorial(html_menu)
    elif (carpeta / "celular.mp4").exists():
        st.video(str(carpeta / "celular.mp4"), loop=True, autoplay=True, muted=True)
    elif (carpeta / "celular.png").exists():
        st.image(str(carpeta / "celular.png"), width="stretch")
    poner_musica()
    sonido_siempre_activo(musica is not None)
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
    sonido_siempre_activo(musica is not None)
