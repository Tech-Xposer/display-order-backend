from app import app
from app import socketio
from app import port
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',port=port, debug=True)
