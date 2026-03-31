import os
import json
import threading
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
socketio = SocketIO(app, cors_allowed_origins="*")

MESSAGES_FILE = 'messages.txt'
file_lock = threading.Lock()

def append_message(message_dict):
    with file_lock:
        with open(MESSAGES_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(message_dict, ensure_ascii=False) + '\n')

def load_messages():
    messages = []
    if not os.path.exists(MESSAGES_FILE):
        return messages
    with file_lock:
        try:
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            messages.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass
    return messages

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('get_history')
def handle_get_history():
    messages = load_messages()
    emit('history', messages)

@socketio.on('send_message')
def handle_send_message(data):
    username = data.get('username', 'Anonymous')
    message = data.get('message', '').strip()
    if not message:
        return
    msg_obj = {
        'username': username,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    append_message(msg_obj)
    emit('new_message', msg_obj, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
