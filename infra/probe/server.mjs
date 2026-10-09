// Sonda técnica local — NÃO é a API da RoboCopa nem uma autenticação de participantes.
import { createServer } from 'node:http';

const host = '0.0.0.0'; // Dentro do contêiner; publicação HOST limitada a 127.0.0.1 no Compose.
const port = 8080;

const server = createServer((request, response) => {
  response.setHeader('Cache-Control', 'no-store');
  response.setHeader('X-Content-Type-Options', 'nosniff');
  if (request.method === 'GET' && request.url === '/health') {
    response.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    response.end(JSON.stringify({
      service: 'robocopa-ifma-infra-probe',
      status: 'ok',
      scope: 'local-development-only',
    }));
    return;
  }
  response.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
  response.end(JSON.stringify({ error: 'not_found' }));
});

server.headersTimeout = 10_000;
server.requestTimeout = 10_000;
server.listen(port, host);
