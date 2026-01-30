from flask import Flask, request, send_file, Response
import subprocess
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("piper-api")

app = Flask(__name__)

# Directory where voices are stored
VOICES_DIR = "/app/voices"

@app.route('/', methods=['GET'])
def index():
    return Response("Piper API is running", status=200)

@app.route('/health', methods=['GET'])
def health():
    return Response("OK", status=200)

@app.route('/api/tts', methods=['POST'])
def tts():
    start_time = time.time()
    try:
        data = request.json
        if not data:
            return Response("Missing JSON body", status=400)
            
        text = data.get('text', '')
        model_name = data.get('model', 'en_US-amy-medium')
        
        if not text:
            return Response("Missing 'text' parameter", status=400)
            
        # Security: Basic sanitization of filenames
        model_name = os.path.basename(model_name)
        if not model_name.endswith('.onnx'):
            model_name += '.onnx'
            
        model_path = os.path.join(VOICES_DIR, model_name)
        output_path = f"/tmp/output_{int(time.time())}.wav"
        
        if not os.path.exists(model_path):
            logger.error(f"Model not found: {model_path}")
            return Response(f"Model {model_name} not found in {VOICES_DIR}", status=404)

        logger.info(f"Generating TTS for: {text[:50]}... using model: {model_name}")
        
        # Execute Piper
        # Command: echo "text" | piper --model model.onnx --output_file output.wav
        process = subprocess.Popen(
            ['/usr/local/bin/piper', '--model', model_path, '--output_file', output_path],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        _, stderr = process.communicate(input=text.encode('utf-8'))
        
        if process.returncode != 0:
            logger.error(f"Piper error: {stderr.decode()}")
            return Response(f"Piper execution failed: {stderr.decode()}", status=500)
            
        logger.info(f"TTS generated in {time.time() - start_time:.2f}s")
        
        return send_file(output_path, mimetype="audio/wav")
        
    except Exception as e:
        logger.exception("Unexpected error in TTS generation")
        return Response(str(e), status=500)

if __name__ == '__main__':
    # Listen on all interfaces on port 5000
    app.run(host='0.0.0.0', port=5000)
