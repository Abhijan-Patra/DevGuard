"""Explicit same-origin browser pairing; no bearer token is returned to JavaScript."""
import secrets
import time
from urllib.parse import urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

COOKIE = 'devguard_workspace'


class BrowserSessions:
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.sessions = {}

    def local_origin(self, request):
        if not self.enabled or request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
            return False
        try:
            host = urlsplit('http://' + request.headers.get('host', ''))
            origin = urlsplit(request.headers.get('origin', ''))
            return (host.hostname in {'127.0.0.1', 'localhost', '::1'}
                    and origin.scheme == 'http' and origin.netloc == host.netloc
                    and not origin.path and not origin.query and not origin.fragment
                    and not origin.username and request.headers.get('x-devguard-workspace') == '1')
        except ValueError:
            return False

    def authorized(self, request):
        # GET fetches omit Origin in browsers. The custom header is unavailable
        # cross-origin without preflight (the API grants no cross-origin access).
        if not self.enabled or request.client is None or request.client.host not in {'127.0.0.1', '::1'}:
            return False
        if request.headers.get('x-devguard-workspace') != '1':
            return False
        try:
            host = urlsplit('http://' + request.headers.get('host', ''))
            if host.hostname not in {'127.0.0.1', 'localhost', '::1'}:
                return False
        except ValueError:
            return False
        if request.method != 'GET' or request.headers.get('origin'):
            if not self.local_origin(request):
                return False
        identifier = request.cookies.get(COOKIE, '')
        return self.sessions.get(identifier, 0) > time.monotonic()

    def router(self):
        router = APIRouter(prefix='/api/v1/session')

        @router.post('/connect')
        async def connect(request: Request):
            if not self.local_origin(request):
                return JSONResponse({'error': {'code': 'LOCAL_ORIGIN_REQUIRED'}}, status_code=403)
            now = time.monotonic()
            self.sessions = {k: v for k, v in self.sessions.items() if v > now}
            if len(self.sessions) >= 8:
                return JSONResponse({'error': {'code': 'SESSION_LIMIT'}}, status_code=429)
            identifier = secrets.token_urlsafe(32)
            self.sessions[identifier] = now + 8 * 3600
            response = JSONResponse({'connected': True, 'expires_in_seconds': 8 * 3600})
            response.set_cookie(COOKIE, identifier, httponly=True, samesite='strict', path='/api/v1', max_age=8 * 3600)
            response.headers['Cache-Control'] = 'no-store'
            return response

        @router.post('/disconnect')
        async def disconnect(request: Request):
            if not self.local_origin(request):
                return JSONResponse({'error': {'code': 'LOCAL_ORIGIN_REQUIRED'}}, status_code=403)
            self.sessions.pop(request.cookies.get(COOKIE, ''), None)
            response = JSONResponse({'connected': False})
            response.delete_cookie(COOKIE, path='/api/v1')
            return response
        return router
