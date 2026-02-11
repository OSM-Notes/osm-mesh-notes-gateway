# Guía de Despliegue en Terreno - Raspberry Pi Gateway

Esta guía describe los elementos necesarios y pasos para desplegar el gateway en terreno. **Es crítico revisar esta lista antes de salir a campo**, ya que olvidar elementos básicos puede hacer que el proyecto no sea utilizable.

---

## ⚠️ Checklist Pre-Salida

### Hardware Esencial

- [ ] **Raspberry Pi** (modelo 3 o superior recomendado)
- [ ] **Tarjeta microSD** con **Raspberry Pi OS (Raspbian) ya instalado** (mínimo 16GB, clase 10 o superior)
  - ⚠️ **IMPORTANTE**: La SD debe estar flasheada con Raspbian **antes de salir a terreno**
  - El gateway debe estar instalado y configurado en la SD
- [ ] **Fuente de alimentación** para Raspberry Pi (5V, mínimo 2.5A)
- [ ] **Dispositivo Meshtastic** (Heltec V3 u otro compatible)
- [ ] **Cable USB** para conectar Meshtastic al Raspberry Pi
- [ ] **Antena LoRa** para el dispositivo Meshtastic

### Elementos de Configuración y Acceso

- [ ] **Cable HDMI** - Para conectar a un televisor o monitor y ver la consola
- [ ] **Teclado USB** - Para entrada de comandos cuando se accede directamente
- [ ] **Mouse USB** - Para facilitar la navegación (opcional pero recomendado)
- [ ] **Computador portátil** - Para acceso SSH cuando la red es la misma
- [ ] **Cable de red Ethernet** (opcional) - Para conexión directa si hay router disponible

### Conectividad

- [ ] **Teléfono del administrador** con capacidad de compartir Internet (hotspot WiFi)
- [ ] **Cable de carga** para el teléfono (si se usa como hotspot)
- [ ] **Batería externa** (power bank) - Para alimentar Raspberry Pi si no hay toma eléctrica

### Herramientas y Accesorios

- [ ] **Cable de extensión USB** (si el cable del Meshtastic es corto)
- [ ] **Hub USB** (opcional) - Si necesitas conectar múltiples dispositivos
- [ ] **Cable de extensión HDMI** (opcional) - Si el monitor está lejos
- [ ] **Caja protectora** para Raspberry Pi (recomendado para campo)
- [ ] **Disipador de calor** (opcional pero recomendado para uso prolongado)

---

## Configuración Inicial en Terreno

### Paso 1: Conexión Física

1. **Conectar Meshtastic al Raspberry Pi**:
   - Conectar el dispositivo Meshtastic al puerto USB del Raspberry Pi
   - Verificar que la antena LoRa esté correctamente conectada

2. **Conectar periféricos** (si se accede directamente):
   - Conectar cable HDMI al televisor/monitor
   - Conectar teclado y mouse USB
   - Conectar fuente de alimentación

3. **Encender el Raspberry Pi**:
   - Esperar a que el sistema arranque completamente
   - Verificar que el LED de actividad parpadee normalmente

### Paso 2: Configuración de Red

#### Opción A: Acceso Directo (HDMI + Teclado)

1. **Verificar que el sistema arrancó**:
   ```bash
   # Verificar que estás en la consola
   uname -a
   ```

2. **Configurar WiFi** (si es necesario):
   ```bash
   sudo raspi-config
   # System Options → Wireless LAN → Configurar SSID y contraseña
   ```

3. **Verificar conexión**:
   ```bash
   ping -c 3 8.8.8.8
   ```

#### Opción B: Acceso por SSH desde Computador

**Requisito**: El computador y el Raspberry Pi deben estar en la misma red.

1. **Compartir Internet desde el teléfono**:
   - Activar hotspot WiFi en el teléfono del administrador
   - Anotar el nombre de la red (SSID) y contraseña

2. **Conectar Raspberry Pi al hotspot**:
   - Si ya está configurado: debería conectarse automáticamente
   - Si no: usar acceso directo (HDMI + teclado) para configurar WiFi

3. **Conectar computador al mismo hotspot**:
   - Conectar el computador al mismo hotspot WiFi del teléfono

4. **Encontrar la IP del Raspberry Pi**:
   ```bash
   # Desde el computador, escanear la red
   nmap -sn 192.168.43.0/24  # IP típica de hotspot Android
   # O desde el teléfono, verificar dispositivos conectados
   ```

5. **Conectar por SSH**:
   ```bash
   ssh pi@<IP_DEL_RASPBERRY>
   # O si el usuario es diferente:
   ssh angoca@<IP_DEL_RASPBERRY>
   ```

### Paso 3: Verificar Configuración del Gateway

1. **Verificar que el servicio está corriendo**:
   ```bash
   sudo systemctl status lora-osmnotes
   ```

2. **Verificar dispositivo serial**:
   ```bash
   ls -l /dev/ttyACM* /dev/ttyUSB*
   # Debería mostrar el dispositivo Meshtastic
   ```

3. **Verificar configuración**:
   ```bash
   cat /var/lib/lora-osmnotes/.env | grep SERIAL_PORT
   ```

4. **Ver logs en tiempo real**:
   ```bash
   sudo journalctl -u lora-osmnotes -f
   ```

---

## Solución de Problemas Comunes en Terreno

### No se puede acceder al Raspberry Pi

**Síntoma**: No hay respuesta por SSH ni se ve nada en HDMI.

**Soluciones**:
1. Verificar que el Raspberry Pi esté encendido (LED de actividad)
2. Si hay HDMI conectado pero pantalla negra: esperar más tiempo o reiniciar
3. Si SSH no funciona: verificar que ambos dispositivos están en la misma red
4. **Usar acceso directo**: Conectar HDMI + teclado para diagnóstico

### El dispositivo Meshtastic no se detecta

**Síntoma**: El servicio no puede conectarse al dispositivo serial.

**Verificar**:
```bash
# Ver dispositivos USB conectados
lsusb

# Ver dispositivos seriales
ls -l /dev/ttyACM* /dev/ttyUSB*

# Verificar permisos
ls -l /dev/ttyACM0  # Ajustar según tu dispositivo
```

**Soluciones**:
1. Desconectar y reconectar el cable USB
2. Verificar que el cable USB funciona (probar con otro dispositivo)
3. Verificar que el dispositivo Meshtastic está encendido
4. Revisar configuración de SERIAL_PORT en `.env`

### No hay Internet pero se necesita configurar

**Situación**: El Raspberry Pi necesita configuración pero no hay Internet.

**Soluciones**:
1. **Usar acceso directo**: HDMI + teclado para configurar localmente
2. **Compartir Internet del teléfono**: Activar hotspot y conectar Raspberry Pi
3. **Usar computador como puente**: Si el computador tiene Internet, compartir conexión

### El servicio no inicia

**Verificar**:
```bash
# Ver estado del servicio
sudo systemctl status lora-osmnotes

# Ver logs de error
sudo journalctl -u lora-osmnotes -n 50

# Verificar permisos
ls -l /var/lib/lora-osmnotes
```

**Soluciones comunes**:
1. Verificar que el usuario del servicio tiene permisos
2. Verificar que el dispositivo serial existe y tiene permisos
3. Verificar que la base de datos no está corrupta

---

## Configuración de Red Alternativa

### Conexión Directa Computador-Raspberry Pi

Si no hay router disponible, puedes conectar directamente:

1. **Configurar IP estática en Raspberry Pi**:
   ```bash
   sudo nano /etc/dhcpcd.conf
   # Agregar:
   interface eth0
   static ip_address=192.168.1.1/24
   ```

2. **Configurar IP estática en computador**:
   - Windows: Configuración de red → Propiedades → IPv4 → 192.168.1.2
   - Linux: `sudo ip addr add 192.168.1.2/24 dev eth0`

3. **Conectar por SSH**:
   ```bash
   ssh pi@192.168.1.1
   ```

### Usar Teléfono como Router WiFi

**Android**:
1. Configuración → Red e Internet → Hotspot y anclaje a red
2. Activar "Hotspot Wi‑Fi"
3. Configurar nombre y contraseña
4. Conectar Raspberry Pi y computador al mismo hotspot

**iPhone**:
1. Configuración → Compartir Internet
2. Activar "Compartir Internet"
3. Conectar dispositivos al hotspot creado

---

## Verificación Rápida en Terreno

Una vez desplegado, verificar que todo funciona:

```bash
# 1. Verificar servicio
sudo systemctl status lora-osmnotes

# 2. Verificar dispositivo Meshtastic
ls -l /dev/ttyACM* /dev/ttyUSB*

# 3. Ver logs recientes
sudo journalctl -u lora-osmnotes --since "5 minutes ago"

# 4. Verificar mensajes recibidos
sudo journalctl -u lora-osmnotes | grep "Received message" | tail -5

# 5. Verificar notas en cola
sudo sqlite3 /var/lib/lora-osmnotes/gateway.db "SELECT COUNT(*) FROM notes WHERE status='pending';"

# 6. Probar comando desde dispositivo Meshtastic
# Enviar: #osmstatus
# Debería responder con estado del gateway
```

---

## Elementos Críticos que NO se Pueden Olvidar

### 🔴 Críticos (sin estos, el proyecto NO funciona)

1. **Cable USB para Meshtastic** - Sin esto, no hay comunicación
2. **Fuente de alimentación** - El Raspberry Pi necesita energía
3. **Tarjeta microSD con sistema** - Debe tener el sistema operativo y el gateway instalado
4. **Antena LoRa** - Sin antena, el alcance es muy limitado

### 🟡 Importantes (dificultan mucho el trabajo sin ellos)

1. **Cable HDMI** - Para acceso directo cuando SSH no funciona
2. **Teclado USB** - Para entrada de comandos en acceso directo
3. **Teléfono con hotspot** - Para compartir Internet y configurar
4. **Computador portátil** - Para acceso SSH y diagnóstico

### 🟢 Recomendados (facilitan el trabajo)

1. **Mouse USB** - Facilita la navegación
2. **Cable de extensión USB** - Para mayor flexibilidad
3. **Batería externa** - Para operación sin toma eléctrica
4. **Caja protectora** - Protege el Raspberry Pi en campo

---

## Notas Adicionales

### Preparación Antes de Salir

1. **Flashear SD con Raspberry Pi OS**: 
   - Usar Raspberry Pi Imager para instalar Raspberry Pi OS (Raspbian)
   - Instalar el gateway usando `scripts/install_pi.sh`
   - Configurar WiFi si es necesario (o configurar en terreno)
   - Verificar que el servicio funciona correctamente

2. **Probar todo en casa primero**: 
   - Conectar todos los elementos y verificar que funcionan
   - Probar acceso SSH y acceso directo (HDMI + teclado)
   - Verificar que el dispositivo Meshtastic se detecta correctamente
   - Enviar un mensaje de prueba desde un dispositivo Meshtastic

3. **Cargar todos los dispositivos**: 
   - Teléfono, computador, batería externa
   - Verificar que la batería externa tiene suficiente capacidad

4. **Tener respaldo**: 
   - Llevar cables y adaptadores de repuesto si es posible
   - Considerar llevar una SD de respaldo con el sistema ya instalado

5. **Documentar configuración**: 
   - Anotar IPs, usuarios, contraseñas en lugar seguro
   - Anotar el puerto serial del dispositivo Meshtastic (`/dev/ttyACM0` o `/dev/ttyUSB0`)
   - Anotar configuración de WiFi si se usa

### En Terreno

1. **Proteger del clima**: Usar caja protectora si hay lluvia o polvo
2. **Verificar alimentación**: Asegurar fuente estable de energía
3. **Monitorear temperatura**: El Raspberry Pi puede sobrecalentarse en exteriores
4. **Tener plan B**: Si algo falla, tener alternativas (acceso directo vs SSH)

---

## Resumen de Comandos Útiles

```bash
# Estado del servicio
sudo systemctl status lora-osmnotes

# Reiniciar servicio
sudo systemctl restart lora-osmnotes

# Ver logs en tiempo real
sudo journalctl -u lora-osmnotes -f

# Ver logs recientes
sudo journalctl -u lora-osmnotes --since "10 minutes ago"

# Verificar dispositivo serial
ls -l /dev/ttyACM* /dev/ttyUSB*

# Ver configuración
cat /var/lib/lora-osmnotes/.env

# Ver estado de notas
sudo sqlite3 /var/lib/lora-osmnotes/gateway.db "SELECT status, COUNT(*) FROM notes GROUP BY status;"

# Verificar conexión a Internet
ping -c 3 api.openstreetmap.org

# Verificar tiempo del sistema
timedatectl status
```

---

Esta guía debe revisarse **antes de cada despliegue en terreno** para asegurar que todos los elementos necesarios están disponibles.
