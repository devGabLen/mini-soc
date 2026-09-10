# Ingesta de tráfico real con tshark

Captura tráfico en vivo de tu máquina y lo inserta en `public.network_logs`,
usando un rol de Postgres dedicado (`sensor_ingest`) que **solo** puede
insertar en esa tabla — no puede leer nada, no puede tocar `incidents` ni
`alerts`, no puede hacer DDL.

## 1. Instalar tshark (si no lo tienes)

```bash
sudo apt install tshark -y
```

## 2. Ver tus interfaces disponibles

```bash
tshark -D
```

Vas a ver algo como `1. eth0`, `2. wlan0`, `3. lo`, etc.

## 3. Configurar

```bash
cd ingest
cp .env.example .env
```

Los defaults ya están calibrados con tu proyecto Supabase real.

## 4. Instalar dependencias

Puedes usar el mismo venv del backend (ya tiene `psycopg` instalado):

```bash
cd ..  # a la raíz del proyecto
source .venv/bin/activate.fish   # o el activate que uses
pip install python-dotenv
```

## 5. Correr

```bash
sudo python3 ingest/tshark_ingest.py --interface eth0
```

(usa el nombre real de tu interfaz, el que viste en `tshark -D`)

Vas a necesitar `sudo` para capturar paquetes, a menos que le des el permiso
una sola vez a `dumpcap` (el binario que tshark usa por debajo):

```bash
sudo setcap cap_net_raw,cap_net_admin+eip $(which dumpcap)
```

Con eso, ya no necesitas `sudo` para correr el script.

## 6. Generar algo "sospechoso" para probar

Deja el script corriendo en una terminal, y en OTRA terminal corre un
escaneo contra ti mismo (perfectamente legal, es tu propia máquina):

```bash
nmap -sT localhost
```

Vas a ver aparecer un montón de filas nuevas en la terminal del script —
eso es tráfico real llegando a `network_logs`. El motor de correlación
(lo que sigue después de esto) es lo que va a leer esas filas y decidir
si constituyen una alerta.

## Detener

`Ctrl+C` en la terminal donde corre el script.
