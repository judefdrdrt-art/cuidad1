# Ciudad Inteligente UIS - Plataforma IoT de Monitoreo Urbano

Plataforma web en tiempo real para el monitoreo y gestión de subsistemas IoT en el campus de la **Universidad Industrial de Santander (UIS)**.

## 🚀 Características Principales

1. **Monitoreo de Sonido:** Medición en tiempo real de contaminación acústica (decibeles) con alertas de niveles críticos.
2. **Entrada y Salida de Materiales (Parqueadero):**
   - Control automatizado de plazas de estacionamiento.
   - Transmisión serie al Arduino (`PARK_OPEN|<espacio>|<placa>`) al registrar vehículos.
   - Bloqueo automático de registros cuando el parqueadero está **COMPLETAMENTE LLENO** (0 plazas libres).
3. **Gestión del Vertedero de Basura:**
   - Visualización en tiempo real del porcentaje de llenado del Vertedero Principal UIS.
   - Alerta animada en rojo de **COMPLETAMENTE LLENO** (100%).
   - Botón de vaciado del vertedero a 0% y limpieza del historial.
4. **Conexión Serial Arduino:**
   - Compatible con puerto COM físico local (`COM3`/`COM5`) y WebSerial USB directo desde navegadores Google Chrome y Microsoft Edge.

---

## 🛠️ Despliegue en Render (Render Web Service)

### Configuración Automática en Render:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn --worker-class eventlet -w 1 app:app`
- **Environment:** `Python 3`

### Variables de Entorno Recomendadas:
- `SECRET_KEY`: `tu-clave-secreta-uis-2026`
- `FLASK_ENV`: `production`

---

## 💻 Desarrollo Local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar servidor local
python app.py
```

Acceder en el navegador a `http://localhost:5000` con el usuario por defecto:
- **Usuario:** `rut1234`
- **Contraseña:** `securepassword`
