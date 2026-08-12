# Especificación del OSM Mesh Notes Gateway

**Estado**: Canónica (refleja el comportamiento implementado en el código).  
**Versión del software**: 0.1.x  
**Fuente de verdad**: este documento + `src/gateway/config.py` para constantes numéricas.

Si la documentación y el código divergen, **actualizar este documento y el código juntos**. El prompt histórico de implementación (MVP original) se conserva solo como referencia en la sección 17.

---

## 1. Propósito

Permitir que personas en terreno (sin Internet) envíen reportes de texto desde una red LoRa mesh (Meshtastic) y que un **gateway en Raspberry Pi** (con Internet intermitente) los convierta en **OSM Notes**.

Prioridades:
- Simplicidad de despliegue
- Robustez store-and-forward
- Privacidad (no es canal de emergencias)

---

## 2. Hardware objetivo

| Rol | Hardware | Notas |
|-----|----------|--------|
| Reporter (campo) | T-Echo (u otro nodo Meshtastic con GNSS) | GPS habilitado; app Meshtastic por BLE |
| Gateway radio | Heltec V3 (u otro Meshtastic USB) | Sin GPS requerido; conectado por USB a la Pi |
| Compute | Raspberry Pi 3+ | Raspberry Pi OS u otro Linux |

**Conexiones**
- Campo: teléfono ↔ BLE ↔ T-Echo ↔ LoRa mesh
- Gateway: Heltec V3 ↔ USB serial ↔ Raspberry Pi ↔ Internet (intermitente) ↔ OSM Notes API

**Rol Meshtastic del gateway**: `CLIENT_MUTE` (envía/recibe, no reenvía tráfico de la mesh).  
**Rol recomendado en nodos móviles**: `CLIENT` (pueden reenviar `#osmXXX` hacia el gateway).

---

## 3. Stack

- Meshtastic sobre LoRa (sin MQTT)
- Python 3.8+ con `meshtastic` (protobuf real, no parser de texto ad-hoc)
- SQLite (cola offline + auditoría + cache GPS + preferencias)
- systemd 24/7
- i18n gettext (`es` por defecto, `en` opcional por nodo)

---

## 4. Alcance

### 4.1 Qué hace
- Recibe paquetes Meshtastic (texto + posición) por USB
- Procesa **solo** comandos/hashtags definidos
- Para `#osmnote`, asocia GPS del emisor y crea/encola una OSM Note
- Store-and-forward si no hay Internet
- Responde por **DM** (ACK, rechazo, comandos informativos)
- Reverse geocoding opcional (Nominatim) en ACKs de éxito
- Atribución del proyecto en el texto de la nota OSM

### 4.2 Qué no hace
- No es sistema de emergencias
- No procesa texto libre sin hashtag
- No exige etiquetas OSM al usuario
- No integra Ushahidi/uMap
- No usa brújula/orientación del celular

---

## 5. Radio / canal (despliegue de referencia)

- Región de referencia: **US915** (Colombia) en todos los nodos
- Canal: **público** (sin PSK) en el despliegue de referencia del MVP

Cualquier nodo en el mismo canal puede leer/escribir. El gateway solo actúa ante comandos.

---

## 6. Experiencia de usuario

1. Encender T-Echo al aire libre 30–60 s (primer fix GNSS)
2. Conectar app Meshtastic por Bluetooth
3. Enviar:

```
#osmnote <mensaje>
```

4. Recibir DM de confirmación / rechazo / cola

Consejo operativo: configurar `#osmnote` en Quick Chat (Append to message).

---

## 7. Validación de ubicación

El GPS y el texto no viajan necesariamente juntos. El gateway mantiene `last_position[node_id]` con el momento de recepción del **paquete POSITION** en el gateway.

### 7.1 Umbrales (`config.py`)

| Constante | Valor | Significado |
|-----------|-------|-------------|
| `POS_GOOD` | 15 s | Posición fresca |
| `POS_MAX` | 120 s | Máxima edad aceptable |

Decisión cerrada: `POS_MAX = 120` (no 60). Motivo: broadcast mínimo de posición Meshtastic ≈ 60 s + latencia mesh.

### 7.2 Reglas

| Condición | Resultado |
|-----------|-----------|
| Sin posición en cache ni `node_info` usable | Rechazar (sin GPS) |
| Edad > `POS_MAX` | Rechazar (GPS viejo) |
| `POS_GOOD` < edad ≤ `POS_MAX` | Aceptar + prefijo `[posición aproximada]` |
| edad ≤ `POS_GOOD` | Aceptar normal |
| Posición solo desde `node_info` (sin POSITION reciente) | Aceptar como aproximada; **no** actualizar cache |

### 7.3 Regla crítica de implementación

**Prohibido** refrescar `received_at` del cache al procesar un mensaje de texto que reutiliza lat/lon cacheados. Eso pondría edad = 0 y anularía `POS_MAX`/`POS_GOOD`.  
La edad solo avanza desde paquetes `POSITION_APP` (o equivalente).

### 7.4 Coordenadas inválidas

Rechazar `(0,0)`, lat fuera de [-90,90], lon fuera de [-180,180].

### 7.5 Arranque reciente del dispositivo

Si hay `device_uptime` < `DEVICE_UPTIME_RECENT` (120 s) y no hay GPS usable, mensaje específico pidiendo esperar (`DEVICE_UPTIME_GPS_WAIT` = 60 s).

### 7.6 Bypass de depuración

`GPS_VALIDATION_DISABLED=true` desactiva checks (solo depuración; puede usar posición por defecto de Bogotá). No usar en producción.

---

## 8. Deduplicación

Objetivo: evitar reintentos accidentales, **no** colapsar eventos reales distintos.

Duplicado **solo si** coinciden todas:
1. Mismo `node_id`
2. Texto normalizado idéntico (trim + colapsar espacios; incluye prefijo de aproximación si aplica)
3. Ubicación cercana: lat/lon a `DEDUP_LOCATION_PRECISION` = 4 decimales (~11 m)
4. Mismo bucket temporal: `floor(recv_time / DEDUP_TIME_BUCKET_SECONDS)` con bucket = 120 s

Explícito:
- No deduplicar entre nodos distintos
- No deduplicar si cambia la ubicación (aunque el texto sea igual)

Si es duplicado: no crear nota; sí enviar ACK de duplicado.

---

## 9. Comandos

Todas las respuestas de comandos van por **DM**.

| Comando | Comportamiento |
|---------|----------------|
| `#osmnote <texto>` | Crear/encolar nota (variantes abajo) |
| `#osmhelp` | Ayuda + tips de configuración |
| `#osmmorehelp` | Ayuda extendida |
| `#osmstatus` | Gateway activo, Internet OK/NO, cola total y del nodo |
| `#osmcount` | Notas del nodo: hoy + total (día según `TZ`) |
| `#osmlist [n]` | Últimas n notas pending+sent (default 5, max 20) |
| `#osmqueue` | Cola total y del nodo |
| `#osmnodes` | Nodos conocidos en cache GPS (máx. 20 listados) |
| `#osmlang [es\|en]` | Ver/cambiar idioma del nodo |

Variantes de nota: `#osmnote`, `#osmnotes`, `#osm-note`, `#osm-notes`, `#osm_note`, `#osm_notes` (word boundary; `#osmnotetest` no cuenta).

Reglas:
- Solo hashtag sin texto → rechazo “falta texto”
- Texto > `MESHTASTIC_MAX_MESSAGE_LENGTH` (200) → rechazo
- Rate limit por nodo: `USER_RATE_LIMIT_MAX_MESSAGES` = 5 en ventana de 60 s
- Texto libre sin comando → **ignore** (sin respuesta)

Chequeo de Internet en `#osmstatus`: HTTP a `https://www.openstreetmap.org` (misma dependencia operativa que el upload).

---

## 10. Plantillas de mensajes (comportamiento)

Los textos exactos viven en `commands.py` + gettext (`locale/`). Decisiones de producto:

- Aviso de privacidad: *«No envíes datos personales ni emergencias de cualquier tipo.»*
- En ACKs de éxito/cola/duplicado, el aviso se muestra cada 5 notas del nodo (`total % 5 == 0`), no en todos los mensajes, para ahorrar bytes LoRa.
- GPS viejo: mensaje indica **>2 min** (alineado con `POS_MAX=120`).
- ACK de éxito puede incluir línea `📍 Ubicación: …` vía Nominatim si hay red.
- Notas OSM incluyen atribución del proyecto al final del texto.
- Mensajes largos se parten en varias DMs (`notifications.split_long_message`).

### 10.1 Flujos `#osmnote`

| Resultado | Tipo interno | ACK |
|-----------|--------------|-----|
| Envío inmediato OK | `osmnote_queued` → success | Nota creada + URL (+ ubicación opcional) |
| Sin Internet / fallo API | `osmnote_queued` → queued | `Q-XXXX` en cola |
| Rechazo | `osmnote_reject` | Motivo (GPS, texto, rate limit, etc.) |
| Duplicado | `osmnote_duplicate` | Ya registrado |
| Error interno al persistir | `osmnote_error` | Error al crear nota |

### 10.2 Notificación Q→Note

Solo cuando una nota estaba `pending`, pasó a `sent`, y `notified_sent == 0`.

Si el envío **inmediato** ya envió ACK de éxito, se marca `notified_sent = 1` para **no** duplicar con Q→Note.

Anti-spam notificaciones: máx. 3 / minuto / nodo; si excede, resumen pidiendo `#osmlist`.

---

## 11. Persistencia SQLite

Ruta por defecto: `/var/lib/lora-osmnotes/gateway.db` (`DATA_DIR`).

### 11.1 Tabla `notes`

Campos: `id`, `local_queue_id` (`Q-0001`), `node_id`, `created_at` (UTC), `lat`, `lon`, `text_original`, `text_normalized`, `status` (`pending`|`sent`), `osm_note_id`, `osm_note_url`, `sent_at`, `last_error`, `notified_sent`.

PRAGMAs: `WAL`, `synchronous=FULL`.

### 11.2 Otras tablas

- `position_cache`: GPS persistente por nodo
- `user_preferences`: idioma por `node_id`
- `system_state`: broadcast diario, startup timestamp, corrección NTP

---

## 12. Worker OSM

- Intervalo: `WORKER_INTERVAL` = 30 s
- Rate limit global: ≥ `OSM_RATE_LIMIT_SECONDS` = 3 s entre POSTs
- Endpoint: `POST https://api.openstreetmap.org/api/0.6/notes.json`
- Reintentos: hasta `OSM_MAX_RETRIES` = 3; delay `OSM_RETRY_DELAY_SECONDS` = 60 s entre fallos en el mismo ciclo
- `last_error` persiste `… (intento n/N)` para detectar agotamiento y notificar fallos
- Tras agotar reintentos en el proceso, no reintentar en bucle inmediato; el marcador en `last_error` evita reintentos inútiles hasta intervención

`DRY_RUN=true`: no envía DMs reales ni llama a OSM (logs + IDs mock).

---

## 13. Tiempo / NTP

En despliegues sin reloj estable, al arrancar se guarda `startup_timestamp`. Cuando NTP sincroniza (`timedatectl`), si el offset es > 60 s se ajustan solo notas `pending`. Ver `docs/TIME_CONFIGURATION.md`.

Timezone por defecto: `America/Bogota` (`TZ`).

---

## 14. Broadcast diario (opcional)

`DAILY_BROADCAST_ENABLED=true`: como máximo un broadcast por día calendario (persistido), no en el primer ciclo del worker tras reinicio.

---

## 15. Privacidad y seguridad operativa

- Canal público: no hay confidencialidad
- Automatismos solo con hashtags
- Comandos informativos y ACKs solo por DM
- Nombre de nodo gateway recomendado: `osm-notes-bot`
- No almacenar PII deliberadamente; las notas OSM son públicas

---

## 16. Prueba de aceptación en campo

1. T-Echo al aire libre 30–60 s
2. `#osmstatus` → DM con Internet OK/NO
3. `#osmnote Prueba en campo` → DM con nota o `Q-XXXX`
4. Cortar Internet → `#osmnote …` → cola
5. Restaurar Internet → DM `Q-XXXX → Nota #YYYY` (si no hubo ACK inmediato previo)
6. `#osmlist` → pending y sent
7. Reenviar el mismo texto inmediatamente → ACK duplicado
8. Esperar >2 min sin POSITION y enviar nota → rechazo GPS viejo

---

## 17. Historial: prompt MVP original (obsoleto como especificación)

El prompt largo usado para bootstrap del MVP pedía `POS_MAX=60s` y un subconjunto de comandos. **Esa sección ya no es normativa.** Valores vigentes: secciones 1–16 y `config.py`.

Cambios relevantes respecto al MVP inicial:
- `POS_MAX` 60 → 120
- Comandos añadidos: `#osmmorehelp`, `#osmlang`, `#osmnodes`
- Integración real `meshtastic-python` (no protocolo texto pipe/JSON)
- Geocoding Nominatim, rate limit por usuario, i18n, corrección NTP, cache GPS persistente
- Variantes plurales de `#osmnote`
- Aviso de privacidad “emergencias de cualquier tipo”
- ACK de éxito puede incluir ubicación textual

---

## 18. Constantes de referencia rápida

| Constante | Valor |
|-----------|-------|
| `POS_GOOD` | 15 |
| `POS_MAX` | 120 |
| `DEDUP_TIME_BUCKET_SECONDS` | 120 |
| `DEDUP_LOCATION_PRECISION` | 4 |
| `OSM_RATE_LIMIT_SECONDS` | 3 |
| `OSM_MAX_RETRIES` | 3 |
| `WORKER_INTERVAL` | 30 |
| `MESHTASTIC_MAX_MESSAGE_LENGTH` | 200 |
| `USER_RATE_LIMIT_MAX_MESSAGES` | 5 / 60 s |
| `NOTIFICATION_ANTI_SPAM_MAX` | 3 / 60 s |
| `LANGUAGE` default | `es` |
