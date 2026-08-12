# Formato de Mensajes Meshtastic

Este gateway usa el protocolo **real** de Meshtastic (protobuf) mediante la biblioteca `meshtastic` (`SerialInterface` + pubsub). No usa un protocolo de texto ad-hoc por línea.

## Entrada

### Mensajes de texto (`TEXT_MESSAGE_APP`)

Suscripción: `meshtastic.receive.text` (y fallback en `meshtastic.receive`).

Campos relevantes del packet:
- `from` / `fromId` → normalizado a `node_id` canónico: `!` + 8 hex lowercase
- `decoded.text` → cuerpo del mensaje

El gateway construye un dict interno:

```python
{
  "node_id": "!a1b2c3d4",
  "text": "#osmnote ...",
  "lat": 4.6097,          # opcional
  "lon": -74.0817,        # opcional
  "timestamp": 1710000000.0,
  "device_uptime": 45.0,  # opcional (segundos)
  "position_source": "cache" | "node_info" | "none",
}
```

Origen de lat/lon al llegar un texto:
1. **cache** — última posición de un paquete `POSITION_APP` (preferido; la edad es real)
2. **node_info** — posición conocida por la mesh en `interface.nodes` (puede estar vieja; se marca aproximada y **no** se escribe en el cache)
3. **none** — sin coordenadas

### Posiciones (`POSITION_APP`)

Suscripción: `meshtastic.receive.position`.

Coordenadas Meshtastic enteras (`latitudeI` / `longitudeI`) ÷ 1e7 → float.  
Esto es lo único que debe llamar a `PositionCache.update()`.

## Salida

### DM

`MeshtasticSerial.send_dm(node_id, message)` → `interface.sendText(..., destinationId=node_num)`.

Mensajes largos se parten en el notification manager (~220 bytes UTF-8 por parte) con prefijo `[i/n]`.

### Broadcast

`send_broadcast(message)` → `sendText` sin destino.

## Comandos de usuario (capa aplicación)

Ver [`spec.md`](spec.md) §9. Ejemplos:

```
#osmnote Árbol caído frente al colegio
#osmhelp
#osmstatus
```

## Nota histórica

Versiones tempranas del documento describían formatos JSON/pipe y baudrate 9600 como MVP de texto. Eso **ya no aplica**: la implementación productiva es protobuf vía `meshtastic-python`.
