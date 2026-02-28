const http = require('http');
const httpProxy = require('http-proxy');

const proxy = httpProxy.createProxyServer({});

const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, ngrok-skip-browser-warning');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Rotear para backend ou frontend (via Docker nginx)
  if (req.url.startsWith('/api/')) {
    console.log(`[PROXY] Backend: ${req.method} ${req.url}`);
    proxy.web(req, res, { 
      target: 'http://localhost:8080',
      changeOrigin: true
    });
  } else {
    console.log(`[PROXY] Frontend: ${req.method} ${req.url}`);
    proxy.web(req, res, { 
      target: 'http://localhost:8080',
      changeOrigin: true,
      ws: true // WebSocket para hot reload
    });
  }
});

// WebSocket para Next.js hot reload
server.on('upgrade', (req, socket, head) => {
  console.log('[PROXY] WebSocket upgrade');
  proxy.ws(req, socket, head, { 
    target: 'http://localhost:8080',
    ws: true
  });
});

const PORT = 9000;
server.listen(PORT, () => {
  console.log(`[PROXY] Servidor rodando na porta ${PORT}`);
  console.log(`[PROXY] Sistema: http://localhost:8080 -> http://localhost:${PORT}`);
  console.log(`[PROXY] Backend:  http://localhost:8080/api/* -> http://localhost:${PORT}/api/*`);
});
