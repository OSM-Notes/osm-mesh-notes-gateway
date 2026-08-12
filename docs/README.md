# Índice de documentación

| Documento | Contenido |
|-----------|-----------|
| [spec.md](spec.md) | **Especificación canónica** (decisiones de producto/comportamiento) |
| [ADOPTION.md](ADOPTION.md) | **Adopción humanitaria** (despliegue, ética, operación, backups) |
| [ROADMAP.md](ROADMAP.md) | Prioridades Must / Should / Later + checklist de release |
| [FIELD_CARD.md](FIELD_CARD.md) | Tarjeta imprimible para reporteros (es/en) |
| [SD_IMAGE_RELEASE.md](SD_IMAGE_RELEASE.md) | Cómo generar y subir `.img.xz` a GitHub Releases |
| [architecture.md](architecture.md) | Componentes, flujos y threading |
| [message-format.md](message-format.md) | Protocolo Meshtastic (protobuf) y dict interno |
| [API.md](API.md) | Referencia de API interna Python |
| [EXAMPLES.md](EXAMPLES.md) | Ejemplos de uso en campo |
| [FIELD_DEPLOYMENT_GUIDE.md](FIELD_DEPLOYMENT_GUIDE.md) | Checklist de despliegue |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Diagnóstico operativo |
| [SECURITY.md](SECURITY.md) | Seguridad operativa |
| [TIME_CONFIGURATION.md](TIME_CONFIGURATION.md) | Tiempo / NTP / corrección de timestamps |
| [DEDUP_API_EXTENSIONS.md](DEDUP_API_EXTENSIONS.md) | Futuro: dedupe entre gateways |
| [OUT_OF_SCOPE_MOBILE_GATEWAY.md](OUT_OF_SCOPE_MOBILE_GATEWAY.md) | Fuera de alcance: gateway móvil |

Guía de usuario e instalación: [`../README.md`](../README.md).

Scripts de operación:
- [`../scripts/health_check.sh`](../scripts/health_check.sh) — salud
- [`../scripts/mission_report.sh`](../scripts/mission_report.sh) — informe de misión
- [`../scripts/export_notes.sh`](../scripts/export_notes.sh) — export CSV/JSON
- [`../scripts/backup_db.sh`](../scripts/backup_db.sh) — backup de la DB
- [`../scripts/install_backup_timer.sh`](../scripts/install_backup_timer.sh) — timer diario
