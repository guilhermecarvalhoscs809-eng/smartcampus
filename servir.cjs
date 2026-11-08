const http = require('http');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname);
const pages = new Set([
  'armarios.html',
  'assignacao.html',
  'avaria.html',
  'criar-utilizador.html',
  'dashboard.html',
  'devolucao.html',
  'equipamentos.html',
  'eventos.html',
  'login.html',
  'logs.html',
  'registar-equipamento.html',
  'salas.html',
  'transferencia.html',
  'utilizacoes.html',
  'utilizadores.html'
]);
const contentTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.png': 'image/png'
};

http.createServer((req, res) => {
  let relative;
  try {
    relative = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  } catch {
    res.writeHead(400);
    res.end('Invalid URL');
    return;
  }

  if (relative === '/') relative = '/index.html';
  else if (pages.has(relative.slice(1))) relative = `/demo${relative}`;

  const file = path.resolve(root, `.${relative}`);
  if (!file.startsWith(`${root}${path.sep}`)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.readFile(file, (err, data) => {
    if (err) {
      res.writeHead(err.code === 'ENOENT' ? 404 : 500);
      res.end(err.code === 'ENOENT' ? 'Not found' : 'Unable to read requested file');
      return;
    }

    res.writeHead(200, {
      'Content-Type': contentTypes[path.extname(file)] || 'application/octet-stream',
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff'
    });
    res.end(data);
  });
}).listen(8766, '127.0.0.1', () => {
  console.log('SmartCampus disponível em http://127.0.0.1:8766/');
});

