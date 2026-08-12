# Arquitectura del Sistema

Documento alineado con el código en `src/gateway/` y con [`spec.md`](spec.md).

## Visión General

El gateway convierte reportes Meshtastic (`#osmnote`) en notas de OpenStreetMap. Corre en una Raspberry Pi con un dispositivo Meshtastic por USB, cola SQLite store-and-forward y worker periódico.

```
Meshtastic USB ──► MeshtasticSerial ──► Gateway ──► CommandProcessor
                         │                  │              │
                    POSITION_APP       NotificationMgr   Database
                         │                  ▲              │
                   PositionCache            │         OSMWorker ──► OSM Notes API
                                            │              │
                                       (DM ACK/Q→Note)  Geocoding (Nominatim)
```

## Componentes

### 1. MeshtasticSerial (`meshtastic_serial.py`)

Comunicación real vía `meshtastic.serial_interface` + pubsub:

- Temas: `meshtastic.receive.text`, `.position`, `.receive` (fallback)
- Normaliza `node_id` a forma canónica `!` + 8 hex
- Actualiza `PositionCache` **solo** en paquetes de posición
- En mensajes de texto adjunta lat/lon desde cache o, si no hay, desde `node_info` (marcando `position_source`)
- Configura rol del gateway a `CLIENT_MUTE`
- `send_dm` / `send_broadcast`

### 2. PositionCache (`position_cache.py`)

Cache en memoria + tabla `position_cache`. La edad (`get_age`) usa `received_at` del último POSITION. No debe refrescarse al reutilizar coordenadas en un texto.

### 3. CommandProcessor (`commands.py`)

Hashtags, GPS, dedupe, rate limit, i18n. Ver lista completa en `spec.md` §9.

### 4. Database (`database.py`)

SQLite con WAL + `synchronous=FULL`. Tablas: `notes`, `position_cache`, `user_preferences`, `system_state`.

### 5. OSMWorker (`osm_worker.py`)

POST a OSM Notes, rate limit 3 s, reintentos con `last_error` marcado `intento n/N`.

### 6. NotificationManager (`notifications.py`)

ACKs, anti-spam, split de mensajes largos, Q→Note, notificaciones de fallo.

### 7. Gateway (`main.py`)

Orquesta serial + worker 30 s + corrección NTP + broadcast diario opcional.

**Envío inmediato**: tras encolar, intenta `send_note`; si OK, ACK success y `notified_sent=1` (evita doble Q→Note).

## Flujo `#osmnote`

```
POSITION_APP → PositionCache.update(received_at=now)
     …
TEXT #osmnote → CommandProcessor
  → validar GPS por edad del cache (sin refrescar received_at)
  → dedupe → create_note(pending)
  → intentar OSM inmediato
      OK  → sent + ACK success + notified_sent=1
      FAIL → pending + ACK queued
Worker 30s → process_pending → Q→Note si notified_sent=0
```

## Validación GPS

- `POS_GOOD = 15s`, `POS_MAX = 120s`
- Sin GPS / >120s → rechazo
- 15–120s → `[posición aproximada]`
- Solo `node_info` → aproximada, sin escribir cache

## Deduplicación

Mismo `node_id` + texto normalizado + coords ~4 decimales + bucket 120 s.

## Threading

1. Main (señales + loop)
2. Callbacks Meshtastic (pubsub)
3. Worker daemon (cola / notificaciones / NTP / broadcast)

SQLite con timeout; PositionCache compartido (escrituras de posición solo desde handler de POSITION).

## Configuración

`.env` en `/var/lib/lora-osmnotes/.env` o raíz del proyecto. Constantes en `config.py`. Ver `spec.md` §18 y `.env.example`.
