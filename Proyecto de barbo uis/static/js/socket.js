// SocketIO Real-time Connection & Web Serial API Helper for Developers
document.addEventListener('DOMContentLoaded', () => {
    if (typeof io !== 'undefined') {
        window.socket = io();

        const systemStatusText = document.getElementById('systemStatusText');

        window.socket.on('connect', () => {
            console.log('[SocketIO] Conectado en tiempo real al servidor en la nube');
            if (systemStatusText) systemStatusText.innerText = 'En línea';
        });

        window.socket.on('disconnect', () => {
            console.warn('[SocketIO] Desconectado del servidor');
            if (systemStatusText) systemStatusText.innerText = 'Desconectado';
        });

        window.socket.on('arduino_event', (data) => {
            console.log('[Arduino Event Broadcast]:', data);
        });

        window.socket.on('send_arduino_command', async (data) => {
            console.log('[Comando saliente hacia Arduino recibido]:', data);
            if (window.webSerialPort && window.webSerialConnected) {
                try {
                    const encoder = new TextEncoder();
                    const writer = window.webSerialPort.writable.getWriter();
                    const cmdStr = (data.command || '').trim() + '\n';
                    await writer.write(encoder.encode(cmdStr));
                    writer.releaseLock();
                    console.log('[WebSerial TX OK]: Transmitido con éxito al Arduino:', cmdStr);
                } catch (err) {
                    console.error('[WebSerial TX Error]: Error enviando a puerto serie:', err);
                }
            }
        });
    }

    window.webSerialPort = null;
    window.webSerialConnected = false;


    // Web Serial API logic for Admin / Developer Users
    const btnConnect = document.getElementById('btnConnectWebSerial');
    const statusText = document.getElementById('webSerialStatusText');
    let serialPort = null;
    let isConnected = false;

    if (btnConnect) {
        btnConnect.addEventListener('click', async () => {
            if (!('serial' in navigator)) {
                alert('La función Web Serial API es soportada en navegadores Google Chrome, Microsoft Edge y Opera. Por favor abre la página en uno de estos navegadores para conectar el Arduino por USB.');
                return;
            }

            if (isConnected && serialPort) {
                try {
                    await serialPort.close();
                } catch (e) {
                    console.error('Error al cerrar puerto:', e);
                }
                isConnected = false;
                window.webSerialConnected = false;
                window.webSerialPort = null;
                btnConnect.classList.remove('active');
                if (statusText) statusText.innerText = 'Conectar Arduino USB';
                return;
            }

            try {
                // Solicitar al usuario desarrollador elegir el puerto COM del Arduino
                serialPort = await navigator.serial.requestPort();
                await serialPort.open({ baudRate: 9600 });

                isConnected = true;
                window.webSerialPort = serialPort;
                window.webSerialConnected = true;
                btnConnect.classList.add('active');
                if (statusText) statusText.innerText = 'Arduino USB Conectado';


                console.log('[WebSerial] Conectado exitosamente al puerto USB seleccionado');

                // Iniciar flujo de lectura de datos del Arduino
                const textDecoder = new TextDecoderStream();
                const readableStreamClosed = serialPort.readable.pipeTo(textDecoder.writable);
                const reader = textDecoder.readable.getReader();
                let buffer = '';

                while (isConnected) {
                    const { value, done } = await reader.read();
                    if (done) {
                        reader.releaseLock();
                        break;
                    }
                    if (value) {
                        buffer += value;
                        const lines = buffer.split('\n');
                        buffer = lines.pop(); // guardar fragmento incompleto
                        for (const line of lines) {
                            const trimmed = line.trim();
                            if (trimmed && window.socket) {
                                console.log('[WebSerial RX Line]:', trimmed);
                                // Retransmitir al servidor en la nube para actualizar a todos los usuarios
                                window.socket.emit('web_serial_data', {
                                    raw: trimmed,
                                    port: 'USB WebSerial (Dev)'
                                });
                            }
                        }
                    }
                }
            } catch (err) {
                console.error('[WebSerial Error]:', err);
                if (err.name !== 'NotFoundError') { // NotFoundError occurs when user cancels prompt
                    alert('No se pudo conectar al puerto serie: ' + err.message);
                }
                isConnected = false;
                btnConnect.classList.remove('active');
                if (statusText) statusText.innerText = 'Conectar Arduino USB';
            }
        });
    }
});
