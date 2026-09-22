from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from models import Contenedor, LecturaContenedor
from extensions import db, socketio
from serial_service.parser import parse_line
from serial_service.commands import dispatch_command

trash_bp = Blueprint('trash', __name__, url_prefix='/basura')

@trash_bp.route('/')
@login_required
def trash():
    # Renderizar la vista de gestión de residuos y basura
    return render_template('basura.html')

@trash_bp.route('/data')
@login_required
def trash_data():
    # Obtener estado actual de todos los contenedores
    contenedores = Contenedor.query.all()
    result = []
    has_full = False
    full_containers = []

    for c in contenedores:
        is_full = c.nivel_actual >= 100.0
        if is_full:
            has_full = True
            full_containers.append(c.codigo)

        result.append({
            'id': c.id,
            'codigo': c.codigo,
            'capacidad_litros': c.capacidad_litros,
            'nivel_actual': round(c.nivel_actual, 1),
            'ubicacion': c.ubicacion or f'Punto Recolección {c.codigo}',
            'is_full': is_full,
            'estado': 'COMPLETAMENTE LLENO' if is_full else ('Precaución' if c.nivel_actual >= 80 else 'Normal')
        })

    # Lecturas recientes
    lecturas = (LecturaContenedor.query
                .order_by(LecturaContenedor.timestamp.desc())
                .limit(20)
                .all())
    lecturas_data = [{
        'contenedor_codigo': l.contenedor.codigo if l.contenedor else f'ID-{l.contenedor_id}',
        'nivel': round(l.nivel, 1),
        'timestamp': l.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for l in lecturas]

    return jsonify({
        'contenedores': result,
        'lecturas': lecturas_data,
        'has_full': has_full,
        'full_containers': full_containers
    })

@trash_bp.route('/simular', methods=['POST'])
@login_required
def simular():
    # Permite probar tramas como BIN|C01|100 o enviar JSON
    payload = request.get_json(silent=True) or {}
    raw_line = payload.get('raw', '').strip()
    
    if not raw_line:
        nivel = payload.get('nivel', 100)
        raw_line = f"BIN|{nivel}"


    parsed = parse_line(raw_line)
    dispatch_res = None
    if parsed:
        dispatch_res = dispatch_command(parsed)

    # Transmitir a todos los clientes por SocketIO
    socketio.emit('arduino_event', {
        'raw': raw_line,
        'parsed': parsed,
        'result': dispatch_res,
        'port': 'Simulador Web Basura'
    })

@trash_bp.route('/vaciar', methods=['POST'])
@login_required
def vaciar():
    # Resetear el Vertedero a 0%
    vertedero = Contenedor.query.first()
    if not vertedero:
        vertedero = Contenedor(
            codigo='VERTEDERO',
            capacidad_litros=500.0,
            nivel_actual=0.0,
            ubicacion='Vertedero Principal Campus UIS'
        )
        db.session.add(vertedero)
    else:
        vertedero.nivel_actual = 0.0

    lectura = LecturaContenedor(contenedor_id=vertedero.id, nivel=0.0)
    db.session.add(lectura)
    db.session.commit()

    socketio.emit('arduino_event', {
        'raw': 'BIN|0',
        'parsed': {'type': 'bin', 'contenedor_id': 'VERTEDERO', 'nivel': 0.0, 'is_full': False},
        'result': 'Vertedero de Basura vaciado: 0.0%',
        'port': 'Acción Web'
    })

    return jsonify({'status': 'ok', 'message': 'Vertedero de Basura vaciado y reseteado a 0%.'})

@trash_bp.route('/vaciar-historial', methods=['POST'])
@login_required
def vaciar_historial():
    # Eliminar todos los registros del historial de lecturas de basura
    LecturaContenedor.query.delete()
    db.session.commit()
    return jsonify({'status': 'ok', 'message': 'Historial de lecturas vaciado correctamente.'})

