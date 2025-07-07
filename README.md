# 📄 Harmony Listener — Instalación y despliegue

Este servicio es una API FastAPI con conexión a PostgreSQL, que almacena mensajes por `account_id` en schemas separados y filtra mensajes por `chat_id` configurables en un YAML.

---

## 🚀 Requisitos

* Linux (CentOS, Debian, Ubuntu…)
* Python ≥ 3.8 instalado
* PostgreSQL ≥ 12
* Acceso como root o sudo
* Conexión a internet para instalar dependencias

---

## 👤 Crear usuario dedicado

Por seguridad, no ejecutes el servicio como `root`.
Crea un usuario del sistema llamado `harmony` (sin login y sin home opcional):

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin harmony
```

Si prefieres darle home para poder acceder a su cache:

```bash
sudo useradd --system --create-home harmony
```

Verifica:

```bash
id harmony
```

---

## 📂 Preparar directorio

Ubica el código fuente en una ruta fija, por ejemplo `/opt/harmony`.
Copia los archivos (excluyendo `__pycache__` y `.venv`) con `rsync`:

```bash
sudo rsync -av --progress \
  --exclude '__pycache__' \
  --exclude '.venv' \
  evolution_listener/ /opt/harmony/listener/
```

Luego dale la propiedad al usuario `harmony`:

```bash
sudo chown -R harmony:harmony /opt/harmony
```

---

## 🐍 Crear entorno virtual (como `harmony`)

El entorno virtual **debe ser creado con el usuario `harmony`**, no como root:

```bash
sudo -u harmony python3 -m venv /opt/harmony/listener/.venv
```

Activar el venv y preparar dependencias:

```bash
sudo -u harmony /opt/harmony/listener/.venv/bin/pip install --upgrade pip
sudo -u harmony /opt/harmony/listener/.venv/bin/pip install -r /opt/harmony/listener/requirements.txt
```

---

## ⚙️ Configurar `.env`

Crea un archivo `.env` en la raíz del proyecto (`/opt/harmony/listener/.env`) con la configuración necesaria.

### 📄 Ejemplo:

```dotenv
# URL de conexión a la base de datos PostgreSQL
POSTGRES_URL=postgresql://usuario:password@host:puerto/dbname
```

Reemplaza `usuario`, `password`, `host`, `puerto` y `dbname` con tus valores reales.

---

## 🗂 Configurar `config.yaml`

Edita el archivo `config.yaml` con los `account_id`, `chat_id` permitidos y la bandera para loggear chats ignorados:

```yaml
filters:
  account_123:
    conversations:
      - 1203630000-1234567890@g.us
      - 1203630000-0987654321@g.us
  account_456:
    conversations:
      - 1203630000-1122334455@g.us
      - 1203630000-5566778899@g.us

logging:
  log_ignored_chats: true
```

Colócalo en `/opt/harmony/listener/config.yaml` o donde el código lo espere.

---

## 🔷 Crear script de arranque

Crea `/opt/harmony/listener/start.sh`:

```bash
#!/bin/bash
cd /opt/harmony/listener
source .venv/bin/activate
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

Hazlo ejecutable:

```bash
chmod +x /opt/harmony/listener/start.sh
```

---

## 🖋 Configurar systemd

Crea `/etc/systemd/system/harmony_listener.service`:

```ini
[Unit]
Description=Harmony Listener Service
After=network.target

[Service]
Type=simple
User=harmony
Group=harmony
WorkingDirectory=/opt/harmony/listener
ExecStart=/opt/harmony/listener/start.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

---

## 📡 Activar y arrancar el servicio

Recarga systemd:

```bash
sudo systemctl daemon-reload
```

Activa para que inicie con el sistema:

```bash
sudo systemctl enable harmony_listener.service
```

Arranca:

```bash
sudo systemctl start harmony_listener.service
```

Verifica estado:

```bash
sudo systemctl status harmony_listener.service
```

Verifica logs:

```bash
sudo journalctl -u harmony_listener.service -f
```

---

## 🌐 Endpoints disponibles

| Método | URL                    | Descripción                             |
| ------ | ---------------------- | --------------------------------------- |
| POST   | `/api/messages/handle` | Procesa un mensaje                      |
| GET    | `/api/status`          | Estado del servicio                     |
| GET    | `/config`              | Devuelve la configuración actual (JSON) |
| POST   | `/config/reload`       | Recarga la configuración desde YAML     |

---

## 📝 Notas

✅ El usuario `harmony` no tiene permisos para nada fuera de `/opt/harmony`.
✅ El `.venv` y todos los archivos deben ser propiedad y creados por `harmony`.
✅ PostgreSQL debe tener el usuario y base de datos configurados previamente.
✅ La URL de conexión está en `.env` y debe ser válida.
✅ Nunca uses `/root/.pyenv` ni crees el venv como root.
✅ Si `log_ignored_chats: true`, los `chat_id` ignorados aparecerán en los logs de systemd.
