from flask import Blueprint, jsonify, request, render_template
from datetime import datetime
from flask_login import login_required
from models import EspacioParqueadero, AccesoParqueadero, Vehiculo
from extensions import db

parking_bp = Blueprint('parking', __name__, url_prefix='/parking')

@parking_bp.route('/')
@login_required
def parking():
    # Render the parking management page
    return render_template('parqueadero.html')

@parking_bp.route('/data')
@login_required
def parking_data():
    # Return JSON with current status of parking spaces
    spaces = EspacioParqueadero.query.all()
    data = [{
        'codigo': s.codigo,
        'disponible': s.disponible
    } for s in spaces]
    return jsonify(data)

@parking_bp.route('/ingresar', methods=['POST'])
@login_required
def ingresar():
    # Verificar si el parqueadero está COMPLETAMENTE LLENO
    libres_count = EspacioParqueadero.query.filter_by(disponible=True).count()
    if libres_count == 0:
        return jsonify({
            'error': '¡El parqueadero está COMPLETAMENTE LLENO! No se permiten nuevos ingresos hasta que se libere algún espacio.'
        }), 400

    # Expect JSON {"placa": "ABC123", "espacio": "P01"}
    payload = request.get_json() or {}
    placa = (payload.get('placa') or '').strip().upper()
    codigo = (payload.get('espacio') or '').strip().upper()

    if not placa or not codigo:
        return jsonify({'error': 'La placa y el código de espacio son obligatorios.'}), 400

    # Find or create vehicle
    vehiculo = Vehiculo.query.filter_by(placa=placa).first()
    if not vehiculo:
        vehiculo = Vehiculo(placa=placa)
        db.session.add(vehiculo)
        db.session.commit()

    # Find parking space
    espacio = EspacioParqueadero.query.filter_by(codigo=codigo, disponible=True).first()
    if not espacio:
        return jsonify({'error': f'El espacio {codigo} no está disponible.'}), 400

    # Register entry
    acceso = AccesoParqueadero(vehiculo_id=vehiculo.id, espacio_id=espacio.id)
    espacio.disponible = False
    db.session.add(acceso)
    db.session.commit()

    # Construir comando hacia el Arduino para abrir el parqueadero / talanquera
    cmd_text = f"PARK_OPEN|{codigo}|{placa}"

    # 1. Enviar vía SocketIO a clientes con WebSerial activo
    from extensions import socketio
    socketio.emit('send_arduino_command', {
        'command': cmd_text,
        'action': 'open_gate',
        'espacio': codigo,
        'placa': placa
    })

    # 2. Intentar enviar directamente por puerto COM serie si la instancia global existe
    try:
        from app import serial_reader
        if serial_reader:
            serial_reader.write_line(cmd_text)
    except Exception as e:
        print(f"[Parking] No se pudo enviar por serial_reader directo: {e}")

    return jsonify({
        'status': 'ok',
        'command_sent': cmd_text,
        'message': f'Registro exitoso. Comando enviado al Arduino: {cmd_text}'
    })


@parking_bp.route('/salir', methods=['POST'])
@login_required
def salir():
    # Expect JSON {"placa": "ABC123"}
    payload = request.get_json() or {}
    placa = payload.get('placa')
    vehiculo = Vehiculo.query.filter_by(placa=placa).first()
    if not vehiculo:
        return jsonify({'error': 'Vehículo no encontrado'}), 404
    # Find active access record
    acceso = AccesoParqueadero.query.filter_by(vehiculo_id=vehiculo.id, salida=None).first()
    if not acceso:
        return jsonify({'error': 'No hay ingreso activo'}), 400
    # Release space
    espacio = db.session.get(EspacioParqueadero, acceso.espacio_id)
    if espacio:
        espacio.disponible = True
    acceso.salida = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'ok'})
