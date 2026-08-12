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

**Estado hoy (operador técnico):** instalar Raspberry Pi OS → `git clone` / checkout → `sudo bash scripts/install_pi.sh` → configurar `.env`. Ese flujo **es válido** y es el recomendado si quien despliega sabe Linux.

**Estado deseado (adopción no técnica):** un archivo de disco listo para flashear, sin GitHub en campo.

### ¿Dónde se “montaría” esa imagen? ¿Es un ISO?

No es un ISO de CD. Es una **imagen completa de la microSD** del Raspberry Pi:

| Qué | Detalle |
|-----|---------|
| Formato | Archivo `.img` o `.img.xz` (disco entero, no un CD) |
| Dónde se publica | **GitHub Releases** del proyecto (junto al tag `vX.Y.Z`), con SHA256 |
| Cómo se usa | En un PC: [Raspberry Pi Imager](https://www.raspberrypi.com/software/) o balenaEtcher → elegir el `.img.xz` → flashear una microSD vacía → insertar en la Pi → encender |
| Qué trae | Raspberry Pi OS + gateway ya instalado + servicio enabled (y `.env` de ejemplo o first-boot) |

**Scripts del repo** (detalle en [SD_IMAGE_RELEASE.md](SD_IMAGE_RELEASE.md)):

```bash
# En la Pi, tras git clone / checkout del tag:
sudo bash scripts/prepare_golden_pi.sh --tag v0.2.0 --with-backup-timer

# En un PC Linux, con la microSD insertada:
sudo bash scripts/build_sd_image.sh --device /dev/sdX --version v0.2.0 --upload
```

Hasta tener el `.img.xz` en Releases, el equivalente operativo es: preparar la SD **en casa** con git+install, probarla, y llevar esa SD al terreno.

### Procedimiento mínimo de preparación (antes de salir)

1. Flashear Raspberry Pi OS en microSD **en casa/oficina** (o flashear la imagen del release cuando exista).
2. Instalar el gateway (`sudo bash scripts/install_pi.sh`) si partiste de OS limpio.
3. Configurar `/var/lib/lora-osmnotes/.env` (`SERIAL_PORT`, `TZ`, `DRY_RUN=false`).
4. Opcional: `sudo bash scripts/install_backup_timer.sh` (backups diarios).
5. Probar con Heltec/T-Echo: `#osmstatus` y un `#osmnote` de prueba.
6. Etiquetar la SD y la caja: versión del software, región LoRa, contacto del operador.
7. Ejecutar `bash scripts/health_check.sh` y guardar la salida.

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

Desde la mesh (sin SSH ni pantalla):

```
#osmstatus
```

Ejemplo de respuesta:

```
ℹ️ Gateway activo
Internet: ✅ OK
Cola: 3 (tuyas: 1)
Hoy: 12 enviadas / 15 nuevas
Último envío: hace 4 min (#456789)
Errores en cola: 0
```

**Regla operativa:** con solo el teléfono (Meshtastic) debe bastar para saber si el puente está sano.

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

### Quién usa qué

| Rol | Acceso | Herramienta |
|-----|--------|-------------|
| Solo app Meshtastic (sin SSH / sin pantalla) | Mesh | `#osmstatus` **enriquecido** (Internet, cola, hoy, último envío, errores) |
| Coordinador con SSH / teclado en la Pi | Consola | Scripts abajo (manual o timer systemd) |

`#osmstatus` **no** llama a `mission_report.sh`. Son canales distintos: el status es un resumen corto por DM LoRa; el mission report es un informe largo en la Pi (tablas + logs) para archivar o donantes.

### Informe de misión (manual)

```bash
bash scripts/mission_report.sh
bash scripts/mission_report.sh --out /var/lib/lora-osmnotes/reports/mission-$(date +%Y%m%d).txt
```

Resumen: totales, pendientes, enviadas, errores, últimas notas, pistas de log.

### Export CSV / JSON (manual)

```bash
bash scripts/export_notes.sh
# → /var/lib/lora-osmnotes/exports/notes-YYYYMMDD-HHMMSS.csv

bash scripts/export_notes.sh --format json --out /tmp/notes.json
bash scripts/export_notes.sh --status pending
```

**Privacidad:** revisar `text_original` antes de compartir con terceros.

### Logs

```bash
sudo journalctl -u lora-osmnotes -n 100 --no-pager
sudo journalctl -u lora-osmnotes --since today | grep -iE 'error|sent|Created note'
```

---

## 7. Resiliencia de despliegue

### Modelo mental

| Escenario | Qué importa |
|-----------|-------------|
| Hay Internet | La nota sube a OSM; OSM es la copia “buena”. Perder la SD duele poco para lo **ya enviado**. |
| Sin Internet / cola `pending` | La DB local es crítica. Si se corrompe la SD, se pierden reportes no subidos. |
| Apagón | Al volver la energía, systemd reinicia el gateway; los `pending` deberían reintentarse. UPS/power bank reduce apagones bruscos. |
| SD parcialmente corrupta | Un **backup periódico de la DB** en carpeta conocida (o USB) mitiga la pérdida de la cola. |

### Dónde están los backups (fácil de encontrar)

Ruta canónica en la Pi:

```
/var/lib/lora-osmnotes/
  gateway.db          # base en vivo
  backups/            # snapshots gateway-YYYYMMDD-HHMMSS.db
  exports/            # CSV/JSON de misión
  reports/            # informes de texto
  README-BACKUP.txt   # nota para quien abre el disco en otra máquina
```

### Backup manual

```bash
bash scripts/backup_db.sh
# → /var/lib/lora-osmnotes/backups/gateway-….db

# Copia extra a USB montada (recomendado si hay cola offline larga)
bash scripts/backup_db.sh --usb /media/pi/NOMBRE_USB
```

### Backup diario automático

```bash
sudo bash scripts/install_backup_timer.sh
# Habilita systemd timer diario → misma carpeta backups/
sudo systemctl start lora-osmnotes-backup.service   # prueba inmediata
```

### Extraer el backup desde otra máquina

1. Apagar la Pi, sacar la microSD (o el USB de backups).
2. Montarla en un PC; abrir `/var/lib/lora-osmnotes/backups/` (o `…/lora-osmnotes-backups/` en el USB).
3. Copiar el `.db` más reciente.
4. En una Pi de reemplazo: detener servicio, poner el archivo como `gateway.db`, arrancar servicio.

### Energía

- **Recomendado:** power bank como UPS — toma → power bank → Pi (passthrough). Ver [FIELD_DEPLOYMENT_GUIDE.md](FIELD_DEPLOYMENT_GUIDE.md).
- Reduce apagones bruscos y corrupción de SD.
- No sustituye el backup si operas muchos días offline.

### Otros

| Riesgo | Mitigación |
|--------|------------|
| Servicio caído | `Restart=always` + `health_check.sh` |
| Reloj incorrecto | [TIME_CONFIGURATION.md](TIME_CONFIGURATION.md) |
| Segunda SD | Llevar una SD ya instalada de repuesto |

---

## 8. Canal y seguridad por contexto

### Despliegue de referencia (MVP)

- Región: **ANZ** (Colombia y varios países LATAM según tabla Meshtastic; no confundir con US). Override: `LORA_REGION` en `.env`.
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
