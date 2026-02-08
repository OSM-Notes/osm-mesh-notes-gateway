#!/bin/bash
# Script para verificar configuración de red mesh Meshtastic
# Uso: ./verificar_mesh.sh

echo "=== Verificación de Red Mesh Meshtastic ==="
echo ""

# Verificar dispositivo serial
echo "1. Dispositivo serial conectado:"
if [ -e /dev/ttyUSB0 ]; then
    echo "   ✓ /dev/ttyUSB0 encontrado"
    ls -la /dev/ttyUSB0
else
    echo "   ✗ /dev/ttyUSB0 no encontrado"
    echo "   Buscando otros dispositivos..."
    ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "   No se encontraron dispositivos seriales"
fi
echo ""

# Verificar servicio
echo "2. Estado del servicio gateway:"
if systemctl is-active --quiet lora-osmnotes 2>/dev/null; then
    echo "   ✓ Servicio activo"
    systemctl status lora-osmnotes --no-pager | head -5
else
    echo "   ✗ Servicio no está activo"
fi
echo ""

# Verificar configuración
echo "3. Configuración del gateway:"
if [ -f /var/lib/lora-osmnotes/.env ]; then
    echo "   ✓ Archivo .env encontrado"
    echo "   SERIAL_PORT: $(grep SERIAL_PORT /var/lib/lora-osmnotes/.env | cut -d'=' -f2)"
    echo "   DAILY_BROADCAST_ENABLED: $(grep DAILY_BROADCAST_ENABLED /var/lib/lora-osmnotes/.env | cut -d'=' -f2)"
else
    echo "   ✗ Archivo .env no encontrado"
fi
echo ""

# Verificar mensajes recientes
echo "4. Mensajes recibidos (últimos 5 minutos):"
RECENT=$(journalctl -u lora-osmnotes --since '5 minutes ago' --no-pager | grep 'Received message' | wc -l)
echo "   Mensajes recibidos: $RECENT"
if [ "$RECENT" -gt 0 ]; then
    echo "   Últimos mensajes:"
    journalctl -u lora-osmnotes --since '5 minutes ago' --no-pager | grep 'Received message' | tail -3 | sed 's/^/     /'
else
    echo "   ⚠️  No se han recibido mensajes recientemente"
fi
echo ""

# Verificar si meshtastic-python está instalado
echo "5. Biblioteca meshtastic-python:"
if python3 -c "import meshtastic" 2>/dev/null; then
    echo "   ✓ meshtastic-python instalado"
    python3 -c "import meshtastic; print(f'   Versión: {meshtastic.__version__}')" 2>/dev/null || echo "   Versión: desconocida"
else
    echo "   ✗ meshtastic-python NO instalado"
    echo "   ⚠️  El código actual es MVP y espera formato texto simplificado"
    echo "   Para usar Meshtastic real, instala: pip install meshtastic"
fi
echo ""

# Instrucciones para validar mesh
echo "=== Cómo validar que están en la misma red mesh ==="
echo ""
echo "Desde el T-Echo:"
echo "1. Envía un mensaje de prueba normal (sin #osmhelp)"
echo "2. Verifica que el Heltec V3 lo recibe"
echo "3. Si se reciben, están en la misma red"
echo ""
echo "Desde el Heltec V3 (usando meshtastic CLI):"
echo "1. Conecta por USB y ejecuta: meshtastic --port /dev/ttyUSB0 --info"
echo "2. Verifica el 'Channel Name' y 'Channel Index'"
echo "3. Compara con el T-Echo (debe ser igual)"
echo ""
echo "Configuración común que debe coincidir:"
echo "- Channel Name (nombre del canal)"
echo "- Channel Index (índice del canal)"
echo "- Region (región LoRa)"
echo "- Hop Limit (límite de saltos)"
echo ""
echo "=== Nota importante ==="
echo "El código actual es un MVP que espera mensajes en formato texto."
echo "Meshtastic real usa protobuf. Para recibir mensajes reales,"
echo "necesitas usar la biblioteca meshtastic-python."
echo ""
