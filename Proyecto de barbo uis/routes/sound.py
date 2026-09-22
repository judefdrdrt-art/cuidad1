from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from models import MedicionSonido

sound_bp = Blueprint('sound', __name__, url_prefix='/sound')

@sound_bp.route('/')
@login_required
def sound():
    # Render the sound monitoring page
    return render_template('sonido.html')

@sound_bp.route('/data')
@login_required
def sound_data():
    # Return JSON data for recent sound measurements (last 30 entries)
    measurements = (MedicionSonido.query
                    .order_by(MedicionSonido.timestamp.desc())
                    .limit(30)
                    .all())
    data = [{
        'sensor_id': m.sensor_id,
        'nivel_db': m.nivel_db,
        'timestamp': m.timestamp.isoformat()
    } for m in measurements]
    return jsonify(data)


