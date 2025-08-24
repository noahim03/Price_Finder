import os
import sys

# Ensure the server directory is on the path
current_dir = os.path.dirname(os.path.realpath(__file__))
server_dir = os.path.join(os.path.dirname(current_dir), 'server')
if server_dir not in sys.path:
    sys.path.append(server_dir)

# Import the Flask app from server/index.py
from index import app  # 'app' is created via create_app() in server/index.py
