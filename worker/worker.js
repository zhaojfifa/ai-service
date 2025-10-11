const ALLOWED_METHODS = 'GET,POST,OPTIONS';
const ALLOWED_HEADERS = 'Content-Type,Authorization,X-Requested-With';
const EXPOSE_HEADERS = 'Content-Length';
const PREFLIGHT_MAX_AGE = '600';

function buildCorsHeaders(request) {
  const origin = request.headers.get('Origin');
  const allowOrigin = origin || '*';
  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': ALLOWED_METHODS,
    'Access-Control-Allow-Headers': ALLOWED_HEADERS,
    'Access-Control-Expose-Headers': EXPOSE_HEADERS,
    'Access-Control-Max-Age': PREFLIGHT_MAX_AGE,
    Vary: 'Origin',
  };
}

function createNotFoundResponse(request) {
  return new Response('Not Found', {
    status: 404,
    headers: buildCorsHeaders(request),
  });
}

function normaliseUpstream(base) {
  if (!base) return null;
  try {
    const url = new URL(base);
    url.pathname = url.pathname.replace(/\/$/, '');
    return url.toString();
  } catch (error) {
    console.error('Invalid UPSTREAM_BASE', base, error);
    return null;
  }
}

async function proxyRequest(request, env) {
  const corsHeaders = buildCorsHeaders(request);
  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  const url = new URL(request.url);
  const isApiPath = url.pathname === '/health' || url.pathname === '/api' || url.pathname.startsWith('/api/');
  if (!isApiPath) {
    return createNotFoundResponse(request);
  }

  const upstreamBase = normaliseUpstream(env.UPSTREAM_BASE || env.RENDER_BASE);
  if (!upstreamBase) {
    return new Response('Missing UPSTREAM_BASE', {
      status: 500,
      headers: corsHeaders,
    });
  }

  const targetUrl = new URL(url.pathname + url.search, upstreamBase);
  const upstreamRequest = new Request(targetUrl.toString(), request);

  const upstreamResponse = await fetch(upstreamRequest, {
    cf: { cacheTtl: 0, cacheEverything: false },
  });

  const responseHeaders = new Headers(upstreamResponse.headers);
  Object.entries(corsHeaders).forEach(([key, value]) => {
    responseHeaders.set(key, value);
  });

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}

export default {
  async fetch(request, env, ctx) {
    try {
      return await proxyRequest(request, env, ctx);
    } catch (error) {
      console.error('Worker proxy error', error);
      return new Response('Worker Internal Error', {
        status: 502,
        headers: buildCorsHeaders(request),
      });
    }
  },
};
