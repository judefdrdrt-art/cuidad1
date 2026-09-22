import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'you-should-set-a-secret-key-uis-smartcity')
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    raw_db_url = os.getenv('DATABASE_URL')
    if raw_db_url and raw_db_url.startswith('postgres://'):
        raw_db_url = raw_db_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = raw_db_url or f"sqlite:///{os.path.join(basedir, 'ciudad_inteligente.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SOCKETIO_MESSAGE_QUEUE = None
    # Serial configuration
    SERIAL_PORTS = os.getenv('SERIAL_PORTS', 'COM3,COM5').split(',')  # priority order
    SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', '9600'))
    SERIAL_TIMEOUT = int(os.getenv('SERIAL_TIMEOUT', '1'))
    SERIAL_READ_INTERVAL = float(os.getenv('SERIAL_READ_INTERVAL', '1'))
