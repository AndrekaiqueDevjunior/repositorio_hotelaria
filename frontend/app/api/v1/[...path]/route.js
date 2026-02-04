// API Proxy Route - Encaminha requisições para o backend
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000';

console.log('[API Proxy] BACKEND_URL configurada:', BACKEND_URL);

// Headers CORS para todas as respostas
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization, ngrok-skip-browser-warning',
  'Access-Control-Max-Age': '86400',
};

async function proxyRequest(request, path) {
  const url = `${BACKEND_URL}/api/v1/${path}`;
  
  console.log(`[API Proxy] ${request.method} ${url}`);
  
  const headers = new Headers();
  headers.set('Content-Type', 'application/json');
  
  // Copiar headers de autorizacao
  const authHeader = request.headers.get('Authorization');
  if (authHeader) {
    headers.set('Authorization', authHeader);
  }

  const options = {
    method: request.method,
    headers: headers,
  };

  // Adicionar body para POST, PUT, PATCH
  if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
    try {
      const body = await request.text();
      if (body) {
        options.body = body;
      }
    } catch (e) {
      console.log('[API Proxy] No body to parse');
    }
  }

  try {
    console.log(`[API Proxy] Tentando conectar: ${url}`);
    const response = await fetch(url, options);
    const data = await response.text();
    
    console.log(`[API Proxy] Sucesso ${response.status} de ${url}`);
    
    return new Response(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders,
      },
    });
  } catch (error) {
    console.error('[API Proxy] ERRO detalhado:', {
      message: error.message,
      code: error.code,
      url: url,
      backend_url: BACKEND_URL
    });
    
    return new Response(JSON.stringify({ 
      error: 'Backend connection failed', 
      detail: error.message,
      code: error.code,
      attempted_url: url,
      backend_configured: BACKEND_URL
    }), {
      status: 502,
      headers: { 
        'Content-Type': 'application/json',
        ...corsHeaders,
      },
    });
  }
}

export async function GET(request, { params }) {
  const path = params.path.join('/');
  return proxyRequest(request, path);
}

export async function POST(request, { params }) {
  const path = params.path.join('/');
  return proxyRequest(request, path);
}

export async function PUT(request, { params }) {
  const path = params.path.join('/');
  return proxyRequest(request, path);
}

export async function PATCH(request, { params }) {
  const path = params.path.join('/');
  return proxyRequest(request, path);
}

export async function DELETE(request, { params }) {
  const path = params.path.join('/');
  return proxyRequest(request, path);
}

export async function OPTIONS(request) {
  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  });
}

