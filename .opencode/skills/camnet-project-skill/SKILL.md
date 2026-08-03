# CamNet — Sistema propio de gestión de cámaras de seguridad (VMS)

> Documento de referencia del proyecto. Úsalo como skill/contexto persistente en OpenCode
> para mantener coherencia de arquitectura, stack y roadmap a través de todas las sesiones
> de desarrollo. Cuando generes código para este proyecto, respeta las decisiones aquí
> documentadas salvo que se actualice explícitamente esta misma sección.

## 0. Objetivo del documento

Este archivo es la fuente de verdad del proyecto CamNet. Contiene:
- La arquitectura completa del sistema.
- El stack tecnológico decidido, por fase.
- El roadmap dividido en hitos, cada uno con sub-objetivos y criterio de "hecho".
- Convenciones de código y estructura de repositorio.
- Un registro de decisiones técnicas (para no repetir discusiones ya cerradas).

**Objetivo del proyecto:** construir, como ejercicio de aprendizaje, un VMS (Video
Management System) propio capaz de descubrir, conectar, visualizar y grabar todas las
cámaras IP de la red doméstica del usuario, usando protocolos estándar (RTSP, ONVIF).
Prioridad: aprender arquitectura de sistemas y programación de bajo nivel (concurrencia,
streaming), no llegar lo antes posible a un producto terminado.

---

## 1. Arquitectura general

### 1.1 Componentes

El sistema se divide en 5 componentes desacoplados, cada uno con responsabilidad única:

1. **Discovery/Registry** — descubre cámaras en la red (WS-Discovery / ONVIF multicast,
   con fallback a nmap/arp-scan) y persiste su configuración: IP, credenciales, RTSP URL,
   endpoint ONVIF, perfiles de stream disponibles.
2. **Stream Manager** — orquesta un proceso por cámara que consume el RTSP y lo convierte
   en algo consumible: HLS para reproducción en vivo, segmentos de archivo para grabación.
3. **Storage/Recording** — política de grabación (continua o por evento), rotación de
   disco por tiempo/espacio, indexado de grabaciones para búsqueda posterior.
4. **API + Frontend** — backend REST que expone cámaras/streams/grabaciones, UI web para
   ver el grid de cámaras y reproducir grabaciones.
5. **Analítica (fase 2)** — detección de movimiento/objetos sobre los streams, disparo de
   eventos que la fase de grabación puede consumir.

### 1.2 Flujo de datos

```
[Cámara IP] --RTSP--> [Stream Manager] --HLS--> [Frontend/Browser]
                              |
                              +--segmentos--> [Storage/Recording] --index--> [DB]
                              |
[Discovery] --config--> [DB] <--API-- [Backend] <--REST-- [Frontend]
                              |
                    (fase 2) [Analítica] --eventos--> [Storage] (grabación por evento)
```

### 1.3 Decisiones de diseño ya tomadas

- **RTSP no se reproduce directo en navegador** → se transcodea a HLS vía FFmpeg. Se elige
  HLS sobre WebRTC para la primera versión por simplicidad de implementación, aceptando
  3-6s de latencia. WebRTC queda como mejora de fase futura si hace falta tiempo real.
- **Un proceso FFmpeg por cámara**, gestionado por el Stream Manager (no un solo proceso
  multiplexando todo — más simple de razonar, aislar fallos y reiniciar individualmente).
- **Discovery híbrido**: WS-Discovery/ONVIF como método principal, nmap/arp-scan como
  fallback para dispositivos que no respondan al protocolo estándar (ya usado manualmente
  por el usuario, se automatiza en el Hito 4).
- **Metadata en SQLite** al inicio (cámaras, grabaciones, eventos). Migrar a Postgres solo
  si el proyecto escala más allá de uso doméstico.

---

## 2. Stack tecnológico

### Fase 1 — Prototipado y validación de arquitectura (Python)

| Capa | Elección | Motivo |
|---|---|---|
| Backend/API | Python + FastAPI | Rápido de iterar, tipado con Pydantic, async nativo |
| ONVIF | `onvif-zeep-async` | La librería más madura disponible en Python |
| Video | FFmpeg (via `subprocess`) | Estándar de facto, hace RTSP→HLS con un comando |
| DB | SQLite + SQLAlchemy | Cero fricción para prototipar, migrable después |
| Frontend | React + `hls.js` | `hls.js` es la forma estándar de reproducir HLS en browsers que no lo soportan nativo |
| Discovery | `wsdiscovery` (Python) + scripts nmap/arp-scan existentes | Cubre el caso estándar y el fallback |

### Fase 2 — Reescritura de componentes críticos (Rust)

Una vez validada la arquitectura en Python, el **Stream Manager** se reescribe en Rust
como servicio independiente, comunicándose con el backend por HTTP/gRPC. Motivo:
concurrencia real sin GIL, sin pausas de GC en el pipeline de video, menor huella de
memoria si se despliega en hardware modesto (Raspberry Pi / mini PC / NAS).

| Capa | Elección | Motivo |
|---|---|---|
| Runtime async | `tokio` | Estándar de facto para async en Rust |
| Video | `gstreamer-rs` o `ffmpeg-next` | Pipelines de video serios; GStreamer más flexible, ffmpeg-next más directo |
| RTSP puro (alternativa) | `retina` | Cliente RTSP nativo en Rust, evita spawnear FFmpeg si se quiere más control |
| Web framework (si aplica) | `axum` | Se integra bien con tokio |
| ONVIF | crate `onvif` (inmaduro) | Esperar más SOAP/XML manual que en Python; posible cuello de botella |

**Nota de riesgo:** ONVIF en Rust es el punto más débil del ecosistema. Es aceptable
mantener el Discovery/Registry en Python (fase 1) y no migrarlo a Rust salvo necesidad
concreta — no todo el sistema tiene que terminar en el mismo lenguaje.

### Librerías/herramientas transversales

- **FFmpeg**: pieza central en ambas fases, para transcodificación RTSP→HLS y grabación.
- **nmap / arp-scan**: ya usados manualmente por el usuario para descubrimiento; se
  integran como fallback automatizado en el Hito 4.
- **Docker Compose**: para levantar el conjunto de servicios (backend, stream manager,
  frontend) de forma reproducible, especialmente útil de cara al despliegue final.

---

## 3. Conceptos técnicos clave (glosario de referencia)

- **RTSP (Real Time Streaming Protocol)**: protocolo por el que viaja el video crudo desde
  la cámara. URL típica: `rtsp://usuario:pass@ip:554/stream1`.
- **ONVIF**: estándar soportado por la mayoría de cámaras IP para descubrimiento,
  configuración y control (PTZ, perfiles de stream, etc.), basado en SOAP/XML.
- **WS-Discovery**: mecanismo de descubrimiento multicast (puerto 3702) usado por ONVIF
  para que los dispositivos se anuncien en la red sin conocer su IP de antemano.
- **HLS (HTTP Live Streaming)**: formato de streaming basado en segmentos `.ts` + playlist
  `.m3u8`, reproducible directo en navegador con `hls.js`. Mayor latencia, mucho más simple
  de implementar que WebRTC.
- **WebRTC**: streaming casi en tiempo real, pero requiere señalización, ICE/STUN/TURN;
  significativamente más complejo de implementar correctamente.
- **GetStreamUri**: llamada ONVIF que devuelve la URL RTSP real de un perfil de stream de
  la cámara — evita tener que adivinar/configurar la URL a mano.

---

## 4. Estructura de repositorio propuesta

```
camnet/
├── backend/                 # FastAPI: API REST, modelos, DB
│   ├── app/
│   │   ├── api/              # routers (cameras, streams, recordings)
│   │   ├── models/            # SQLAlchemy models
│   │   ├── onvif/             # wrapper sobre onvif-zeep-async
│   │   └── discovery/         # WS-Discovery + fallback nmap/arp-scan
│   └── tests/
├── stream-manager/           # Fase 1: subprocess FFmpeg orquestado desde Python
│                              # Fase 2: reescrito en Rust, servicio independiente
├── frontend/                  # React + hls.js
│   └── src/
│       ├── components/        # CameraGrid, StreamPlayer, RecordingBrowser
│       └── api/                # cliente REST
├── storage/                   # grabaciones (montado como volumen, no versionado)
├── docker-compose.yml
└── camnet-project-skill.md    # este documento
```

---

## 5. Roadmap por hitos

Cada hito es un proyecto funcional en sí mismo — al terminarlo tenés algo tangible
corriendo, no solo piezas sueltas.

### Hito 1 — Un solo stream por línea de comandos
**Objetivo:** validar la conexión básica a una cámara real y entender sus particularidades
(timeouts, reconexión, autenticación).

Sub-objetivos:
- [ ] Obtener la RTSP URL de una cámara (a mano o vía ONVIF `GetStreamUri`).
- [ ] Script Python que invoque FFmpeg para grabar segmentos de N segundos a disco.
- [ ] Manejo de reconexión automática si la cámara se cae o hay timeout.
- [ ] Logging básico de eventos (conexión, desconexión, error).

**Criterio de "hecho":** dejás el script corriendo 24hs contra una cámara real y sobrevive
a al menos una caída/reconexión sin intervención manual.

**Riesgos/gotchas:** algunas cámaras cierran la conexión RTSP si no reciben keep-alive;
verificar el comportamiento real de tus marcas específicas.

---

### Hito 2 — Verlo en el navegador
**Objetivo:** pipeline completo cámara → navegador.

Sub-objetivos:
- [ ] FFmpeg generando HLS (`-f hls`) en vez de solo grabar.
- [ ] Servidor HTTP mínimo (FastAPI) sirviendo el `.m3u8` y los segmentos `.ts`.
- [ ] Página HTML simple con `hls.js` reproduciendo el stream.

**Criterio de "hecho":** abrís una URL en el navegador y ves el video en vivo de la cámara
con latencia aceptable (<10s).

---

### Hito 3 — Multi-cámara + registry
**Objetivo:** generalizar de "una cámara hardcodeada" a "N cámaras gestionadas".

Sub-objetivos:
- [ ] Modelo de datos en SQLite: tabla `cameras` (ip, credenciales, rtsp_url, nombre).
- [ ] API REST: `POST/GET/DELETE /cameras`.
- [ ] Stream Manager como proceso que lanza/mata un FFmpeg por cámara según el registry.
- [ ] Frontend: grid mostrando todas las cámaras activas simultáneamente.

**Criterio de "hecho":** agregás una cámara nueva vía API/UI y aparece transmitiendo en el
grid sin reiniciar el sistema.

---

### Hito 4 — Discovery automatizado
**Objetivo:** eliminar la carga manual de cámaras.

Sub-objetivos:
- [ ] Implementar WS-Discovery (multicast puerto 3702) para encontrar dispositivos ONVIF.
- [ ] Al encontrar un dispositivo, consultar sus perfiles y `GetStreamUri` automáticamente.
- [ ] Fallback: script de nmap/arp-scan para detectar IPs que no respondan a ONVIF, y
      dejarlas como "pendiente de configuración manual" en vez de perderlas silenciosamente.
- [ ] Botón "Escanear red" en el frontend que dispare el discovery y muestre resultados.

**Criterio de "hecho":** con las cámaras conectadas a la red pero no registradas, un
"escaneo" las encuentra y las deja listas para agregar con un clic.

---

### Hito 5 — Grabación con retención
**Objetivo:** pasar de "streaming efímero" a "sistema de grabación real".

Sub-objetivos:
- [ ] Grabación continua a disco en paralelo al streaming en vivo.
- [ ] Política de rotación: por antigüedad (ej. borrar >7 días) y/o por espacio en disco.
- [ ] Indexado de grabaciones en DB (cámara, timestamp inicio/fin, path del archivo).
- [ ] UI para navegar grabaciones por cámara y rango de fecha/hora.

**Criterio de "hecho":** el sistema graba de forma continua durante días sin llenar el
disco, y podés recuperar y reproducir un segmento de una fecha específica.

---

### Hito 6 — Detección de movimiento/objetos
**Objetivo:** grabación inteligente en vez de puramente continua.

Sub-objetivos:
- [ ] Detección de movimiento simple con OpenCV (diferencia de frames).
- [ ] (Opcional, más avanzado) Detección de objetos con un modelo liviano (YOLO nano).
- [ ] Emisión de eventos que el sistema de grabación consume (grabar N segundos antes/después
      del evento, marcar el segmento como "evento" en vez de "continuo").
- [ ] Notificaciones básicas (webhook/log) cuando se detecta un evento.

**Criterio de "hecho":** el sistema distingue y marca segmentos "con movimiento" de los
puramente continuos, consultable desde la UI.

---

### Hito 7 (fase 2) — Migración del Stream Manager a Rust
**Objetivo:** aprender concurrencia/systems programming aplicado a un problema real,
una vez que la arquitectura ya está validada y estable en Python.

Sub-objetivos:
- [ ] Reescribir el Stream Manager como servicio Rust independiente (tokio + gstreamer-rs
      o ffmpeg-next).
- [ ] Definir el contrato de comunicación con el backend Python (HTTP/gRPC).
- [ ] Migrar cámara por cámara (correr ambos en paralelo durante la transición, no un
      big-bang switch).
- [ ] Benchmark comparativo: uso de memoria/CPU del Stream Manager Python vs Rust con la
      misma cantidad de cámaras.

**Criterio de "hecho":** el Stream Manager en Rust maneja todas las cámaras de forma
estable, y tenés números concretos que muestran la diferencia de recursos vs la versión
Python.

---

## 6. Convenciones de código

- **Commits**: convención tipo Conventional Commits (`feat:`, `fix:`, `refactor:`, etc.),
  un commit por sub-objetivo cuando sea razonable.
- **Python**: type hints obligatorios en funciones públicas, `ruff` para linting.
- **Rust**: `clippy` sin warnings antes de mergear, evitar `unwrap()` fuera de tests/prototipos.
- **Nombres de servicios**: en inglés (`stream-manager`, `discovery-service`), UI/mensajes
  de usuario en español.
- **Credenciales de cámaras**: nunca en código ni en el repositorio — variables de entorno
  o vault local, incluso en fase de prototipo casero.

---

## 7. Registro de decisiones (ADR-lite)

| Fecha | Decisión | Alternativas consideradas | Motivo |
|---|---|---|---|
| Inicio | HLS en vez de WebRTC para v1 | WebRTC | Simplicidad de implementación, latencia aceptable para uso doméstico |
| Inicio | Python en fase 1, Rust en fase 2 solo para Stream Manager | Rust desde el inicio en todo el sistema | Evitar sumar curva de aprendizaje del lenguaje + del dominio al mismo tiempo; Rust brilla específicamente en la concurrencia del Stream Manager |
| Inicio | SQLite en vez de Postgres | Postgres desde el inicio | Cero fricción de setup para un proyecto de escala doméstica; migración es straightforward si hace falta |
| Inicio | ONVIF/WS-Discovery + fallback nmap/arp-scan | Solo ONVIF | El usuario ya tiene un flujo de descubrimiento funcionando con nmap/arp-scan; no descartarlo, integrarlo como red de seguridad |

> Agregar filas nuevas a esta tabla cada vez que se tome una decisión de arquitectura no
> trivial durante el desarrollo, para no repetir la discusión más adelante.

---

## 8. Próximo paso inmediato

Arrancar **Hito 1**: script Python que se conecte a una cámara real vía RTSP y comience a
grabar segmentos a disco, con reconexión automática ante caídas.
