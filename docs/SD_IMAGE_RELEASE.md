# Publicar imagen de microSD en GitHub Releases

Guía operativa para generar y subir el artefacto `.img.xz` (no es un ISO).

## Visión del flujo

```
[PC] Flashear Raspberry Pi OS en microSD
        ↓
[Pi]  git clone / checkout tag
        ↓
[Pi]  sudo bash scripts/prepare_golden_pi.sh --tag vX.Y.Z
        ↓
[Pi]  shutdown → sacar SD
        ↓
[PC]  sudo bash scripts/build_sd_image.sh --device /dev/sdX --version vX.Y.Z [--upload]
        ↓
GitHub Release assets: *.img.xz + *.sha256
```

## Fase A — Pi dorada (en la Raspberry)

1. Flashear **Raspberry Pi OS** (manual, Imager).
2. Arrancar, red, `git clone` del repo (o copiar el checkout).
3. Ejecutar:

```bash
cd osm-mesh-notes-gateway   # o el nombre del clone
sudo bash scripts/prepare_golden_pi.sh --tag v0.2.0
```

Por defecto instala también el **timer diario de backup** (systemd, no cron) y deja el servicio **enabled** (arranque automático). Usa `--no-backup-timer` si no lo quieres.

## Qué es automático vs qué no

| Automático en la imagen | Sigue siendo del operador |
|-------------------------|---------------------------|
| Arranque del gateway al encender la Pi (`systemd`) | Enchufar Heltec/USB Meshtastic |
| Reintento de cola `pending` al volver Internet/energía | Dar Internet a la Pi cuando se quieran subir notas |
| Backup diario de la DB (máx. 14 copias) | Ajustar `SERIAL_PORT` si no es `/dev/ttyACM0` |
| Responder `#osmstatus` / `#osmnote` por mesh | Configurar región/canal en los nodos de campo |
| | Power bank / sitio físico |

“Nula administración” en la práctica = **no SSH ni pantalla para el día a día**. Sigue habiendo un setup físico de una vez (radio + red + corriente).

4. (Recomendado) Probar una vez con Heltec + `#osmstatus`, luego:

```bash
sudo systemctl stop lora-osmnotes
sudo shutdown -h now
```

5. Llevar la microSD al PC.

## Fase B — Imagen + checksum (+ upload) en un PC Linux

**Cuidado:** `--device` debe ser la SD. Un error borra el disco del PC.

```bash
# Identificar dispositivo
lsblk

sudo bash scripts/build_sd_image.sh \
  --device /dev/sdX \
  --version v0.2.0 \
  --upload \
  --repo OSM-Notes/osm-mesh-notes-gateway
```

Sin subir aún:

```bash
sudo bash scripts/build_sd_image.sh --device /dev/sdX --version v0.2.0
# Artefactos en ./dist/
gh release upload v0.2.0 dist/*.img.xz dist/*.sha256 --repo OSM-Notes/osm-mesh-notes-gateway
```

Requisitos en el PC: `dd`, `xz`, `sha256sum`; para `--upload`: [GitHub CLI](https://cli.github.com/) (`gh auth login`).

## Qué ve el usuario final

1. Descarga el `.img.xz` y el `.sha256` del Release.
2. Verifica: `sha256sum -c ….sha256`
3. Raspberry Pi Imager → Use custom → elige el `.img.xz` → flashea otra SD.
4. Arranca la Pi → lee `IMAGE_INFO.txt` → ajusta `.env` → `systemctl start lora-osmnotes`.

## Notas

- El `.img` refleja el **tamaño de la SD** usada (una SD de 32 GB genera un archivo grande aunque el sistema ocupe poco). Para imágenes más pequeñas usa una SD de 16 GB o herramientas de shrink (p. ej. PiShrink) antes de comprimir — fuera del alcance mínimo de estos scripts.
- **No hace falta** imagen para un release estable: basta tag + `install_pi.sh`. La imagen es el atajo para adopción no técnica.
- No subas el `.img` al repositorio git; solo a **Release assets**.
