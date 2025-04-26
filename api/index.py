from flask import Flask, jsonify
import os
import sys

# Add the backend directory to the path
current_dir = os.path.dirname(os.path.realpath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), 'price_tracker', 'backend')
sys.path.append(backend_dir)

# Import the Flask app
from app import create_app

app = create_app()

@app.route('/api/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "ok"})

# This allows the file to be imported by Vercel
app = app 