from http.server import BaseHTTPRequestHandler
import sys
import os

# Add the backend directory to the path
current_dir = os.path.dirname(os.path.realpath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), 'price_tracker', 'backend')
sys.path.append(backend_dir)

# Import the Flask app
from app import create_app

app = create_app()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import parse_qs, urlparse
        
        # Parse the query string
        query_components = parse_qs(urlparse(self.path).query)
        
        # Create a WSGI environment
        environ = {
            'wsgi.input': self.rfile,
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
            'CONTENT_LENGTH': self.headers.get('content-length', ''),
            'REMOTE_ADDR': self.client_address[0],
            'SERVER_NAME': self.server.server_name,
            'SERVER_PORT': str(self.server.server_port),
            'SERVER_PROTOCOL': self.request_version,
        }
        
        # Add HTTP headers
        for key, value in self.headers.items():
            environ['HTTP_' + key.upper().replace('-', '_')] = value
        
        # Define WSGI callback
        def start_response(status, headers):
            self.send_response(int(status.split()[0]))
            for key, value in headers:
                self.send_header(key, value)
            self.end_headers()
        
        # Run the application and get the response
        response = app(environ, start_response)
        
        # Send the response body
        for data in response:
            self.wfile.write(data)
    
    def do_POST(self):
        self.do_GET()

def handler(event, context):
    return Handler.as_view()(event, context) 