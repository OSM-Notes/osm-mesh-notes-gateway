# Roadmap

Prioridades para adopción humanitaria y extensiones técnicas.  
Alineado con [ADOPTION.md](ADOPTION.md) y la especificación [spec.md](spec.md).

Leyenda:
- **Must** — bloquea adopción seria sin el autor del software presente
- **Should** — alto valor, mismo producto (gateway fijo)
- **Later** — otro producto o dependencia externa

---

## Must (adopción)

| Ítem | Estado | Notas |
|------|--------|--------|
| Spec canónica + docs alineadas al código | Hecho | `docs/spec.md`, architecture, message-format |
| Guía de adopción humanitaria | Hecho | `docs/ADOPTION.md` |
| Tarjeta de campo imprimible | Hecho | `docs/FIELD_CARD.md` |
| Script de salud operativa | Hecho | `scripts/health_check.sh` |
| Modo entrenamiento documentado (`DRY_RUN`) | Hecho (código ya existía) | ADOPTION §4 |
| Ética / do-no-harm operativa | Hecho (documento) | ADOPTION §5 |
| Checklist de release versionado | Hecho (proceso) | ver § Release abajo |
| Informe de misión + export CSV/JSON | Hecho | `scripts/mission_report.sh`, `scripts/export_notes.sh` |
| Backup DB + timer diario opcional | Hecho | `scripts/backup_db.sh`, `install_backup_timer.sh`, `systemd/lora-osmnotes-backup.*` |
| Imagen microSD preconfigurada + checksum | Scripts listos; artefacto pendiente | `prepare_golden_pi.sh` + `build_sd_image.sh` + [SD_IMAGE_RELEASE.md](SD_IMAGE_RELEASE.md) |
| Guía PSK / canal dedicado por operación | Hecho (operativa) | ADOPTION §8 |

---

## Should (mismo repo)

| Ítem | Valor humanitario | Estado |
|------|-------------------|--------|
| Plantillas de reporte (`#osmnote derrumbe`, etc.) | Menos errores de tipeo | Pendiente |
| Usar HDOP / precisión GPS en validación | Menos notas con cold-start malo | Pendiente |
| Estado `failed` + reintento / visibilidad | Recuperar cola sin SSH | Pendiente |
| Dashboard HTML local read-only | Coordinación en puesto base | Pendiente |
| OAuth OSM opcional | Notas atribuibles a org | Pendiente |
| Export / informe de misión | Informes post-día | Hecho (`mission_report` / `export_notes`) |
| Backup DB + timer | Mitigar corrupción SD de la cola | Hecho |
| Enriquecer `#osmstatus` | Coordinación solo por mesh (sin SSH) | Hecho |
| Más idiomas (`.po` + FIELD_CARD) | Operaciones fuera de es/en | Pendiente |
| Watchdog HW documentado | Despliegues solares largos | Pendiente menor |

---

## Later (ecosistema / otro producto)

| Ítem | Dónde |
|------|--------|
| Dedupe global entre gateways | [DEDUP_API_EXTENSIONS.md](DEDUP_API_EXTENSIONS.md) + OSM-Notes-API |
| Gateway móvil (teléfono store-and-forward) | [OUT_OF_SCOPE_MOBILE_GATEWAY.md](OUT_OF_SCOPE_MOBILE_GATEWAY.md) |
| Mapa/listado “notas desde mesh” | Capa web OSM-Notes |
| Allowlist de nodos / roles | Cuando el canal abierto no sea aceptable |
| Multimedia / fotos | Fuera del presupuesto útil de LoRa |
| Integración HOT Tasking Manager / uMap | Evitar diluir el MVP del gateway |

---

## Release checklist (cada versión estable)

Copiar a la descripción del release de GitHub:

```markdown
## Summary
- …

## Adoption
- [ ] Tag vX.Y.Z
- [ ] CHANGELOG [Unreleased] → versión fechada
- [ ] docs/spec.md revisada vs código
- [ ] CI verde
- [ ] install_pi.sh probado en Pi limpia (o nota de versión mínima de OS)
- [ ] FIELD_CARD y ADOPTION sin contradicciones
- [ ] Limitaciones conocidas listadas (GPS 120s, canal, anonimato OSM)

## Test plan
- [ ] #osmstatus / #osmnote online
- [ ] #osmnote offline → cola → envío al restaurar red
- [ ] Duplicado inmediato → ACK duplicate
- [ ] GPS stale (>120s) → rechazo
- [ ] DRY_RUN=true en taller (documentado)
- [ ] bash scripts/health_check.sh → exit 0 en setup sano
```

---

## Principio

> La siguiente versión “adoptable” no es más comandos mesh: es **kit de despliegue + confianza + operabilidad**.  
> Extensiones grandes (dedupe global, mobile gateway) solo cuando el gateway fijo se instala y opera sin el autor presente.
