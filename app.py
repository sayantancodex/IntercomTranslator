from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, join_room, leave_room
from deep_translator import GoogleTranslator
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
import logging
import re
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, async_mode='eventlet', logger=True, engineio_logger=True)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

users = {}
rooms = {}

LANGUAGE_CODES = {
    'en': 'English',
    'bn': 'Bengali'
}

def load_mappings():
    mappings_file = 'translation_mappings.json'
    default_mappings = {"benglish_to_bengali": {}, "english_to_bengali": {}}
    if not os.path.exists(mappings_file):
        try:
            with open(mappings_file, 'w', encoding='utf-8') as f:
                json.dump(default_mappings, f, ensure_ascii=False, indent=4)
            logger.info(f"Created empty {mappings_file}")
        except Exception as e:
            logger.error(f"Error creating {mappings_file}: {e}")
            return default_mappings
    try:
        with open(mappings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading mappings: {e}")
        return default_mappings

MAPPINGS = load_mappings()
BENGLISH_TO_BENGALI = MAPPINGS.get("benglish_to_bengali", {})
ENGLISH_TO_BENGALI = MAPPINGS.get("english_to_bengali", {})

def is_benglish(text):
    return bool(re.match(r'^[a-zA-Z\s\W]+$', text))

def benglish_to_bengali(text):
    try:
        if text.lower() in BENGLISH_TO_BENGALI:
            bengali_text = BENGLISH_TO_BENGALI[text.lower()]
            logger.debug(f"Transliterated '{text}' to '{bengali_text}' (from mappings)")
            return bengali_text
        words = text.lower().split()
        transliterated_words = []
        for word in words:
            transliterated_words.append(BENGLISH_TO_BENGALI.get(word, transliterate(word, sanscript.ITRANS, sanscript.BENGALI)))
        bengali_text = ' '.join(transliterated_words)
        logger.debug(f"Transliterated '{text}' to '{bengali_text}'")
        return bengali_text
    except Exception as e:
        logger.error(f"Transliteration error: {e}")
        return text

def translate_to_bengali(text):
    if text.lower() in ENGLISH_TO_BENGALI:
        translated_text = ENGLISH_TO_BENGALI[text.lower()]
        logger.debug(f"Translated English '{text}' to '{translated_text}' (from mappings)")
        return translated_text
    try:
        translator = GoogleTranslator(source='en', target='bn')
        translated_text = translator.translate(text)
        logger.debug(f"GoogleTranslated English '{text}' to '{translated_text}'")
        return translated_text
    except Exception as e:
        logger.error(f"English to Bengali translation error: {e}")
        return text

def translate_to_english(text):
    try:
        translator = GoogleTranslator(source='bn', target='en')
        translated_text = translator.translate(text)
        logger.debug(f"GoogleTranslated Bengali '{text}' to '{translated_text}'")
        return translated_text
    except Exception as e:
        logger.error(f"Bengali to English translation error: {e}")
        return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug')
def debug():
    return jsonify({'users': {sid: info for sid, info in users.items()}, 'rooms': rooms})

@socketio.on('join')
def on_join(data):
    sid = request.sid
    username = data['username']
    language = data['language']
    room = 'chat_room'

    if sid in users:
        logger.debug(f"User {username} (SID: {sid}) already joined. Updating info.")
        old_room = users[sid].get('room')
        if old_room and old_room in rooms:
            rooms[old_room].remove(sid)
            if not rooms[old_room]:
                del rooms[old_room]
    
    users[sid] = {'username': username, 'language': language, 'room': room}
    if room not in rooms:
        rooms[room] = []
    if sid not in rooms[room]:
        rooms[room].append(sid)
    
    join_room(room)
    logger.debug(f"User {username} (SID: {sid}, Lang: {language}) joined room {room}. Members: {rooms[room]}")
    socketio.emit('message', {
        'username': 'System',
        'message': f"{username} joined in {LANGUAGE_CODES.get(language, 'Unknown')}."
    }, room=room)

    if len(rooms[room]) == 2:
        socketio.emit('message', {
            'username': 'System',
            'message': 'Chat started! Go ahead and talk.'
        }, room=room)
    elif len(rooms[room]) > 2:
        socketio.emit('message', {
            'username': 'System',
            'message': "Room's full. Only two users allowed."
        }, to=sid)
        leave_room(room)
        rooms[room].remove(sid)
        del users[sid]
        logger.debug(f"Rejected {username} (SID: {sid}) from full room {room}")

@socketio.on('change_language')
def on_change_language(data):
    sid = request.sid
    username = data['username']
    language = data['language']
    user = users.get(sid, {})
    room = user.get('room')

    if not room or room not in rooms:
        logger.error(f"Invalid room {room} for SID {sid}")
        socketio.emit('message', {
            'username': 'System',
            'message': 'Error: Invalid room.'
        }, to=sid)
        return

    users[sid]['language'] = language
    logger.debug(f"User {username} (SID: {sid}) changed language to {language}")
    socketio.emit('message', {
        'username': 'System',
        'message': f"{username} switched to {LANGUAGE_CODES.get(language, 'Unknown')}."
    }, room=room)

@socketio.on('leave')
def on_leave():
    sid = request.sid
    user = users.get(sid, {})
    room = user.get('room')
    if room and room in rooms:
        rooms[room].remove(sid)
        socketio.emit('message', {
            'username': 'System',
            'message': f"{user.get('username', 'User')} left the chat."
        }, room=room)
        if not rooms[room]:
            del rooms[room]
        leave_room(room)
        del users[sid]
        logger.debug(f"User {user.get('username', 'Unknown')} (SID: {sid}) left room {room}")

@socketio.on('message')
def handle_message(data):
    sender_sid = request.sid
    sender = users.get(sender_sid, {})
    room = sender.get('room')
    sender_lang = sender.get('language', 'en')
    message = data.get('message', '')
    
    logger.debug(f"Message from {sender.get('username', 'Unknown')} (SID: {sender_sid}, Lang: {sender_lang}): {message}")
    
    if not room or room not in rooms:
        logger.error(f"Invalid room {room} for SID {sender_sid}")
        socketio.emit('message', {
            'username': 'System',
            'message': 'Error: Invalid room.'
        }, to=sender_sid)
        return
    
    # Preprocess message
    processed_message = message
    original_message = message
    if sender_lang == 'bn' and is_benglish(message):
        processed_message = benglish_to_bengali(message)
    
    recipient_sids = [sid for sid in rooms[room] if sid != sender_sid]
    if not recipient_sids:
        socketio.emit('message', {
            'username': 'System',
            'message': 'No one else in the room.'
        }, to=sender_sid)
        logger.debug(f"No recipient in room {room} for SID {sender_sid}")
        return

    # Send to recipients
    for recipient_sid in recipient_sids:
        recipient_lang = users.get(recipient_sid, {}).get('language', 'en')
        recipient_username = users.get(recipient_sid, {}).get('username', 'Unknown')
        translated_message = processed_message
        hover_message = original_message
        
        if sender_lang != recipient_lang:
            if sender_lang == 'en' and recipient_lang == 'bn':
                translated_message = translate_to_bengali(processed_message)
                hover_message = original_message  # English original for Bengali recipient
            elif sender_lang == 'bn' and recipient_lang == 'en':
                translated_message = translate_to_english(processed_message)
                hover_message = processed_message  # Bengali processed for English recipient
        
        logger.debug(f"Sending to {recipient_username} (SID: {recipient_sid}, Lang: {recipient_lang}): {translated_message} (hover: {hover_message})")
        socketio.emit('message', {
            'username': sender['username'],
            'message': translated_message,
            'original': hover_message
        }, to=recipient_sid)
    
    # Send back to sender
    sender_message = message if sender_lang == 'en' else processed_message
    logger.debug(f"Sending to sender {sender['username']} (SID: {sender_sid}, Lang: {sender_lang}): {sender_message}")
    socketio.emit('message', {
        'username': sender['username'],
        'message': sender_message,
        'original': original_message
    }, to=sender_sid)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    user = users.get(sid, {})
    room = user.get('room')
    if room and room in rooms:
        rooms[room].remove(sid)
        socketio.emit('message', {
            'username': 'System',
            'message': f"{user.get('username', 'User')} left the chat."
        }, room=room)
        if not rooms[room]:
            del rooms[room]
        del users[sid]
        logger.debug(f"User {user.get('username', 'Unknown')} (SID: {sid}) disconnected from {room}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, allow_unsafe_werkzeug=True)