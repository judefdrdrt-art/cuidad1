from flask_login import UserMixin
from datetime import datetime
# Shared extensions – db instance
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

class Zona(db.Model):
    __tablename__ = 'zonas'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text)
    sensores = db.relationship('SensorSonido', backref='zona', lazy=True)


class SensorSonido(db.Model):
    __tablename__ = 'sensores_sonido'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    zona_id = db.Column(db.Integer, db.ForeignKey('zonas.id'), nullable=False)
    ubicacion = db.Column(db.String(200))
    mediciones = db.relationship('MedicionSonido', backref='sensor', lazy=True)

class MedicionSonido(db.Model):
    __tablename__ = 'mediciones_sonido'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensores_sonido.id'), nullable=False)
    nivel_db = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class EventoSonido(db.Model):
    __tablename__ = 'eventos_sonido'
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensores_sonido.id'), nullable=False)
    descripcion = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Alerta(db.Model):
    __tablename__ = 'alertas'
    id = db.Column(db.Integer, primary_key=True)
    zona_id = db.Column(db.Integer, db.ForeignKey('zonas.id'), nullable=False)
    nivel = db.Column(db.Float, nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Contenedor(db.Model):
    __tablename__ = 'contenedores'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    capacidad_litros = db.Column(db.Float, nullable=False)
    nivel_actual = db.Column(db.Float, default=0.0)
    ubicacion = db.Column(db.String(200))
    lecturas = db.relationship('LecturaContenedor', backref='contenedor', lazy=True)

class LecturaContenedor(db.Model):
    __tablename__ = 'lecturas_contenedor'
    id = db.Column(db.Integer, primary_key=True)
    contenedor_id = db.Column(db.Integer, db.ForeignKey('contenedores.id'), nullable=False)
    nivel = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20), unique=True, nullable=False)
    modelo = db.Column(db.String(50))
    propietario = db.Column(db.String(100))

class EspacioParqueadero(db.Model):
    __tablename__ = 'espacios_parqueadero'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    disponible = db.Column(db.Boolean, default=True)

class AccesoParqueadero(db.Model):
    __tablename__ = 'accesos_parqueadero'
    id = db.Column(db.Integer, primary_key=True)
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculos.id'), nullable=False)
    espacio_id = db.Column(db.Integer, db.ForeignKey('espacios_parqueadero.id'), nullable=False)
    ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    salida = db.Column(db.DateTime)

class SerialLog(db.Model):
    __tablename__ = 'serial_log'
    id = db.Column(db.Integer, primary_key=True)
    mensaje = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
