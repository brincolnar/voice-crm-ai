from flask import Flask, request, jsonify
from flask_cors import CORS
from ai import *
from pydub import AudioSegment
import ffmpeg
from celery import Celery
from werkzeug.utils import secure_filename
from shutil import move
from datetime import datetime
from flask_socketio import SocketIO, emit


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

CORS(app, supports_credentials=True, origins=['*'])


@socketio.on('stream')
def handle_stream(audio_chunk):
    # Process the chunk and transcribe
    # Send transcription back to the client
    print("Received audio chunk")
    emit('transcription', {'text': 'Streaming'})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio_data' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file_ = request.files['audio_data']
    print("Raw file: ")
    print(file_)

    filename = file_.filename.replace(':', '_') + '.wav'
    print('Audio filename 1: ', filename)
    
    # Get the current timestamp and append it to the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"

    # Save the file to the uploads directory
    uploads_dir = '.\\uploads'
    os.makedirs(uploads_dir, exist_ok=True)

    file_path = os.path.join(uploads_dir, filename)
    print('Audio filename 2: ', file_path)
    try:
        file_.save(file_path)
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({'error': 'Error saving file'}), 500
    
    # Initialize your whisper module (replace `init` and `whisper` with your actual initialization and transcription methods)
    try:
        text = whisper(file_path)
    except Exception as e:
        print(f"Error during transcription: {e}")
        return 'Error during transcription'

    print("Transcription: ", text)

    return jsonify({'message': text}), 200

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/')
def home():
    return "Hello Flask!"

if __name__ == '__main__':
    socketio.run(app, debug=True)

