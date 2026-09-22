import logging
from datetime import datetime
from extensions import db
from models import (
    SerialLog,
    Zona,
    SensorSonido,
    MedicionSonido,
    Contenedor,
    LecturaContenedor,
    Vehiculo,
    EspacioParqueadero,
    AccesoParqueadero,
)


def dispatch_command(data: dict) -> str:
    """Handle parsed serial commands and perform necessary actions (e.g., save to DB).
    Since this is called from background threads or WebSerial handlers, it requires an
    application context to interact with the database.
    """
    if not data:
        return "No data"

    from app import app

    with app.app_context():
        try:
            msg_type = data.get("type")

            # Save raw event to SerialLog for tracking
            new_log = SerialLog(mensaje=str(data))
            db.session.add(new_log)

            if msg_type == "sound":
                sensor_codigo = str(data.get("sensor_id", "A1"))
                nivel_db = float(data.get("nivel_db", 0.0))

                # Ensure default zona exists
                zona = Zona.query.first()
                if not zona:
                    zona = Zona(descripcion="Zona Campus UIS")
                    db.session.add(zona)
                    db.session.commit()


                # Ensure SensorSonido exists
                sensor = SensorSonido.query.filter_by(codigo=sensor_codigo).first()
                if not sensor:
                    sensor = SensorSonido(codigo=sensor_codigo, zona_id=zona.id, ubicacion="Campus UIS")
                    db.session.add(sensor)
                    db.session.commit()

                # Record MedicionSonido
                medicion = MedicionSonido(sensor_id=sensor.id, nivel_db=nivel_db)
                db.session.add(medicion)

            elif msg_type == "bin":
                nivel = float(data.get("nivel", 0.0))
                # Usar el Vertedero único
                contenedor = Contenedor.query.first()
                if not contenedor:
                    contenedor = Contenedor(
                        codigo="VERTEDERO",
                        capacidad_litros=500.0,
                        nivel_actual=nivel,
                        ubicacion="Vertedero Principal Campus UIS"
                    )
                    db.session.add(contenedor)
                    db.session.commit()
                else:
                    contenedor.nivel_actual = nivel

                lectura = LecturaContenedor(contenedor_id=contenedor.id, nivel=nivel)
                db.session.add(lectura)
                db.session.commit()
                status_txt = "COMPLETAMENTE LLENO" if nivel >= 100 else f"{nivel:.1f}%"
                return f"Vertedero de Basura actualizado: {status_txt}"


            elif msg_type == "park":
                placa = str(data.get("placa", "DESCONOCIDO")).upper()
                codigo_espacio = str(data.get("espacio_codigo", "P01")).upper()
                accion = str(data.get("accion", "in")).lower()

                vehiculo = Vehiculo.query.filter_by(placa=placa).first()
                if not vehiculo:
                    vehiculo = Vehiculo(placa=placa)
                    db.session.add(vehiculo)
                    db.session.commit()

                espacio = EspacioParqueadero.query.filter_by(codigo=codigo_espacio).first()
                if not espacio:
                    espacio = EspacioParqueadero(codigo=codigo_espacio, disponible=True)
                    db.session.add(espacio)
                    db.session.commit()

                if accion in ["in", "ingresar", "ingreso"]:
                    if espacio.disponible:
                        acceso = AccesoParqueadero(vehiculo_id=vehiculo.id, espacio_id=espacio.id)
                        espacio.disponible = False
                        db.session.add(acceso)
                elif accion in ["out", "salir", "salida"]:
                    acceso = AccesoParqueadero.query.filter_by(vehiculo_id=vehiculo.id, salida=None).first()
                    espacio.disponible = True
                    if acceso:
                        acceso.salida = datetime.utcnow()

            db.session.commit()
            return f"Processed {msg_type} successfully"
        except Exception as e:
            logging.error("Error in dispatch_command: %s", e)
            db.session.rollback()
            return f"Error: {e}"

