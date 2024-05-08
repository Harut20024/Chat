from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from pymongo import MongoClient
import openai 
import os
from dotenv import load_dotenv
from openai.error import RateLimitError, APIError

# Load environment variables
load_dotenv(override=True)


app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

openai.api_key = os.getenv('OPENAI_API_KEY')
print("Loaded API Key:", os.getenv('OPENAI_API_KEY'))


# MongoDB connection
client = MongoClient(os.getenv("MONGODB_URI"))
db = client.chat_db
messages_col = db.messages
users_col = db.users

@socketio.on('connect')
def handle_connect(auth=None):
    messages = list(messages_col.find({}, {'_id': 0}))
    for message in messages:
        emit('receive_message', message)
    update_users_online()

@socketio.on('disconnect')
def handle_disconnect():
    user_left = users_col.find_one_and_delete({'sid': request.sid})
    if user_left:
        emit('user_left', {'name': user_left['name']}, broadcast=True)
    update_users_online()

@socketio.on('register_user')
def handle_register_user(name):
    if users_col.find_one({'name': name}):
        emit('registration_failed', {'message': 'Name already exists'})
    else:
        users_col.insert_one({'name': name, 'sid': request.sid})
        emit('user_joined', name)
        update_users_online()

@socketio.on('send_message')
def handle_send_message(data):
    user_message = data["message"]
    print(data)
    if user_message.startswith("/ask"):
        query = user_message[5:].strip()
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": query}],
                max_tokens=400,
                temperature=0.5
            )
            output = response.choices[0].message['content'].strip()
            message = {'name': "ChatGPT", 'message': output,'time': data["time"]}
            messages_col.insert_one(message)
            emit('bot_answer', broadcast=True)
            emit('receive_message', {'name': 'ChatGPT', 'message': output,'time': data["time"]}, broadcast=True)
            
        except RateLimitError as e:
            emit('receive_message', {'name': 'System', 'message': 'Rate limit exceeded, please try again later.'}, broadcast=True)
        except APIError as e:
            emit('receive_message', {'name': 'System', 'message': 'An API error occurred: ' + str(e)}, broadcast=True)
        except Exception as e:
            emit('receive_message', {'name': 'System', 'message': 'An unexpected error occurred: ' + str(e)}, broadcast=True)
    else:
        message = {'name': data['name'], 'message': user_message,'time': data["time"]}
        messages_col.insert_one(message)
        message['_id'] = str(message['_id'])
        emit('receive_message', message, broadcast=True)
      
        
        
def update_users_online():
    users_online = list(users_col.find({}, {'_id': 0, 'name': 1}))
    emit('users_online', users_online, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
