# Cómo Validar que los Dispositivos Están en la Misma Red Mesh

## Opción 1: Usar un Solo Celular (Más Simple)

**Con la app Meshtastic:**

1. **Conecta el celular al T-Echo** (por Bluetooth o USB)
2. Abre la app Meshtastic
3. Envía un mensaje de prueba desde el celular
4. **Desconecta el celular del T-Echo**
5. **Conecta el celular al Heltec V3** (por Bluetooth o USB)
6. Verifica si el mensaje aparece en el Heltec V3

**Si el mensaje aparece en ambos dispositivos**, están en la misma red mesh.

## Opción 2: Usar el T-Echo para Verificar

1. **Desde el T-Echo**, envía un mensaje de prueba (cualquier texto)
2. **Observa el Heltec V3**:
   - Si tiene pantalla, debería mostrar el mensaje
   - Si no tiene pantalla, usa la app Meshtastic conectada al Heltec V3 para ver si recibió el mensaje

## Opción 3: Verificar Configuración Manualmente

**En el T-Echo:**
- Menú → Configuración → Canal
- Anota: Channel Name, Channel Index, Region

**En el Heltec V3 (usando app Meshtastic):**
- Conecta el celular al Heltec V3
- App → Configuración → Canal
- Compara: Channel Name, Channel Index, Region deben ser **iguales**

## Opción 4: Instalar meshtastic CLI (Para Verificación Técnica)

```bash
# Instalar meshtastic CLI
pip3 install meshtastic

# Verificar configuración del Heltec V3
meshtastic --port /dev/ttyUSB0 --info

# Ver nodos en la red
meshtastic --port /dev/ttyUSB0 --nodes
```

## Opción 5: Test de Broadcast (Más Confiable)

1. **Desde el T-Echo**, envía un mensaje broadcast (mensaje normal sin destinatario)
2. **Verifica en el Heltec V3** si lo recibió
3. **Desde el Heltec V3**, envía un mensaje broadcast
4. **Verifica en el T-Echo** si lo recibió

Si ambos se reciben mensajes mutuamente, **definitivamente están en la misma red**.

## Problema Actual del Gateway

**Importante:** El gateway actual es un MVP que espera mensajes en formato texto simplificado, pero Meshtastic real usa protobuf. Por eso no está recibiendo los mensajes del T-Echo.

**Para solucionarlo**, necesitas:
1. Instalar `meshtastic-python`: `pip install meshtastic`
2. Modificar el código para usar `meshtastic.serial_interface.SerialInterface()`

Esto permitirá recibir mensajes reales en formato protobuf.
