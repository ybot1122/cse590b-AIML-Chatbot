"""debugserver.py
Debug server.
You do not need to edit this file.
"""
import api
import gzip, json, base64
from http.server import BaseHTTPRequestHandler, HTTPServer

DEBUG_SERVER_PORT = 8000 # Use env variables instead of changing this value
FOUR_OH_FOUR = '''<!doctype html><html><head>
    <title>404 Not Found</title>
  </head>
  <body>
    <h1>404 Not found</h1>
    <p>The resource specified was not found.</p>
  </body>
</html>'''

FILES = json.loads(gzip.decompress(base64.b64decode('H4sIADNMimAC/8VXe2/bNhD/KlzQQTJmSU6HDoVjd8PaAOvQF5Dsj6EuClo8S4xpUiBpO0aQ774jqafjrssGrA5ii/fiPX53pO7OsrMpOVvI2XdM5fZQASntRryY+e+FJGRWAmX+CZ83YCnJS6oN2PnibGtXyfPF2YAr6QaQteOwr5S2izOSK2lBOvk9Z7acM9jxHBK/GBMuueVUJCanAubnnTXLrYAXL0tql8qSV7DcFrMsEGsJweWaaBBo2diDAFMCuA1LDSukldZWZpplOZPpjWEg+E6nEmwmq022VMoaq2n1y7N0kk6SJfr+Y8a4sVluTMdON1ymSEGzD3caOFLvmnmBr6qYXPPKEqPznqcVWEvljUkLbsvtMuUqY6v8xrhvDAENugqhgoVbm93QHQ1m0OwsC48n7WdLauAxBmZZW/XZUrFDW2HKJckFNQZtuLriGnQblUPLecvf2OQZslwF0d55J8P4rhXSat9TP2LmSgyYNZszx0OzQhUOX400UpK+UzOs565ve7A+Wj3GqeR8cuwXl9XWBs+2BnTiEtzzbaX0xvumlSD9RSKKYVVwVQmaQ6kEA43Ea9eUjkNK0DD06zjAYz+fEpYUmrNjb5dba5UM7hqQrHMhcHqeL60k+J9Umm+oPvhnUfifpVD5Gk1foYVZFjT/UbpnmQNSjbQaXwiRZuScjUkL2TCdMFnGkrfvX11eXf/55vKKzMmdk4xcrqMpiXztN6YgOdWMLIvW3ZVQyEEHfQoTwYvSRmOvi2PlpKqXqRWNpdoGVUb1utYErdXpbRmVBeiHymHfhby/WMgd1eQzRoBNXa+e4Gq1lbnlWJQYRuQOJ4fdaklwKG83ODzTAuylAPf46+E1Q5kLcr+QC9mquTl6BcbgczwK2altrMDmZRxltOKZd+mzCXLROMhhRDi6S8VcSB/eX12HMJHspgBog/S7po7RyzDOE4dLp0CrSvCcOieyG4NWg+R9Y8PV18nd3XvO/Si1Jci4i1eDqUbNBrXPjpY6a/Ho4rQWo5a2WnxF4roqmAgy4BFiS2xoImFPLp2IV029dDCO5gkIA51Gk30U/BhZtQYZfWpEgzu4GuZ/Q9fwFvNKC/iDx67oY7JRDLwfTscV2sH1LcJlTj7HEfZDVwFMlO+4d3h8YrZip+pC6WH+5661OupHJ/iJTDve4wA9aqpFPn7Fpdaun23eeOJrO7CA6o49+oR/PmNP4qge1dEoRaxgK74suWBxnYsTUngQKSGuVYV5OsH4DVw8Fz2E16Ye1MSNtromsa8iliQsa3Q43NSU1OLEiEepAFnYksznczI5RuUHrTYcxxKiU4kdNNh0X8Py1zbH9YBqY2yPBgxmR8UWMMIo8tx+lzr0K8n+1/78/er9uxSvPFwWfHWIO3sB/lMSEtiS6xCRUT/VZkffqMmHBehafNyM66bX/808OGE81Mi4GruDZPT304EBplYdmgHtc/nlKY2w/SYz+hgDw9r/t9LWGdlzydQ+pYxd7tDDN3jhBrytxRFOJwf4zmzTov1z7Xjrfh59g7mOd3Pmgfkc41+fsu8+J+bEqWZt0dE8HAk93HUNB4xWDvaF3sYO0viu4Ga9GzjRJZYNkdoJPNq3GoI9J7+Y8SXgRRS28kuZd5+TuB2mAQGByELsngoR3+m0jaPXWESyolwAQ39wvEbkBwKNvuuWUXvxa9+fwtUvbY+zuzBnb8Ob45Q8n3x/EUi64HgbVXj/3EzJ+aS69XS1A42H3j65nRK6tcoTcwFUTwkKl6FJ0+Gx5jfZl9xCYiq8hk9JpaEv2b5gBNHSH0ZT8tOk2bbCTGMDTcnThnLk4NMHDh6mJBxtYSNMxP1f6l7Wr5kPAAA=')).decode('utf-8'))

class DebugServer(BaseHTTPRequestHandler):
  def _sniff_type(self):
    if self.path.endswith('.js'):
      return 'text/javascript'
    elif self.path.endswith('.css'):
      return 'text/css'
    elif self.path.endswith('.html') or \
      self.path.endswith('.htm') or \
      self.path.endswith('/'):
      return 'text/html'
    else:
      return 'application/octet-stream'

  def do_GET(self):
    if self.path == '/index.html' or self.path == '/index.htm':
      self.send_response(301)
      self.send_header('location', '/')
      self.end_headers()
    elif self.path in FILES:
      self.send_response(200)
      self.send_header('content-type', self._sniff_type())
      self.end_headers()
      self.wfile.write(bytes(FILES[self.path], "utf-8"))
    else:
      self.send_response(404)
      self.send_header('content-type', 'text/html')
      self.end_headers()
      self.wfile.write(bytes(FOUR_OH_FOUR, 'utf-8'))

  def do_POST(self):
    if self.path.startswith('/api/'):
      code, resp = 200, None
      try:
        # Get the body
        body_len = int(self.headers.get('Content-Length'))
        body = json.loads(self.rfile.read(body_len))
        if self.path.endswith('/start_session'):
          resp = { 'token': api.start_session() }
          print(resp)
        elif self.path.endswith('/end_session'):
          api.end_session(body['token'])
          resp = { 'success': True }
        elif self.path.endswith('/respond'):
          resp = { 'response': api.respond(body['token'], body['message']) }
      except Exception as e:
        code = 500
        print(e)
        resp = { 'error': str(e) }
      self.send_response(code)
      self.send_header("content-type", "application/json")
      self.end_headers()
      self.wfile.write(bytes(json.dumps(resp), 'utf-8'))
    else:
      self.send_response(404)
      self.send_header('content-type', 'text/html')
      self.end_headers()
      self.wfile.write(bytes(FOUR_OH_FOUR, 'utf-8'))

if __name__ == '__main__':
  import os
  import socketserver
  port = int(os.environ['PORT']) if 'PORT' in os.environ else DEBUG_SERVER_PORT

  with socketserver.TCPServer(("", port), DebugServer) as httpd:
    print(f'Serving HTTP debug console on port {port}')
    httpd.serve_forever()
