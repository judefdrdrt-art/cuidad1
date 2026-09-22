from flask import Flask, redirect, url_for, request
from config import Config
from extensions import db, login_manager, socketio
from models import User, EspacioParqueadero, Contenedor

# Crear aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
socketio.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crear tablas y asegurar permisos de administrador en todas las cuentas
with app.app_context():

    db.create_all()
    # Garantizar que todas las cuentas existentes tengan derechos de administrador / desarrollador
    all_users = User.query.all()
    for u in all_users:
        if not u.is_admin:
            u.is_admin = True
    if all_users:
        db.session.commit()

    admin_username = 'rut1234'
    admin_email = 'rut1234@example.com'
    if not User.query.filter_by(username=admin_username).first():
        from werkzeug.security import generate_password_hash
        admin_user = User(
            username=admin_username,
            email=admin_email,
            password_hash=generate_password_hash('securepassword'),
            is_admin=True,
        )
        db.session.add(admin_user)
        db.session.commit()
        print('[Inicio] Usuario administrador creado (rut1234)')

    # Inicializar espacios de parqueadero por defecto si está vacío
    if EspacioParqueadero.query.count() == 0:
        for i in range(1, 9):
            codigo = f"P{i:02d}"
            nuevo_espacio = EspacioParqueadero(codigo=codigo, disponible=True)
            db.session.add(nuevo_espacio)
        db.session.commit()
        print('[Inicio] Espacios de parqueadero inicializados (P01 a P08)')

    # Asegurar que solo exista 1 único Vertedero de Basura en el sistema
    Contenedor.query.filter(Contenedor.codigo != 'VERTEDERO').delete()
    db.session.commit()

    if Contenedor.query.count() == 0:
        vertedero = Contenedor(
            codigo='VERTEDERO',
            capacidad_litros=500.0,
            nivel_actual=15.0,
            ubicacion='Vertedero Principal Campus UIS'
        )
        db.session.add(vertedero)
        db.session.commit()
        print('[Inicio] Vertedero de Basura único inicializado (VERTEDERO)')


# Iniciar lector serie local (intenta COM3 y COM5 si hay hardware conectado a la máquina servidor)
from serial_service.reader import SerialReader
serial_reader = SerialReader(socketio)
serial_reader.start()

# Registrar blueprints (rutas)
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.sound import sound_bp
from routes.parking import parking_bp
from routes.trash import trash_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(sound_bp)
app.register_blueprint(parking_bp)
app.register_blueprint(trash_bp)


# Receptor para datos del puerto serie enviados vía Web Serial API desde el navegador del Desarrollador
@socketio.on('web_serial_data')
def handle_web_serial_data(data):
    raw_line = data.get('raw', '').strip() if isinstance(data, dict) else str(data).strip()
    if raw_line:
        from serial_service.parser import parse_line
        from serial_service.commands import dispatch_command
        parsed = parse_line(raw_line)
        dispatch_result = None
        if parsed:
            dispatch_result = dispatch_command(parsed)
        # Emitir a todos los clientes conectados en tiempo real
        socketio.emit('arduino_event', {
            'raw': raw_line,
            'parsed': parsed,
            'result': dispatch_result,
            'port': data.get('port', 'WebSerial USB'),
        })

@socketio.on('connect')
def handle_connect():
    print('[SocketIO] Cliente conectado')

@socketio.on('disconnect')
def handle_disconnect():
    print('[SocketIO] Cliente desconectado')

# Endpoint API HTTP para empujar datos serie desde agentes externos si se requiere
@app.route('/api/serial/push', methods=['POST'])
def api_serial_push():
    payload = request.get_json(silent=True) or {}
    raw_line = payload.get('raw', '').strip()
    if raw_line:
        from serial_service.parser import parse_line
        from serial_service.commands import dispatch_command
        parsed = parse_line(raw_line)
        dispatch_result = None
        if parsed:
            dispatch_result = dispatch_command(parsed)
        socketio.emit('arduino_event', {
            'raw': raw_line,
            'parsed': parsed,
            'result': dispatch_result,
            'port': payload.get('port', 'API HTTP'),
        })
        return {'status': 'ok', 'result': dispatch_result}, 200
    return {'error': 'Formato inválido. Se requiere el campo raw.'}, 400

# Ruta principal – redirige al dashboard si está autenticado
@app.route('/')
def index():
    return redirect(url_for('dashboard.dashboard'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug_mode = app.config.get('DEBUG', False)
    print(f"[Servidor] Iniciando servidor en 0.0.0.0:{port}...")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode, allow_unsafe_werkzeug=True)

