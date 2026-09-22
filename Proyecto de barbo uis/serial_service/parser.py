import logging
from typing import Dict, Any


def parse_line(line: str) -> Dict[str, Any]:
    """Parse a raw line received from the Arduino serial port.

    Expected formats (as documented in the project spec):
        SOUNDSET|<sensor_id>|<nivel_db>
        BIN|<contenedor_id>|<nivel>
        PARK|<placa>|<espacio_codigo>|<accion>

    Returns a dictionary with a ``type`` key indicating the message kind
    and the parsed fields. If the line cannot be parsed, an empty dict is
    returned and a warning is logged.
    """
    line = line.strip()
    if not line:
        return {}

    parts = line.split("|") if "|" in line else line.split(":")
    if not parts:
        return {}

    msg_type = parts[0].upper()
    try:
        if (msg_type == "SOUNDSET" or msg_type == "SOUND") and len(parts) >= 3:
            sensor_id = parts[1]
            nivel_db = float(parts[2])
            freq = float(parts[3]) if len(parts) > 3 else 1000.0
            amp = float(parts[4]) if len(parts) > 4 else min(1.0, max(0.05, nivel_db / 100.0))
            return {
                "type": "sound",
                "sensor_id": sensor_id,
                "nivel_db": nivel_db,
                "freq": freq,
                "amp": amp,
            }
        elif msg_type == "SOUNDWAVE" and len(parts) >= 3:
            sensor_id = parts[1]
            samples = [float(x) for x in parts[2].split(",") if x.strip()]
            return {
                "type": "sound_wave",
                "sensor_id": sensor_id,
                "samples": samples,
            }
        elif msg_type == "BIN" and len(parts) >= 2:
            if len(parts) == 2:
                contenedor_id = "VERTEDERO"
                val_str = parts[1].strip().upper()
            else:
                contenedor_id = parts[1].upper()
                val_str = parts[2].strip().upper()

            if val_str in ["LLENO", "FULL", "MAX"]:
                nivel = 100.0
            elif val_str in ["VACIO", "EMPTY", "MIN"]:
                nivel = 0.0
            elif val_str in ["MEDIO", "HALF"]:
                nivel = 50.0
            else:
                try:
                    nivel = float(val_str)
                except ValueError:
                    nivel = 0.0

            # Limitar nivel entre 0 y 100
            nivel = max(0.0, min(100.0, nivel))
            is_full = nivel >= 100.0


            return {
                "type": "bin",
                "contenedor_id": contenedor_id,
                "nivel": nivel,
                "is_full": is_full,
            }
        elif msg_type == "PARK" and len(parts) >= 4:
            placa = parts[1].upper()
            espacio_codigo = parts[2].upper()
            accion = parts[3].lower()
            return {
                "type": "park",
                "placa": placa,
                "espacio_codigo": espacio_codigo,
                "accion": accion,
            }
        else:
            logging.warning("Unrecognized serial line format: %s", line)
            return {}
    except Exception as e:
        logging.error("Error parsing serial line %s: %s", line, e)
        return {}

