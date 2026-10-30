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


def pagina_control():
    st.markdown("""<style>
      .block-container { padding: 24px 16px 60px !important; max-width: 720px !important; margin: 0 auto; }
      [data-testid="stVerticalBlock"] { gap: 12px !important; }
      h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; font-family: sans-serif; }
      div.stButton > button { width: 100%; min-height: 64px; font-size: 20px; font-weight: 800; border-radius: 14px; }
      .cc-estado { border-radius: 16px; padding: 14px 16px; margin-top: 8px; font-family: sans-serif; }
      .cc-disp { background: #0F3D22; border: 2px solid #2FB457; }
      .cc-agot { background: #4A0A12; border: 2px solid #FF3B4E; }
      .cc-tag { font-size: 14px; font-weight: 800; letter-spacing: 2px; color: #F7C948; text-transform: uppercase; }
      .cc-nom { font-size: 20px; font-weight: 800; color: #FFFFFF; margin: 4px 0; }
      .cc-est { font-size: 16px; font-weight: 800; }
    </style>""", unsafe_allow_html=True)
    try:
        clave = str(st.secrets["CLAVE_ADMIN"])
    except Exception:
        st.error("Falta configurar la clave: en Streamlit, Settings → Secrets, escriba  CLAVE_ADMIN = \"su clave\"")
        st.stop()
    if not st.session_state.get("admin_ok"):
        st.markdown("### 🔒 Control de platos – Cafetería CC")
        intento = st.text_input("Clave", type="password")
        if st.button("Entrar", width="stretch"):
            if intento == clave:
                st.session_state.admin_ok = True
                st.rerun()
            st.error("Clave incorrecta")
        st.stop()
    if carpeta is None:
        st.warning("Todavía no hay ningún menú publicado.")
        st.stop()
    st.markdown(f"### 🍽️ Control de platos\n**{fecha_larga(fecha)}**")
    st.caption("Los cambios se ven en todas las TV y celulares en 2–3 segundos.")
    agot = agotados_de(fecha)
    for (codigo, etiqueta), nombre in zip(PLATOS, nombres_platos(carpeta)):
        esta_agotado = codigo in agot
        clase, texto = ("cc-agot", "🔴 AGOTADO") if esta_agotado else ("cc-disp", "🟢 DISPONIBLE")
        st.markdown(f'<div class="cc-estado {clase}"><div class="cc-tag">{etiqueta}</div>'
                    f'<div class="cc-nom">{nombre}</div><div class="cc-est">{texto}</div></div>',
                    unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("🟢 Disponible", key=f"d_{codigo}", type="secondary" if esta_agotado else "primary", width="stretch"):
            marcar_plato(fecha, codigo, False)
            st.rerun()
        if c2.button("🔴 Agotado", key=f"a_{codigo}", type="primary" if esta_agotado else "secondary", width="stretch"):
            marcar_plato(fecha, codigo, True)
            st.rerun()
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
