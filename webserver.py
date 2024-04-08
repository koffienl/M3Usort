import sys
from flask import Flask, request, send_from_directory, abort
from werkzeug.utils import secure_filename  # Corrected import
import os
import logging
from logging.handlers import RotatingFileHandler

# Configuration
BASE_DIR = "/data/M3Usort/files"  # Base directory for serving files
PORT_NUMBER = 8080  # Port number now configurable

app = Flask(__name__)

# Setup logging
handler = RotatingFileHandler('/data/M3Usort/server.log', maxBytes=100000, backupCount=3)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
app.logger.addHandler(handler)

class StreamToLogger:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

    def flush(self):
        pass

sys.stdout = StreamToLogger(logger, logging.INFO)
sys.stderr = StreamToLogger(logger, logging.ERROR)

@app.route('/<path:filename>')
def dynamic_serve_file(filename):
    username = request.args.get('username')
    password = request.args.get('password')
    if not username or not password:
        abort(401)  # Unauthorized access if username or password aren't provided

    # Securely construct the file path to avoid path traversal vulnerabilities
    secure_filename_path = secure_filename(filename)
    #file_path = os.path.join(BASE_DIR, username, password, secure_filename_path)
    #file_path = BASE_DIR
    file_path = os.path.join(BASE_DIR, secure_filename_path)
    
    if not os.path.isfile(file_path):
        abort(404)  # Not found if the file doesn't exist

    # Attempt to capture the real client IP, considering the X-Forwarded-For header
    client_ip = request.headers.get('X-Real-IP', request.headers.get('X-Forwarded-For', request.remote_addr).split(",")[0].strip())
    logger.info(f"File requested by {client_ip}: {filename}")

    # Serve the file without directory listing
    return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT_NUMBER)
