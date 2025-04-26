from flask import Flask, jsonify, request
import os
import sys
import json

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

# Vercel serverless function handler
def handler(event, context):
    """Serverless function handler for Vercel."""
    path = event.get('path', '')
    http_method = event.get('httpMethod', '')
    headers = event.get('headers', {})
    query_string = event.get('queryStringParameters', {})
    body = event.get('body', '')
    
    # Create environment with the request data
    environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.input': body,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https'
    }
    
    # Add headers
    for header, value in headers.items():
        environ[f'HTTP_{header.upper().replace("-", "_")}'] = value
    
    # Prepare for response
    response_body = []
    status_headers = [None, None]
    
    def start_response(status, response_headers):
        status_headers[0] = status
        status_headers[1] = response_headers
        return response_body.append
    
    # Process the request through Flask app
    resp = app(environ, start_response)
    
    # Combine all response body chunks
    body_chunks = []
    for chunk in resp:
        if chunk:
            body_chunks.append(chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk)
    
    # Format the response as required by Vercel
    return {
        'statusCode': int(status_headers[0].split(' ')[0]),
        'headers': dict(status_headers[1]),
        'body': ''.join(body_chunks)
    }

# For local development
if __name__ == '__main__':
    app.run(debug=True, port=3001) 