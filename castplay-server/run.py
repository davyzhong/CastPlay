"""CastPlay Server Entry Point"""
import os

# Monkey patch for gevent
from gevent import monkey
monkey.patch_all()

from app import create_app, socketio

app = create_app(os.getenv('FLASK_ENV') or 'development')

if __name__ == '__main__':
    # Use socketio.run instead of app.run for WebSocket support
    # Port 5001 to avoid conflict with macOS AirPlay (port 5000)
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=app.config['DEBUG']
    )
