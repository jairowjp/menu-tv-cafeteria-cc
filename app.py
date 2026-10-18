"""
Menú del día – Cafetería CC
Pantalla para TV de 80" y vista para celulares.

Uso:
  Misma dirección para todos: https://menu-cafeteria-cc.streamlit.app/
  La app detecta sola si es celular (video vertical) o TV/computadora (video horizontal 4K).
  Forzar vista:   ?vista=tv   o   ?vista=celular
  TV lenta:       ?calidad=1080

Cada día se agrega una carpeta en  menus/AAAA-MM-DD/  con:
  tv_4k.mp4     video horizontal 3840x2160 (con música)
  tv_1080.mp4   video horizontal 1920x1080 (para TV con navegador lento)
  celular.mp4   video vertical 1080x1920 (con música)
  celular.png   imagen vertical en alta resolución
La app muestra sola el menú de HOY (hora de Ecuador). Si aún no se subió,
muestra el último menú disponible.
"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
from streamlit_autorefresh import st_autorefresh

ZONA = ZoneInfo("America/Guayaquil")
CARPETA_MENUS = Path(__file__).parent / "menus"
WHATSAPP = "https://wa.me/593968515340"
PLATAFORMA = "https://comedor.itb.edu.ec/login"
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

st.set_page_config(page_title="Menú del día – Cafetería CC", page_icon="☕",
                   layout="wide", initial_sidebar_state="collapsed")

params = st.query_params


def es_celular():
    """Detecta el tipo de equipo por el 'User-Agent' que envía el navegador.
    Celulares: traen 'Mobile' o 'iPhone'. Las Smart TV y Android TV no traen 'Mobile'."""
    try:
        ua = (st.context.headers.get("User-Agent") or "")
    except Exception:
        ua = ""
    return ("Mobi" in ua) or ("iPhone" in ua) or ("iPod" in ua)


# ?vista=tv o ?vista=celular obliga una vista; si no se indica, se detecta sola.
vista = params.get("vista", "").lower()
if vista not in ("tv", "celular"):
    vista = "celular" if es_celular() else "tv"
calidad = params.get("calidad", "4k").lower()

# Revisa cada 10 minutos si hay un menú nuevo (por ejemplo, al cambiar el día).
st_autorefresh(interval=10 * 60 * 1000, key="refresco")


def fecha_larga(d):
    return f"{DIAS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]} de {d.year}"


def buscar_menu():
    """Devuelve (carpeta, fecha, es_de_hoy) del menú de hoy o el último disponible."""
    hoy = datetime.now(ZONA).date()
    if not CARPETA_MENUS.exists():
        return None, None, False
    fechas = []
    for c in CARPETA_MENUS.iterdir():
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

# ---------- Estilos: pantalla completa, sin barras de Streamlit ----------
fondo = "#0B0B0E"
css_tv = ("" if vista == "celular" else
          '[data-testid="stVideo"], video { width: 100vw !important; height: 100vh !important; '
          'max-height: 100vh !important; object-fit: contain; background: #0B0B0E; display: block; } '
          '.stApp { overflow: hidden; } '
          'video::-webkit-media-controls, video::-webkit-media-controls-panel { display: none !important; }')
st.markdown(f"""
<style>
  header[data-testid="stHeader"], footer, #MainMenu,
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"], [data-testid="stSidebar"] {{ display: none !important; }}
  html, body, .stApp, [data-testid="stAppViewContainer"] {{ background: {fondo} !important; }}
  .block-container {{ padding: 0 !important; max-width: 100% !important; }}
  [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
  {css_tv}
  iframe[title="streamlit_autorefresh.st_autorefresh"] {{ display: none; }}
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

if carpeta is None:
    st.markdown('<div class="aviso">☕ Cafetería CC<br>El menú del día se publicará pronto.</div>',
                unsafe_allow_html=True)
    st.stop()

# La música inicia activada. Si el navegador bloquea el sonido automático, el video
# sigue en silencio y el sonido se activa solo al primer toque o botón del control.
if "sonido" not in st.session_state:
    st.session_state.sonido = True   # la música inicia ACTIVADA por defecto
etiqueta = "🔇 Silenciar" if st.session_state.sonido else "🔊 Activar música"
if st.button(etiqueta, key="btn_sonido"):
    st.session_state.sonido = not st.session_state.sonido
    st.rerun()
silencio = not st.session_state.sonido


def forzar_reproduccion(silencio):
    """Arranque automático en Chrome, Safari y Smart TV, con sonido por defecto.
    1) Intenta reproducir CON sonido.
    2) Si el navegador lo bloquea (política de autoplay), reproduce en silencio
       para que nunca quede detenido y muestra un aviso discreto; al primer toque,
       clic o botón del control remoto, activa el sonido automáticamente.
    3) Cada segundo revisa y, si el video se pausó, lo vuelve a reproducir."""
    st.html(f"""
<script>
(function () {{
  var quiereSilencio = {'true' if silencio else 'false'};
  window.__ccQuiereSilencio = quiereSilencio;

  function aviso(mostrar) {{
    var a = document.getElementById('cc-aviso-sonido');
    if (!a && mostrar) {{
      a = document.createElement('div'); a.id = 'cc-aviso-sonido';
      a.textContent = '🔊 Toque la pantalla o pulse OK para activar el sonido';
      a.style.cssText = 'position:fixed;left:50%;bottom:3vh;transform:translateX(-50%);z-index:99999;' +
        'background:rgba(0,0,0,.72);color:#F7C948;border:2px solid #F7C948;border-radius:999px;' +
        'padding:10px 22px;font:700 clamp(14px,1.6vw,34px) sans-serif;pointer-events:none;';
      document.body.appendChild(a);
    }}
    if (a) a.style.display = mostrar ? 'block' : 'none';
  }}

  function reproducir(v) {{
    var p = v.play();
    if (p && p.catch) p.catch(function () {{
      // Bloqueado con sonido: seguir en silencio y esperar un toque del usuario.
      v.muted = true; v.play().catch(function () {{}});
      if (!window.__ccQuiereSilencio) aviso(true);
    }});
  }}

  function arrancar() {{
    document.querySelectorAll('video').forEach(function (v) {{
      v.setAttribute('playsinline', ''); v.setAttribute('webkit-playsinline', '');
      v.playsInline = true; v.loop = true; v.autoplay = true; v.preload = 'auto';
      if (v.dataset.ccSilencio !== String(quiereSilencio)) {{
        v.dataset.ccSilencio = String(quiereSilencio);
        v.muted = quiereSilencio;
        if (quiereSilencio) aviso(false);
        reproducir(v);
      }} else if (v.paused) {{
        reproducir(v);
      }}
    }});
  }}

  function activarSonido() {{
    if (window.__ccQuiereSilencio) return;
    document.querySelectorAll('video').forEach(function (v) {{
      v.muted = false; v.volume = 1; v.play().catch(function () {{}});
    }});
    aviso(false);
  }}
  if (!window.__ccListeners) {{
    window.__ccListeners = true;
    ['pointerdown', 'touchstart', 'keydown', 'click'].forEach(function (ev) {{
      document.addEventListener(ev, activarSonido, {{ capture: true, passive: true }});
    }});
    document.addEventListener('visibilitychange', function () {{ if (!document.hidden) arrancar(); }});
  }}

  if (window.__ccTimer) clearInterval(window.__ccTimer);
  window.__ccTimer = setInterval(arrancar, 1000);
  arrancar();
}})();
</script>""", unsafe_allow_javascript=True)

if vista == "celular":
    st.markdown(f"<h3 style='color:#F7C948;text-align:center;font-family:sans-serif;margin:60px 12px 12px'>"
                f"Menú del {fecha_larga(fecha).lower()}</h3>", unsafe_allow_html=True)
    video = carpeta / "celular.mp4"
    if video.exists():
        st.video(str(video), loop=True, autoplay=True, muted=silencio)
        forzar_reproduccion(silencio)
    elif (carpeta / "celular.png").exists():
        st.image(str(carpeta / "celular.png"), width="stretch")
    st.markdown(f"""<div class="botones">
        <a class="wa" href="{WHATSAPP}" target="_blank">📲 Pedir por WhatsApp</a>
        <a class="pl" href="{PLATAFORMA}" target="_blank">🛒 Pedir en la plataforma</a></div>""",
                unsafe_allow_html=True)
    if (carpeta / "celular.png").exists():
        with open(carpeta / "celular.png", "rb") as f:
            st.download_button("⬇️ Descargar imagen del menú", f, file_name=f"menu_{fecha}.png",
                               mime="image/png", width="stretch")
else:
    nombre = "tv_1080.mp4" if calidad == "1080" else "tv_4k.mp4"
    video = carpeta / nombre
    if not video.exists():
        video = carpeta / ("tv_4k.mp4" if nombre == "tv_1080.mp4" else "tv_1080.mp4")
    if video.exists():
        st.video(str(video), loop=True, autoplay=True, muted=silencio)
        forzar_reproduccion(silencio)
    else:
        st.markdown('<div class="aviso">Falta el video de TV en la carpeta del día.</div>',
                    unsafe_allow_html=True)
