from flask import Flask, render_template, jsonify, Response
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
import queue
import json

load_dotenv()

app = Flask(__name__)

# Global queue for storing translations
translation_queue = queue.Queue()
is_translating = False

class SpeechTranslator:
    def __init__(self):
        self.speech_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=os.getenv('SPEECH_KEY'),
            region=os.getenv('SPEECH_REGION')
        )
        self.speech_config.speech_recognition_language = "hi-IN"
        self.speech_config.add_target_language("en")
        self.translation_recognizer = None
        self.is_translating = False

    def start_translation(self):
        self.is_translating = True
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        self.translation_recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=self.speech_config,
            audio_config=audio_config
        )

        def handle_translation_result(evt):
            if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech:
                translation = evt.result.translations['en']
                translation_queue.put(translation)

        self.translation_recognizer.recognized.connect(handle_translation_result)
        self.translation_recognizer.start_continuous_recognition()

    def stop_translation(self):
        if self.translation_recognizer:
            self.is_translating = False
            self.translation_recognizer.stop_continuous_recognition()

translator = SpeechTranslator()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_translation', methods=['POST'])
def start_translation():
    global is_translating
    is_translating = True
    translator.start_translation()
    return jsonify({'status': 'started'})

@app.route('/stop_translation', methods=['POST'])
def stop_translation():
    global is_translating
    is_translating = False
    translator.stop_translation()
    return jsonify({'status': 'stopped'})

@app.route('/stream')
def stream():
    def generate():
        while True:
            try:
                if not is_translating:
                    break
                translation = translation_queue.get(timeout=0.1)
                yield f"data: {json.dumps({'translation': translation})}\n\n"
            except queue.Empty:
                continue
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)