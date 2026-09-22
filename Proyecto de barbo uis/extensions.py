from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

# Shared extensions to avoid circular imports

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
