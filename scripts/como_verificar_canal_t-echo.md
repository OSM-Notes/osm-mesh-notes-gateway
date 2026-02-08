# Cómo Verificar el Canal en el T-Echo

## Desde la App Meshtastic (Método Más Fácil)

1. **Conecta tu celular al T-Echo** (por Bluetooth o USB)
2. Abre la **app Meshtastic**
3. Ve a **Configuración** (Settings) → **Canal** (Channel)
4. Verás el **nombre del canal** (Channel Name)
5. Anota también el **Channel Index** y la **Region**

## Canales Comunes en Meshtastic

Los canales por defecto suelen ser:
- **LongFast** (canal por defecto más común)
- **LongSlow**
- **MediumFast**
- **MediumSlow**
- **ShortFast**
- **ShortSlow**

O puede ser un **canal personalizado** con un nombre específico que hayas creado.

## Comparar con el Heltec V3

Para ver qué canal usa el Heltec V3:

```bash
# Detener servicio temporalmente
sudo systemctl stop lora-osmnotes

# Ver información del canal
sudo /opt/lora-osmnotes/bin/meshtastic --port /dev/ttyUSB0 --info | grep -A 20 "Channels"

# Reiniciar servicio
sudo systemctl start lora-osmnotes
```

## Importante

**Ambos dispositivos DEBEN tener:**
- ✅ **Mismo Channel Name** (nombre del canal)
- ✅ **Mismo Channel Index** (índice del canal)
- ✅ **Misma Region** (región LoRa)

Si son diferentes, **no se comunicarán** aunque estén cerca.

## Si el Canal es Diferente

1. **Opción 1**: Cambiar el T-Echo para usar el mismo canal que el Heltec V3
   - App Meshtastic → Configuración → Canal → Seleccionar el mismo canal

2. **Opción 2**: Cambiar el Heltec V3 para usar el mismo canal que el T-Echo
   ```bash
   sudo systemctl stop lora-osmnotes
   sudo /opt/lora-osmnotes/bin/meshtastic --port /dev/ttyUSB0 --ch-set name "NOMBRE_DEL_CANAL"
   sudo systemctl start lora-osmnotes
   ```

## Nota sobre "Public"

Si ves "public" en algún lugar, podría ser:
- Un canal personalizado llamado "public"
- Una referencia a que el canal es público (no privado)
- Un nombre de canal específico que configuraste

Lo importante es que **ambos dispositivos usen exactamente el mismo nombre de canal**.
