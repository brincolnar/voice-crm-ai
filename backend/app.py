from flask import Flask, request, jsonify
from flask_cors import CORS
from ai import *
from pydub import AudioSegment
import ffmpeg
from celery import Celery
from werkzeug.utils import secure_filename
from shutil import move
from datetime import datetime

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['result_backend'],
        broker=app.config['broker_url']
    )
    celery.conf.update(app.config)
    celery.conf.update(CELERY_IMPORTS=('your_script_name',))
    return celery

app = Flask(__name__)
app.config.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0'
)

celery = make_celery(app)
CORS(app, supports_credentials=True, origins=['*'])
    
@celery.task
def convert_task(file_path):
    # Convert OGA to WAV using ffmpeg-python
    wav_path = file_path.replace('.oga', '.wav')
    try:
        ffmpeg.input(file_path).output(wav_path).run(overwrite_output=True)
    except ffmpeg.Error as e:
        print(f'ffmpeg error: {e.stderr.decode()}')
        return 'Conversion failed'

    # Convert WAV to MP3
    mp3_path = file_path.replace('.oga', '.mp3')
    try:
        sound = AudioSegment.from_wav(wav_path)
        sound.export(mp3_path, format="mp3")
    except Exception as e:
        print(f"Error converting to MP3: {e}")
        return 'Error converting to MP3'

    # Call transcribe task
    transcribe_task.delay(mp3_path)

@celery.task
def transcribe_task(mp3_path):
    # Initialize your whisper module (replace `init` and `whisper` with your actual initialization and transcription methods)
    try:
        init()
        text = whisper(mp3_path)
    except Exception as e:
        print(f"Error during transcription: {e}")
        return 'Error during transcription'

    return f'File transcribed successfully: {text}'

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['audio']
    filename = secure_filename(file.filename)

    # Get the current timestamp and append it to the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"

    # Save the file to the uploads directory
    uploads_dir = 'uploads'
    os.makedirs(uploads_dir, exist_ok=True)

    file_path = os.path.join(uploads_dir, filename)
    print("file_path: ", file_path)
    try:
        file.save(file_path)
        print(f"File saved with timestamp: {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")
        return jsonify({'error': 'Error saving file'}), 500
    
    # Initiate the convert task
    convert_task.delay(file_path)

    return jsonify({'message': 'File upload successful'}), 200

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/')
def home():
    return "Hello Flask!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)
