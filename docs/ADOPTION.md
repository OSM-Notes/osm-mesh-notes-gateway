# Adopción humanitaria del gateway

Guía para que organizaciones y comunidades **desplieguen, operen y confíen** en el OSM Mesh Notes Gateway sin depender del equipo de desarrollo.

Complementa:
- [FIELD_DEPLOYMENT_GUIDE.md](FIELD_DEPLOYMENT_GUIDE.md) — checklist de hardware
- [FIELD_CARD.md](FIELD_CARD.md) — tarjeta imprimible para usuarios de campo
- [spec.md](spec.md) — comportamiento del software
- [ROADMAP.md](ROADMAP.md) — prioridades futuras
- [SECURITY.md](SECURITY.md) — usuario del servicio y endurecimiento técnico

---

## 1. Artefacto “listo para campo”

**Estado hoy:** instalación con `scripts/install_pi.sh` + guía de terreno.  
**Objetivo de adopción:** una Pi que arranca y ya escucha `#osmnote`.

### Procedimiento mínimo de preparación (antes de salir)

1. Flashear Raspberry Pi OS en microSD **en casa/oficina**.
2. Instalar el gateway (`sudo bash scripts/install_pi.sh`).
3. Configurar `/var/lib/lora-osmnotes/.env` (`SERIAL_PORT`, `TZ`, `DRY_RUN=false`).
4. Probar con Heltec/T-Echo: `#osmstatus` y un `#osmnote` de prueba.
5. Etiquetar la SD y la caja: versión del software, región LoRa (p. ej. US915), contacto del operador.
6. Ejecutar `bash scripts/health_check.sh` y guardar la salida (foto o archivo).

### Imagen preconfigurada (aún no publicada)

Publicar una imagen `.img.xz` versionada es el salto pendiente (ver ROADMAP *Must*). Hasta entonces, este procedimiento + SD ya instalada es el equivalente operativo.

---

## 2. Tarjeta de campo para usuarios

Usar **[FIELD_CARD.md](FIELD_CARD.md)** (imprimir 1 página, plastificar si es posible).

Contenido esencial que debe llevar todo reportero:
- Cómo enviar `#osmnote`
- Esperar GPS 30–60 s al aire libre
- Qué respuestas esperar (nota / cola / rechazo)
- Qué **no** enviar (datos personales, emergencias)
- Comandos útiles: `#osmhelp`, `#osmstatus`

---

## 3. Salud operativa visible

Desde la Pi (o por SSH):

```bash
bash scripts/health_check.sh
```

El script reporta: servicio systemd, puerto serial, espacio en disco, NTP, cola SQLite pendiente, última actividad en logs.

Desde la mesh (sin SSH):

```
#osmstatus
```

Respuesta esperada: gateway activo, Internet OK/NO, cola total y del nodo.

**Regla operativa:** un coordinador debe poder decir en &lt;2 minutos si el puente está vivo.

---

## 4. Modo entrenamiento / demo

Para talleres **sin** escribir notas reales en OSM:

```bash
# En /var/lib/lora-osmnotes/.env
DRY_RUN=true
```

```bash
sudo systemctl restart lora-osmnotes
```

Comportamiento (`spec.md`):
- No envía DMs reales ni POSTs a OSM (según implementación: logs + IDs mock en worker)
- Sirve para practicar flujo de comandos y roles Meshtastic

Antes de operación real: `DRY_RUN=false` y verificar con un `#osmnote` controlado (texto claro tipo “PRUEBA — borrar”).

---

## 5. Ética y do-no-harm

### Principios

1. **No es un canal de emergencias.** No sustituye 123/911 ni coordinación médica.
2. **Canal LoRa puede ser público.** Cualquiera en el mismo canal puede leer mensajes.
3. **Las notas OSM son públicas** y permanentes hasta que la comunidad las cierre.
4. **Minimizar datos personales.** No nombres, teléfonos, direcciones de domicilio, datos de menores.
5. **Operador responsable.** Debe haber una persona/org identificable que mantiene el gateway.

### Antes de cada despliegue humanitario

- [ ] Briefing de 10 minutos con reporteros (tarjeta de campo + ejemplos)
- [ ] Acuerdo de qué se reporta (infraestructura, daños, puntos de agua…) y qué no
- [ ] Contacto del operador del gateway publicado en el puesto base
- [ ] Decidir canal: público de referencia vs canal con PSK (sección 8)
- [ ] Plan de retiro: apagar servicio / retirar SD al terminar la operación

### Responsabilidad

El software facilita reportes de mapeo. La decisión de desplegarlo en un contexto sensible (conflicto, población vulnerable, datos de sobrevivientes) es de la **organización operadora**, no del código.

---

## 6. Observabilidad mínima (sin SaaS)

### Cola y errores (SQLite)

```bash
DB=/var/lib/lora-osmnotes/gateway.db

# Pendientes
sudo sqlite3 "$DB" "SELECT local_queue_id, node_id, status, substr(text_original,1,40), last_error FROM notes WHERE status='pending' ORDER BY created_at;"

# Últimas 20 notas
sudo sqlite3 "$DB" "SELECT local_queue_id, status, osm_note_id, created_at FROM notes ORDER BY id DESC LIMIT 20;"

# Conteo del día (UTC en DB; interpretar con TZ del servidor)
sudo sqlite3 "$DB" "SELECT status, COUNT(*) FROM notes GROUP BY status;"
```

### Logs

```bash
sudo journalctl -u lora-osmnotes -n 100 --no-pager
sudo journalctl -u lora-osmnotes --since today | grep -iE 'error|sent|Created note'
```

### Export simple para post-misión

```bash
sudo sqlite3 "$DB" -header -csv "SELECT * FROM notes;" > notes_export_$(date +%Y%m%d).csv
```

No enviar este CSV a terceros sin revisar PII en `text_original`.

---

## 7. Resiliencia de despliegue

| Riesgo | Mitigación operativa |
|--------|----------------------|
| Corte de luz | Power bank ≥ 10 000 mAh; apagado limpio si es posible |
| SD corrupta | SD clase 10+; imagen de respaldo flasheada en segunda SD |
| Servicio caído | `systemd` ya usa `Restart=always`; verificar con `health_check.sh` |
| Sin Internet | Esperado: cola local; no reiniciar en pánico |
| Reloj incorrecto | Ver [TIME_CONFIGURATION.md](TIME_CONFIGURATION.md) |
| Pérdida de datos | Copiar `gateway.db` a USB al final del día |

### Backup rápido

```bash
sudo systemctl stop lora-osmnotes
sudo cp /var/lib/lora-osmnotes/gateway.db /media/usb/gateway-$(date +%Y%m%d).db
sudo systemctl start lora-osmnotes
```

### Watchdog

El unit systemd reinicia el proceso si muere. Para watchdog de hardware (Pi), ver configuración opcional en ROADMAP; no es obligatoria para el MVP.

---

## 8. Canal y seguridad por contexto

### Despliegue de referencia (MVP)

- Región: la de tu país (doc de referencia del proyecto: US915 / Colombia)
- Canal público sin PSK: máxima interoperabilidad, **cero confidencialidad**

### Operación sensible (recomendado valorar)

1. Crear canal Meshtastic **dedicado** a la operación (nombre claro, p. ej. `OSM-NOTES-OP`).
2. Configurar **PSK** en todos los nodos autorizados (app Meshtastic → canal).
3. Documentar la clave **fuera de línea** (papel en sobre, no en chat público).
4. Gateway y T-Echos deben compartir exactamente región + canal + PSK.
5. Tras la operación: rotar o invalidar la PSK.

Esto no sustituye cifrado de extremo a extremo de grado militar; reduce oyentes casuales en el aire.

Detalle técnico del servicio: [SECURITY.md](SECURITY.md).

---

## 9. Empaquetado y release

Para adopción institucional, cada versión estable debe publicar:

- [ ] Tag Git (`vX.Y.Z`) y [CHANGELOG](../CHANGELOG.md) actualizado
- [ ] Notas de release: qué hace / qué no hace / breaking changes
- [ ] Commit/tag alineado con `docs/spec.md`
- [ ] Tests CI en verde
- [ ] Artefacto instalable: tarball del repo o instrucciones `install_pi.sh` pinneadas a ese tag
- [ ] (Deseable) imagen SD checksumada
- [ ] Limitaciones conocidas (GPS 120 s, canal público por defecto, notas anónimas en OSM)

Checklist completo: sección *Release* en [ROADMAP.md](ROADMAP.md).

---

## 10. Multi-idioma de producto

### Runtime (ya implementado)

- Idioma por defecto: `LANGUAGE=es` en `.env`
- Por nodo: `#osmlang es` / `#osmlang en`
- Traducciones: `locale/*/LC_MESSAGES/lora-osmnotes.po`
- Compilar: `bash scripts/compile_translations.sh`

### Materiales de adopción

| Material | Idiomas mínimos |
|----------|-----------------|
| FIELD_CARD | es + en (mismas páginas o reverso) |
| Briefing do-no-harm | idioma local de la operación |
| README técnico | puede quedar en es/en mixto |

### Cómo añadir un idioma (operador técnico)

1. Copiar `locale/es/LC_MESSAGES/lora-osmnotes.po` → `locale/<code>/...`
2. Traducir `msgstr`
3. Compilar `.mo`
4. Extender validación en `database.set_user_language` / `#osmlang` si se quiere exponer el código nuevo

---

## Matriz rápida: qué pide un despliegue humanitario

| Rol | Necesita |
|-----|----------|
| Reportero | Tarjeta de campo, T-Echo, GPS al aire libre |
| Coordinador de puesto | `#osmstatus`, `health_check.sh`, export CSV |
| Instalador | FIELD_DEPLOYMENT_GUIDE + install_pi + prueba en seco |
| Org / donante | Ética do-no-harm, versión liberada, métricas post-misión (conteos) |

---

## Referencias rápidas de comandos

Ver [spec.md §9](spec.md) y [FIELD_CARD.md](FIELD_CARD.md).
