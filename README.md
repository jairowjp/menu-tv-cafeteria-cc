# Menú del día – Cafetería CC (pantalla para TV y celulares)

App de Streamlit que muestra automáticamente el menú del día:
- **TV 80" (4K):** `https://menu-cafeteria-cc.streamlit.app`
- **TV con navegador lento (Full HD):** `https://menu-cafeteria-cc.streamlit.app/?calidad=1080`
- **Celulares:** `https://menu-cafeteria-cc.streamlit.app/?vista=celular` (video + botones de WhatsApp y plataforma)

La app elige sola el menú de **hoy** (hora de Ecuador). Si el de hoy aún no se subió, muestra el último disponible.
Cada 10 minutos revisa si hay uno nuevo, así que la TV cambia sola de día.

## Estructura
```
app.py
requirements.txt
.streamlit/config.toml
menus/
  2026-10-16/
    tv_4k.mp4     (horizontal 3840x2160, con música, ciclo de 8 s)
    tv_1080.mp4   (horizontal 1920x1080, con música)
    celular.mp4   (vertical 1080x1920, con música)
    celular.png   (imagen vertical en alta resolución)
```

## Publicar (una sola vez)
1. Cree un repositorio en GitHub (por ejemplo `menu-tv-cafeteria-cc`) y suba todo el contenido de esta carpeta.
2. Entre a https://share.streamlit.io con su cuenta, pulse **Create app**, elija el repositorio, rama `main` y archivo `app.py`.
3. Elija el nombre de la dirección (por ejemplo `menu-cafeteria-cc`) y pulse **Deploy**.

## Publicar el menú de cada día
1. En GitHub, entre a la carpeta `menus`, pulse **Add file → Upload files**.
2. Arrastre los 4 archivos del día dentro de una carpeta con la fecha `AAAA-MM-DD`
   (en la casilla del nombre escriba por ejemplo `2026-10-19/` antes de soltar los archivos).
3. Pulse **Commit changes**. En 1–2 minutos la app se actualiza y la TV lo muestra sola.

## En la TV
- Abra la dirección en el navegador de la Smart TV (o en un TV Box / Chromecast / laptop conectada por HDMI) y póngala en pantalla completa.
- El video arranca en silencio (los navegadores lo exigen). Para la música, pulse una vez el botón **🔊 Activar música** (esquina superior derecha) con el control.
- Desactive el ahorro de energía / protector de pantalla de la TV.
