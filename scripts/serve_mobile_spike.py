#!/usr/bin/env python3
"""Owner-only mobile authorship lab. Binds loopback; never serves project files.

No multi-user accounts or production authentication. Local CSRF/Host checks do not
turn this development HTTP server into a public student-submission service.
"""
from __future__ import annotations
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import urllib.parse
import run_mobile_spike as mobile

WEB = mobile.ROOT / 'spikes/autoria-mobile/web'
STATIC = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/style.css': ('style.css', 'text/css; charset=utf-8')}
MAX_BODY = 16384

class LabServer(ThreadingHTTPServer):
    daemon_threads = False
    allow_reuse_address = False
    def __init__(self, port: int = 18081, execute=None):
        super().__init__(('127.0.0.1', port), LabHandler)
        self.token = secrets.token_urlsafe(32)
        self.busy = threading.Lock()
        self.execute = execute if execute is not None else mobile.run_program
        self.allowed_hosts = {f'127.0.0.1:{self.server_port}', f'localhost:{self.server_port}'}
        self.allowed_origins = {'http://' + h for h in self.allowed_hosts}
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address

class LabHandler(BaseHTTPRequestHandler):
    server_version = 'RoboCopaLab/0.1'
    def log_message(self, *_):
        pass  # no source, credentials, query strings, paths or client identifiers logged

    def send_payload(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy',
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(payload)
        self.close_connection = True

    def reply(self, status: int, data: dict) -> None:
        self.send_payload(status, json.dumps(data, ensure_ascii=False).encode('utf-8'),
                          'application/json; charset=utf-8')

    def host_ok(self) -> bool:
        if self.headers.get('Host') not in self.server.allowed_hosts:
            self.reply(403, {'error': 'Host não permitido neste laboratório local.'})
            return False
        return True

    def do_GET(self) -> None:
        if not self.host_ok():
            return
        if self.path == '/api/config':
            self.reply(200, {'csrf': self.server.token, 'examples': mobile.LANG.EXAMPLES,
                'language_version': mobile.LANG.VERSION, 'scope': 'owner-local-only', 'rounds': 3})
        elif self.path in STATIC:
            name, kind = STATIC[self.path]
            self.send_payload(200, (WEB / name).read_bytes(), kind)
        else:
            self.reply(404, {'error': 'Rota não encontrada.'})

    def do_POST(self) -> None:
        if not self.host_ok():
            return
        if (self.headers.get('Origin') not in self.server.allowed_origins
            or not secrets.compare_digest(self.headers.get('X-Robocopa-CSRF', '').encode('utf-8'), self.server.token.encode('ascii'))):
            self.reply(403, {'error': 'Reabra esta página local para renovar a sessão.'})
            return
        if self.path not in ('/api/validate', '/api/train'):
            self.reply(404, {'error': 'Rota não encontrada.'})
            return
        try:
            raw_length = self.headers.get('Content-Length', '')
            if not raw_length.isascii() or not raw_length.isdigit():
                raise ValueError('Content-Length obrigatório.')
            length = int(raw_length)
            if not 1 <= length <= MAX_BODY or self.headers.get('Transfer-Encoding'):
                self.reply(413, {'error': 'Programa grande demais.'})
                return
            if self.headers.get_content_type() != 'application/json':
                self.reply(415, {'error': 'Envie JSON.'})
                return
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError('Corpo incompleto.')
            request = json.loads(raw.decode('utf-8'))
            if not isinstance(request, dict) or set(request) != {'source'}:
                raise ValueError('Envie apenas o campo source.')
            compiled = mobile.LANG.compile_program(request['source'])
        except mobile.LANG.ProgramError as error:
            self.reply(400, {'error': str(error), 'line': error.line})
            return
        except (UnicodeError, ValueError, OSError):
            self.reply(400, {'error': 'Requisição inválida.'})
            return
        if self.path == '/api/validate':
            self.reply(200, {'valid': True, 'program_sha256': compiled['program_sha256'],
                             'instructions': compiled['ast']['node_count']})
            return
        if not self.server.busy.acquire(blocking=False):
            self.reply(409, {'error': 'Uma batalha já está em andamento. Não foi criada outra execução.'})
            return
        try:
            result = self.server.execute(request['source'])
            self.reply(200, result)
        except (BrokenPipeError, ConnectionResetError):
            pass  # browser disconnected; execution cleanup is handled by the runner
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
            self.reply(500, {'error': 'Falha no treino. O código foi preservado; consulte .local/mobile-spike no host.'})
        finally:
            self.server.busy.release()

    def do_OPTIONS(self) -> None:
        self.reply(405, {'error': 'Acesso entre origens não habilitado.'})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-build', action='store_true', help='Reutilizar imagem já preparada nesta versão.')
    args = parser.parse_args()
    if not args.skip_build:
        mobile.prepare_images()
    else:
        mobile.baseline().docker(['image', 'inspect', '--format', '{{.Id}}', mobile.IMAGE])
    with LabServer() as server:
        print('Laboratório: http://127.0.0.1:18081 | Ctrl+C para encerrar.', flush=True)
        print('Somente neste computador. Não abra portas/túneis para alunos. Compose existente não foi alterado.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('Encerrando o laboratório; uma batalha em andamento concluirá a limpeza.', flush=True)

if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print('BLOCKED: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
