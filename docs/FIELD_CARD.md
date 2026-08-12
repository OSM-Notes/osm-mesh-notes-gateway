# Tarjeta de campo — OSM Mesh Notes

**Imprimir 1 página · plastificar si es posible · una por reportero**

---

## Español

### Crear un reporte

1. Enciende el T-Echo **al aire libre** y espera **30–60 segundos** (GPS).
2. App Meshtastic: región LoRa = **ANZ** (Colombia), mismo canal que el gateway.
3. Envía:

```
#osmnote <tu mensaje>
```

Ejemplo: `#osmnote Puente agrietado, solo peatones.`

**Consejo:** Quick Chat → agrega `#osmnote` → desactiva “Instantly send” (Append).

### Qué vas a recibir (mensaje directo)

| Situación | Idea del mensaje |
|-----------|------------------|
| Hay Internet | Nota creada en OSM + enlace |
| Sin Internet | Quedó en cola `Q-XXXX` (se envía después) |
| Sin GPS / GPS viejo (&gt;2 min) | Rechazo: espera y reenvía |
| Mismo texto reenviado al instante | “Ya estaba registrado” |

### Otros comandos

| Comando | Para qué |
|---------|----------|
| `#osmhelp` | Ayuda |
| `#osmstatus` | Estado del gateway (Internet, cola, enviadas hoy, último envío) |
| `#osmlist` | Tus últimas notas |
| `#osmlang es` / `#osmlang en` | Idioma |

### No uses esto para

- Emergencias médicas o rescate
- Datos personales (nombres, teléfonos, direcciones de casa)
- Información de menores o sobrevivientes identificables

Las notas en OpenStreetMap son **públicas**. El canal de radio puede ser escuchado por otros.

**Operador del gateway:** _________________ **Contacto:** _________________

---

## English

### Send a report

1. Power on the T-Echo **outdoors** and wait **30–60 seconds** (GPS).
2. Meshtastic app: LoRa region **ANZ** (Colombia default), same channel as the gateway.
3. Send:

```
#osmnote <your message>
```

**Tip:** Quick Chat → add `#osmnote` → turn off “Instantly send”.

### Useful commands

`#osmhelp` · `#osmstatus` · `#osmlist` · `#osmlang en`

### Do not use for

Medical emergencies · personal data · identifiable survivors. OSM notes are **public**.

**Gateway operator:** _________________ **Contact:** _________________
