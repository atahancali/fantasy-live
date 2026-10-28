"""One-time Yahoo OAuth authorization. Run locally, never commit credentials."""
import base64
import os
import secrets
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

CLIENT_ID = os.environ['YAHOO_CLIENT_ID']
CLIENT_SECRET = os.environ['YAHOO_CLIENT_SECRET']
REDIRECT_URI = 'http://localhost:8765/callback'
STATE = secrets.token_urlsafe(24)
result = {}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if params.get('state', [''])[0] != STATE:
            self.send_response(400); self.end_headers(); self.wfile.write(b'Invalid state'); return
        result['code'] = params.get('code', [None])[0]
        result['error'] = params.get('error', [None])[0]
        self.send_response(200); self.end_headers()
        self.wfile.write(b'Yahoo authorization received. Return to terminal.')
        threading.Thread(target=self.server.shutdown, daemon=True).start()
    def log_message(self, *_):
        pass

params = urllib.parse.urlencode({
    'client_id': CLIENT_ID,
    'redirect_uri': REDIRECT_URI,
    'response_type': 'code',
    'language': 'en-us',
    'state': STATE,
})
auth_url = 'https://api.login.yahoo.com/oauth2/request_auth?' + params
print('Opening Yahoo authorization page...')
print('If browser does not open, paste this URL:', auth_url)
server = HTTPServer(('localhost', 8765), Handler)
webbrowser.open(auth_url)
server.serve_forever()
if not result.get('code'):
    raise SystemExit('Authorization failed: ' + str(result.get('error')))
credentials = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()
r = requests.post('https://api.login.yahoo.com/oauth2/get_token',
    headers={'Authorization': f'Basic {credentials}'},
    data={'grant_type': 'authorization_code', 'code': result['code'], 'redirect_uri': REDIRECT_URI}, timeout=30)
r.raise_for_status()
print('\nSAVE THIS AS GITHUB SECRET YAHOO_REFRESH_TOKEN (do not commit):')
print(r.json()['refresh_token'])
print('\nOAuth bootstrap complete.')
