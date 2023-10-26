from flask import jsonify
from dotenv import find_dotenv, load_dotenv
import os
import openai


load_dotenv(find_dotenv())
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def whisper(path):
    with open(path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    
    text = transcript['text']

    return text
