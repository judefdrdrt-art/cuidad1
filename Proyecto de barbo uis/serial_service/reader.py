import threading
import time
import serial
import serial.tools.list_ports
from config import Config
from .parser import parse_line
from .commands import dispatch_command

class SerialReader(threading.Thread):
    """Background thread that continuously scans and reads from available serial ports.
    Auto-detects Arduino COM ports (COM1-COM30) and automatically reconnects when plugged in."""

    def __init__(self, socketio):
        super().__init__(daemon=True)
        self.socketio = socketio
        self._stop_event = threading.Event()
        self.serial_conn = None
        self.current_port = None

    def _get_candidate_ports(self):
        # Scan active system serial ports dynamically
        ports = [p.device for p in serial.tools.list_ports.comports()]
        # Add configured priority ports if not already in list
        for p in Config.SERIAL_PORTS:
            p = p.strip()
            if p and p not in ports:
                ports.append(p)
        return ports

    def _open_port(self) -> bool:
        candidate_ports = self._get_candidate_ports()
        for port in candidate_ports:
            try:
                self.serial_conn = serial.Serial(
                    port=port,
                    baudrate=Config.SERIAL_BAUDRATE,
                    timeout=Config.SERIAL_TIMEOUT,
                )
                self.current_port = port
                print(f"[SerialReader] Successfully connected to {port} at {Config.SERIAL_BAUDRATE} baud")
                return True
            except (serial.SerialException, OSError) as e:
                err_str = str(e)
                if "PermissionError" in err_str or "Acceso denegado" in err_str or "13" in err_str:
                    print(f"[SerialReader ATENCIÓN] El puerto {port} está OCUPADO por otra aplicación (ej: el Monitor Serie del Arduino IDE). Por favor CIERRA la pestaña 'Serial Monitor' en Arduino IDE para permitir que Python lea el puerto.")
                continue
        return False

    def run(self):
        print("[SerialReader] Background thread running. Scanning for Arduino COM ports...")
        while not self._stop_event.is_set():
            if not self.serial_conn or not self.serial_conn.is_open:
                if not self._open_port():
                    # Wait 2 seconds before retry (keep thread alive!)
                    time.sleep(2)
                    continue

            try:
                line_bytes = self.serial_conn.readline()
                if not line_bytes:
                    time.sleep(0.05)
                    continue

                line = line_bytes.decode(errors='ignore').strip()
                if not line:
                    continue

                print(f"[SerialReader RX {self.current_port}] {line}")

                data = parse_line(line)
                dispatch_result = None
                if data:
                    dispatch_result = dispatch_command(data)

                # Broadcast real-time serial payload to all connected frontend clients
                self.socketio.emit('arduino_event', {
                    'raw': line,
                    'parsed': data,
                    'result': dispatch_result,
                    'port': self.current_port,
                })

            except Exception as exc:
                print(f"[SerialReader Error on {self.current_port}] {exc}")
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except Exception:
                        pass
                self.serial_conn = None
                self.current_port = None
                time.sleep(2)

    def write_line(self, line: str) -> bool:
        """Enviar comando por puerto serie al Arduino si el puerto está abierto."""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                msg = (line.strip() + "\n").encode('utf-8')
                self.serial_conn.write(msg)
                self.serial_conn.flush()
                print(f"[SerialReader TX {self.current_port}] {line.strip()}")
                return True
            except Exception as e:
                print(f"[SerialReader TX Error] {e}")
                return False
        return False

    def stop(self):
        self._stop_event.set()
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
            print(f"[SerialReader] Closed {self.current_port}")


