# uCam / uCam — Sistema propio de gestión de cámaras de seguridad (VMS)

> Documento de referencia del proyecto. Úsalo como skill/contexto persistente
> para mantener coherencia de arquitectura, stack y roadmap a través de todas
> las sesiones de desarrollo. Cuando generes código para este proyecto, respeta
> las decisiones aquí documentadas salvo que se actualice explícitamente esta
> misma sección.

> **REGLAS DE TRABAJO OBLIGATORIAS**:
> 1. Ante cualquier duda técnica (API, propiedades CSS, comportamiento de GTK,
>    GStreamer, FFmpeg, etc.) **lo primero es consultar la documentación oficial**
>    (docs.gtk.org, docs.rs, man pages, etc.) o buscar en la web. NO escribir
>    scripts de prueba, probes, ni experimentar a ciegas antes de leer la doc.
> 2. Seguir SIEMPRE la guía visual de la sección 1.4 para cualquier control nuevo.

## 0. Objetivo del documento

Este archivo es la fuente de verdad del proyecto uCam (UI de escritorio: **uCam**). Contiene:
- La arquitectura completa del sistema (planificada y real).
- El stack tecnológico decidido, por fase.
- El roadmap dividido en hitos, con estado actual y criterio de "hecho".
- Convenciones de código y estructura de repositorio.
- Un registro de decisiones técnicas (para no repetir discusiones ya cerradas).

**Objetivo del proyecto:** construir, como ejercicio de aprendizaje, un VMS (Video
Management System) propio capaz de descubrir, conectar, visualizar y grabar todas las
cámaras IP de la red doméstica del usuario, usando protocolos estándar (RTSP, ONVIF).
Prioridad: aprender arquitectura de sistemas y programación de bajo nivel (concurrencia,
streaming, pipelines de video), no llegar lo antes posible a un producto terminado.

**Nombre:**
- **uCam** — nombre del sistema / dominio del código (`ucam_viewer`, logs, config).
- **uCam** — nombre de la aplicación de escritorio (título de ventana, branding UI).

---

## 1. Arquitectura general

### 1.1 Componentes

El sistema se divide en componentes desacoplados. El frontend de fase 1 **no es web**:
es un visor nativo GTK4 + GStreamer. Un frontend web (HLS) queda como opción futura
para acceso remoto, no como camino actual.

| # | Componente | Responsabilidad | Estado |
|---|---|---|---|
| 1 | **Discovery / Registry** | Descubrir cámaras (ONVIF; luego WS-Discovery + nmap/arp-scan) y persistir config (nombre, RTSP URL, endpoint ONVIF, perfiles) | Parcial: ONVIF por endpoint manual + store JSON |
| 2 | **Live Viewer (uCam)** | UI de escritorio multi-cámara: grid/lista, preview, add/delete, estados de conexión | Avanzado (sección Cameras funcional) |
| 3 | **Stream / Recording Manager** | Orquestar grabación (y a futuro políticas) por cámara vía FFmpeg; un proceso por cámara | Hito 1 CLI listo; **no integrado** al viewer |
| 4 | **Storage / Index** | Segmentos en disco, rotación por tiempo/espacio, índice para búsqueda | Solo archivos sueltos en `recordings/` |
| 5 | **Analítica (fase 2)** | Movimiento/objetos → eventos → grabación inteligente | No empezado |
| 6 | **Acceso remoto (opcional, futuro)** | API + HLS/WebRTC para ver desde navegador fuera de la LAN | Explícitamente **fuera del camino crítico** |

### 1.2 Flujo de datos (actual y objetivo cercano)

```
                    ┌─────────────────────────────────────────┐
                    │  uCam (GTK4 + GStreamer)                │
                    │  CameraPlayer × N                       │
[Cámara IP]--RTSP-->│  rtspsrc → decodebin3 → gtk4paintablesink│
                    │  CameraStore → ~/.config/ucam/         │
                    └─────────────────────────────────────────┘
                              │
                              │ (pendiente: integrar)
                              ▼
                    ┌─────────────────────────────────────────┐
                    │  stream-manager (FFmpeg, 1 proc/cámara) │
                    │  segmentos MP4 → recordings/            │
                    └─────────────────────────────────────────┘

ONVIF (manual hoy): endpoint + creds → GetProfiles + GetStreamUri → RTSP URL
```

Flujo objetivo a medio plazo (sin web):

```
[Cámara IP] --RTSP--+--> [Viewer GStreamer] --> pantalla
                    |
                    +--> [RecordingManager] --> segmentos --> [índice] --> UI Recordings
[Discovery] --> [Store/DB]
(fase 2) [Analítica] --eventos--> [RecordingManager]
```

### 1.3 Decisiones de diseño vigentes

- **Visor nativo GTK4 + GStreamer** para live view en fase 1 (latencia baja, HW decode,
  sin transcode intermedio). **No** se implementa HLS/React como frontend principal.
- **HLS / web / WebRTC** solo si más adelante se necesita acceso remoto o multi-cliente;
  no bloquean el roadmap de desktop.
- **Un proceso FFmpeg por cámara** para grabación (aislar fallos, reinicio individual).
  El live view usa **un pipeline GStreamer por cámara** dentro del proceso del viewer.
- **Un `CameraPlayer` compartido** entre vista grid y lista (no dos conexiones RTSP a la
  misma cámara por layout).
- **decodebin3** como decoder principal (HW cuando hay); fallback único a **decodebin**
  si aparece "No caps set" / "Broken bit stream". Sin más heurísticas de codec.
- **RTSP por TCP** en el viewer (`rtspsrc protocols=4`, latency ~200 ms) — más fiable
  en redes domésticas que UDP.
- **Discovery híbrido** (plan): WS-Discovery/ONVIF principal; nmap/arp-scan fallback.
  Hoy: ONVIF con endpoint ingresado a mano + normalización de URLs estilo Dahua/Hikvision.
- **Metadata**: JSON en `~/.config/ucam/cameras.json` ahora; migrar a **SQLite** cuando
  haga falta indexar grabaciones/eventos. Postgres solo si escala más allá de lo doméstico.
- **Credenciales**: no en el repositorio. Store local y/o env (`CAMNET_RTSP_URL`). El
  JSON actual guarda URLs con credenciales embebidas (aceptable en prototipo casero;
  mejorar antes de multi-usuario).

### 1.4 Guía visual UI (estilo vigente — mantener en nuevos controles)

Paleta y formas ya decididas para la app. **Todo control nuevo debe heredar este estilo**:
- **Base**: fondo negro `#000000`, texto blanco, radio de esquinas = 5px (mismo que
  `$button_radius` del tema Default de GTK4; verify con fuente oficial si hay dudas).
- **Botones de acción (Play / Folder / Delete)**: **sin contorno** (`border: none`),
  `background-color: #1b1b1d`, `border-radius: 5px`, `padding: 6px 11px`,
  `min-height: 0`, font 12px/500; hover `#1f1f22`, active `#141414`. Icono
  `.material-icon` interior: `min-width: 0`, `font-size: 13px` (ver nota abajo).
  Delete: texto `#ffb4ab`, hover `#2a1c1c`.
- **Botón Refresh**: fondo `#1b1b1b`, contorno `1px solid #262626`, `border-radius: 5px`,
  `padding: 7px 10px`, `min-height: 0`, `font-size: 14.667px`, hover `#1f1f1f`.
- **DropDown de filtro**: entre texto y flecha sin hueco grande — esto sale de
  `min-width` (hoy 0) y del `spacing` del Box interno. El radio del botón interno del
  dropdown lo da el tema (5px), no el CSS propio (GTK4 CSS **sí** soporta selectores
  descendientes como `.recording-action-btn .material-icon`).
- **Junto**: dropdown y refresh (46px vs 34px de altura) ya están alineados: se iguala
  por tamaño de botón interno del dropdown (~34px) y estilos de refresh.
- **Fila de grabación**: fondo `#161618`, contorno `1px solid #26262a`,
  `border-radius: 10px`, `padding: 10px`; hover `#1c1c1f` + borde `#333338` (el usuario
  lo quiere MANTENER). Thumb: fondo `#0d0d0f`, radio 6px.
- **Lección aprendida (importante)**: en GTK4/Pango la altura de un `Label` con icono
  glyph impar, del `font-size` del icono (ascent+descent del glifo, no `line-height`).
  Para poder controlar la altura de un botón, hay que reducir el `font-size` del icono,
  no jugar con `line-height`.

---

## 2. Stack tecnológico

### Fase 1 — Python (vigente)

| Capa | Elección | Motivo |
|---|---|---|
| UI live | **GTK4 + PyGObject** | Nativo Linux, CSS, widgets ricos, sin browser |
| Video live | **GStreamer** (`rtspsrc`, `decodebin3`, `gtk4paintablesink`) | Pipeline real, HW accel, paintable en GTK4 |
| Grabación | **FFmpeg** vía `subprocess` (`-c copy`, segment muxer) | Sin reencode, bajo CPU, segmentos con timestamp |
| ONVIF | **`onvif-zeep`** (síncrono; discovery en thread + `GLib.idle_add`) | Maduro en Python; WSDL del paquete |
| Persistencia cámaras | JSON (`CameraStore`) → SQLite más adelante | Cero fricción; swap anticipado en código |
| Discovery red (pendiente) | WS-Discovery + nmap/arp-scan | Cubre ONVIF y dispositivos mudos |
| Empaquetado viewer | `viewer/.venv` + entry `ucam-viewer.py` | Re-exec al venv si existe |

### Fase 2 — Reescritura de componentes críticos (Rust)

Cuando la arquitectura desktop + grabación esté **estable e integrada**, el
**Recording / Stream Manager** (no necesariamente el viewer GTK) puede reescribirse
en Rust como servicio independiente.

| Capa | Elección | Motivo |
|---|---|---|
| Runtime async | `tokio` | Estándar async en Rust |
| Video | `gstreamer-rs` o `ffmpeg-next` | Pipelines serios; GStreamer más flexible |
| RTSP nativo (alt.) | `retina` | Evitar spawnear FFmpeg si se quiere más control |
| Comunicación | HTTP/gRPC hacia el resto del sistema | Contrato estable durante la migración |

**Nota:** ONVIF en Rust es débil. Discovery/Registry puede quedarse en Python.
No todo el sistema tiene que migrar de lenguaje.

### Herramientas transversales

- **FFmpeg / ffprobe**: grabación y probe de conectividad.
- **GStreamer + plugins** (incl. `gtk4paintablesink`): live view obligatorio.
- **nmap / arp-scan**: fallback de discovery (Hito 4).
- **Docker Compose**: opcional más adelante si hay servicios headless (recorder daemon,
  API remota); no es requisito del viewer de escritorio.

### Stack descartado / diferido como camino principal

| Idea original | Estado |
|---|---|
| React + `hls.js` como frontend v1 | **Diferido** — no es el frontend de fase 1 |
| FastAPI sirviendo HLS en vivo | **Diferido** — solo si hay acceso remoto |
| RTSP → HLS con latencia 3–6 s para uso local | **Reemplazado** por GStreamer nativo |

---

## 3. Conceptos técnicos clave (glosario)

- **RTSP**: protocolo del video desde la cámara. URL típica:
  `rtsp://usuario:pass@ip:554/stream1`. Algunas marcas (Dahua/Hikvision) meten
  credenciales en el path (`user=…_password=…`); el viewer las normaliza a
  `user:pass@host`.
- **ONVIF**: estándar SOAP/XML para discovery, perfiles y control (PTZ, etc.).
- **WS-Discovery**: multicast puerto 3702; anuncio de dispositivos ONVIF sin IP previa.
- **GetStreamUri**: ONVIF → URL RTSP real de un perfil (evita adivinar paths).
- **GStreamer pipeline (live)**: `rtspsrc` → `decodebin3`/`decodebin` → `videoconvert`
  → `gtk4paintablesink` → `Gtk.Picture`.
- **FFmpeg segment recording**: `-f segment -segment_time N -strftime 1` + `-c copy`.
- **HLS / WebRTC**: relevantes solo para un eventual cliente web remoto; no para el
  uso local del VMS en fase 1.

---

## 4. Estructura de repositorio (real)

```
uCam/   (repo; sistema uCam)
├── stream-manager/
│   └── recorder.py              # Hito 1: grabación RTSP 1 cámara, reconexión + backoff
├── viewer/
│   ├── ucam-viewer.py         # entry point (re-exec a .venv si existe)
│   ├── requirements.txt         # PyGObject, onvif-zeep
│   ├── .venv/                   # entorno local (no versionar secrets)
│   └── ucam_viewer/
│       ├── main.py              # Gtk.Application + MainWindow
│       ├── cli.py               # --camera NOMBRE=URL, CAMNET_RTSP_URL
│       ├── models.py            # CameraConfig, CameraStatus, CameraState
│       ├── pipeline.py          # build_pipeline GStreamer
│       ├── store.py             # ~/.config/ucam/cameras.json
│       ├── onvif_discovery.py   # perfiles + GetStreamUri + normalize_rtsp_url
│       ├── dialogs/             # AddCameraDialog (RTSP | ONVIF + preview)
│       ├── widgets/             # Sidebar, TopBar, CameraGrid, Card, ListRow, Player
│       └── styles/              # CSS GTK4 modular (base, sidebar, topbar, camera, …)
├── recordings/                  # segmentos MP4 de prueba (no es storage definitivo)
└── .opencode/skills/
    └── ucam-project-skill/
        └── SKILL.md             # este documento
```

**Runtime config (fuera del repo):**
- `~/.config/ucam/cameras.json` — lista de `{name, rtsp_url}`.

**Aún no existen (y no hay que inventarlos sin necesidad):** `backend/`, `frontend/` React,
`docker-compose.yml` como piezas del camino crítico.

---

## 5. Roadmap por hitos

Cada hito es un entregable usable. Los checkboxes reflejan el **estado real del código**.

### Hito 1 — Un solo stream por línea de comandos
**Objetivo:** validar RTSP real (timeouts, reconexión, auth) y grabar a disco.

Sub-objetivos:
- [x] Obtener RTSP URL (manual / ONVIF `GetStreamUri`).
- [x] Script Python + FFmpeg: segmentos de N segundos a disco (`recorder.py`).
- [x] Reconexión automática con backoff exponencial.
- [x] Logging de conexión / desconexión / error.
- [ ] Validación formal 24 h contra cámara real (criterio de "hecho" original).

**Criterio de "hecho":** el script corre ~24 h y sobrevive al menos una caída/reconexión
sin intervención manual.

**Dónde está:** `stream-manager/recorder.py`. Salida de prueba en `recordings/`.

---

### Hito 2 — Live view nativo (reemplaza “verlo en el navegador”)
**Objetivo:** ver video en vivo en escritorio con baja latencia.

> **Pivot:** el plan original era FFmpeg→HLS + FastAPI + hls.js. Se reemplazó por
> GStreamer embebido en GTK4. El criterio de valor es el mismo (ver el stream en vivo);
> el medio no.

Sub-objetivos:
- [x] Pipeline GStreamer RTSP → `gtk4paintablesink`.
- [x] Widget de reproducción con estados (CONNECTING / LIVE / NO_SIGNAL / ERROR).
- [x] Reconexión automática en el player.
- [x] Fallback decodebin3 → decodebin documentado.
- [x] Preview al agregar cámara.

**Criterio de "hecho":** abrís uCam y ves al menos una cámara en vivo de forma estable.

**Dónde está:** `viewer/ucam_viewer/` (`pipeline.py`, `widgets/camera_player.py`).

---

### Hito 3 — Multi-cámara + registry
**Objetivo:** N cámaras gestionadas, no una hardcodeada.

Sub-objetivos:
- [x] Modelo mínimo `CameraConfig` (name, rtsp_url).
- [x] Persistencia (JSON `CameraStore`; SQLite pendiente).
- [x] UI multi-cámara: grid + lista, un player por cámara compartido entre layouts.
- [x] Add / delete desde UI; merge con CLI `--camera`.
- [x] ONVIF en Add Camera: endpoint + perfiles + preview + add.
- [ ] Camera Management real (editar, reconectar, elegir perfil).
- [ ] Integrar el Recording Manager al registry (hoy el recorder es CLI aparte).
- [ ] Migrar store a SQLite cuando se indexen grabaciones.

**Criterio de "hecho":** agregás una cámara por UI y aparece en vivo sin reiniciar;
sobrevive reinicio de la app (persistencia).

**Estado:** criterio principal cumplido; management y grabación unificada pendientes.

---

### Hito 4 — Discovery automatizado
**Objetivo:** no depender de copiar endpoints a mano.

Sub-objetivos:
- [ ] WS-Discovery (multicast 3702).
- [ ] Al encontrar dispositivo: perfiles + `GetStreamUri` (reutilizar `onvif_discovery`).
- [ ] Fallback nmap/arp-scan → “pendiente de configuración manual”.
- [ ] Botón “Escanear red” en uCam.

**Criterio de "hecho":** con cámaras en la red no registradas, un escaneo las lista y
permite agregarlas con un clic (tras credenciales si hace falta).

---

### Hito 5 — Grabación con retención + UI
**Objetivo:** de “recorder CLI suelto” a sistema de grabación usable.

Sub-objetivos:
- [ ] Orquestar grabación desde uCam (o daemon controlado por el store) en paralelo al live.
- [ ] Estado UI `RECORDING` real por cámara.
- [ ] Política de rotación (antigüedad y/o espacio en disco).
- [ ] Índice de grabaciones (cámara, inicio/fin, path) — SQLite natural aquí.
- [ ] Sección **Recordings** en el sidebar: navegar y reproducir (GStreamer sobre archivo).

**Criterio de "hecho":** graba días sin llenar el disco; recuperás un segmento por fecha
desde la UI.

---

### Hito 6 — Detección de movimiento/objetos
**Objetivo:** grabación inteligente además de continua.

Sub-objetivos:
- [ ] Movimiento simple (OpenCV / diff de frames) o análisis sobre pipeline.
- [ ] (Opcional) YOLO nano u otro modelo liviano.
- [ ] Eventos → pre/post buffer de grabación; marca en el índice.
- [ ] Sección **Events** + notificaciones básicas (log/webhook).

**Criterio de "hecho":** segmentos “con evento” distinguibles de los continuos en la UI.

---

### Hito 7 (fase 2) — Recording/Stream Manager en Rust
**Objetivo:** systems programming sobre un problema real, **después** de validar
arquitectura e integración en Python.

Sub-objetivos:
- [ ] Servicio Rust (tokio + gstreamer-rs o ffmpeg-next).
- [ ] Contrato con el viewer/store (HTTP/gRPC/socket local).
- [ ] Migración gradual (ambos en paralelo).
- [ ] Benchmark memoria/CPU Python vs Rust con la misma cantidad de cámaras.

**Criterio de "hecho":** el manager Rust sostiene todas las cámaras de forma estable y
hay números comparativos.

---

### UI shell (trabajo transversal, no es un hito de streaming)

La app ya tiene navegación esqueleto. Completar sin bloquear Hitos 4–5:

| Sección | Estado |
|---|---|
| Cameras | Funcional (grid/list, add, delete, menú contextual) |
| Dashboard | Placeholder / vacío |
| Recordings | Vacío → Hito 5 |
| Events | Vacío → Hito 6 |
| Camera Management | Navega pero sin contenido real |
| Settings / Support / Sign Out | Cosmético |
| Favorites (top bar) | Cosmético |
| Fullscreen / Reconnect (list row) | Botones sin lógica |

---

## 6. Convenciones de código

- **Commits**: Conventional Commits (`feat:`, `fix:`, `refactor:`, `doc:`, etc.).
- **Python**: type hints en APIs públicas; preferir claridad sobre magia.
- **UI / mensajes de usuario**: español o inglés según lo ya usado en la pantalla
  (hoy la shell está mayormente en inglés: "Add Camera", "Cameras"); ser **consistente
  por superficie**. Nombres de módulos/servicios en inglés (`stream-manager`,
  `ucam_viewer`, `CameraStore`).
- **Credenciales**: nunca commitear URLs con password ni meterlas en el skill/docs.
  Usar env o store local. No loguear passwords en claro en nivel INFO.
- **GStreamer**: al destruir un pipeline, orden fijo — `paintable=None` → `NULL` →
  `get_state` wait — para evitar cuelgues/crashes (lección ya pagada en preview ONVIF).
- **Un player por `rtsp_url`**: no spawnear un segundo pipeline solo por cambiar layout.
- **Rust** (cuando aplique): `clippy` limpio; evitar `unwrap()` fuera de tests/prototipos.

---

## 7. Registro de decisiones (ADR-lite)

| Fecha | Decisión | Alternativas | Motivo |
|---|---|---|---|
| Inicio | Python fase 1; Rust solo para manager de streams/grabación en fase 2 | Rust en todo desde día 1 | No sumar lenguaje + dominio a la vez |
| Inicio | SQLite (plan) / JSON ahora; no Postgres | Postgres de entrada | Escala doméstica; migración simple si hace falta |
| Inicio | ONVIF + fallback nmap/arp-scan | Solo ONVIF | El usuario ya usa nmap/arp-scan; red de seguridad |
| Inicio (obsoleta como v1) | HLS en vez de WebRTC para browser | WebRTC | Simplicidad si el cliente era web |
| **2026-08** | **Frontend fase 1 = GTK4 + GStreamer (uCam), no React/HLS** | Seguir con HLS + hls.js; WebRTC | Live local con baja latencia, HW decode, sin transcode; el valor del Hito 2 se cumple en desktop |
| **2026-08** | **HLS/API web = opcional acceso remoto futuro** | Web como UI principal | No bloquea grabación, discovery ni analítica en LAN |
| **2026-08** | Live = GStreamer in-process; grabación = FFmpeg subprocess | Todo FFmpeg; todo GStreamer | Live necesita paintable GTK; grabación copy-segment es trivial y robusta con FFmpeg |
| **2026-08** | decodebin3 + fallback único a decodebin | Pipeline H.264 explícito fijo | Mejor caps/HW; avdec_h264 explícito no renderizaba bien con gtk4paintablesink en pruebas |
| **2026-08** | Persistencia inicial JSON en `~/.config/ucam` | SQLite de entrada | Iterar UI sin schema; store con API swappable |
| **2026-08** | Un `CameraPlayer` compartido grid/lista | Un pipeline por vista | Evita doble sesión RTSP y carga en la cámara |

> Agregar filas cada vez que se tome una decisión de arquitectura no trivial.

---

## 8. Estado actual y próximo paso

### Hecho (resumen)
- Recorder CLI con reconexión (`stream-manager/recorder.py`).
- Visor multi-cámara GTK4 con live RTSP, reconexión, grid/lista.
- Add Camera RTSP y ONVIF (perfiles, preview, normalización de URL).
- Persistencia JSON; menú contextual delete/config (config solo navega).
- CSS modular; shell con secciones (solo Cameras con contenido).

### No hecho / desacoplado
- Viewer y recorder no se hablan.
- Discovery de red automático.
- Recordings / Events / Management / Dashboard reales.
- Retención, índice SQLite, analítica, Rust.

### Próximos pasos recomendados (en orden de coherencia)

1. **UI shell útil**: Camera Management (editar/reconectar), Fullscreen, Reconnect;
   placeholders honestos en el resto.
2. **Integrar grabación al viewer** (Hito 5 light): REC por cámara + listado básico.
3. **Discovery de red** (Hito 4).
4. **SQLite + retención** cuando el índice de grabaciones lo exija.
5. **Analítica** y **Rust** solo con lo anterior estable.

Al implementar, **no** reintroducir React/HLS como dependencia del camino crítico salvo
decisión explícita nueva en la tabla ADR y en esta sección.
