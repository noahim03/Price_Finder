from http.server import BaseHTTPRequestHandler
import sys
import os
import json

# Add the backend directory to the path
current_dir = os.path.dirname(os.path.realpath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), 'price_tracker', 'backend')
sys.path.append(backend_dir)

# Import the Flask app
from app import create_app

app = create_app()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
    
    def do_PUT(self):
        self._handle_request()
    
    def do_DELETE(self):
        self._handle_request()
    
    def _handle_request(self):
        from urllib.parse import parse_qs, urlparse
        
        # Parse the query string
        query_components = parse_qs(urlparse(self.path).query)
        
        # Read request body if it exists
        content_length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(content_length) if content_length else b''
        
        # Create a WSGI environment
        environ = {
            'wsgi.input': body,
            'wsgi.errors': sys.stderr,
            'wsgi.version': (1, 0),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'wsgi.url_scheme': 'https',
            'REQUEST_METHOD': self.command,
            'PATH_INFO': self.path.split('?')[0],
            'QUERY_STRING': urlparse(self.path).query,
            'CONTENT_TYPE': self.headers.get('content-type', ''),
            'CONTENT_LENGTH': str(content_length),
            'REMOTE_ADDR': self.client_address[0],
            'SERVER_NAME': self.server.server_name,
            'SERVER_PORT': str(self.server.server_port),
            'SERVER_PROTOCOL': self.request_version,
        }
        
        # Add HTTP headers
        for key, value in self.headers.items():
            environ['HTTP_' + key.upper().replace('-', '_')] = value
        
        # Define WSGI callback
        response_body = []
        status_code = [200]
        status_text = ['OK']
        response_headers = [[]]
        
        def start_response(status, headers):
            status_parts = status.split(' ', 1)
            status_code[0] = int(status_parts[0])
            status_text[0] = status_parts[1] if len(status_parts) > 1 else ''
            response_headers[0] = headers
            return response_body.append
        
        # Run the application and get the response
        result = app(environ, start_response)
        
        # Send response status and headers
        self.send_response(status_code[0])
        for name, value in response_headers[0]:
            self.send_header(name, value)
        self.end_headers()
        
        # Send the response body
        for data in result:
            if data:
                self.wfile.write(data if isinstance(data, bytes) else data.encode('utf-8'))

def handler(event, context):
    """Handler for serverless function."""
    # Parse the event data
    path = event.get('path', '')
    http_method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    query_params = event.get('queryStringParameters', {})
    body = event.get('body', '')
    
    # Convert query params to query string
    query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()]) if query_params else ''
    
    # Create environment with the request data
    environ = {
        'REQUEST_METHOD': http_method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.input': body.encode('utf-8') if isinstance(body, str) else body,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https'
    }
    
    # Add headers
    for header, value in headers.items():
        key = 'HTTP_' + header.upper().replace('-', '_')
        environ[key] = value
    
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
    status_code = int(status_headers[0].split(' ')[0]) if status_headers[0] else 200
    return {
        'statusCode': status_code,
        'headers': dict(status_headers[1]) if status_headers[1] else {},
        'body': ''.join(body_chunks)
    } 