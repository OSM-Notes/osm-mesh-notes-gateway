#!/bin/bash
# Script para verificar configuración del canal Meshtastic
# Uso: sudo ./verificar_canal.sh

echo "=== Verificación de Canal Meshtastic ==="
echo ""
echo "Deteniendo servicio gateway temporalmente..."
sudo systemctl stop lora-osmnotes
sleep 2

echo ""
echo "Información del Heltec V3:"
echo "=========================="
sudo /opt/lora-osmnotes/bin/meshtastic --port /dev/ttyUSB0 --info 2>&1 | grep -A 50 "Channels:" | head -30

echo ""
echo "Nodos en la red:"
echo "================"
sudo /opt/lora-osmnotes/bin/meshtastic --port /dev/ttyUSB0 --nodes 2>&1 | head -20

echo ""
echo "Reiniciando servicio gateway..."
sudo systemctl start lora-osmnotes
sleep 2

echo ""
echo "=== Instrucciones ==="
echo "Compara esta información con la configuración del T-Echo:"
echo "- Channel Name debe ser igual"
echo "- Channel Index debe ser igual"
echo "- Region debe ser igual"
echo ""
echo "Si son diferentes, configura ambos dispositivos con los mismos valores."
