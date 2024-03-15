from flask import Flask, render_template,request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

stored_messages = []
users_online = []
    
@socketio.on('connect')
def handle_connect():
    for message in stored_messages:
        emit('receive_message', message)
    emit('users_online', users_online, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    user_left = [user for user in users_online if user['sid'] == request.sid]
    if user_left:
        users_online.remove(user_left[0])
        emit('user_left', user_left[0]['name'], broadcast=True)
    emit('users_online', users_online, broadcast=True)

@socketio.on('register_user')
def handle_register_user(name):
    users_online.append({'name': name, 'sid': request.sid})
    emit('user_joined', name, broadcast=True)
    emit('users_online', users_online, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    message = data['message']
    name = data['name']
    full_message = f"{name}: {message}"
    stored_messages.append(full_message)
    emit('receive_message', full_message, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
