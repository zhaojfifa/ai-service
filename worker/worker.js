const DEFAULT_ALLOWED_METHODS = 'GET,POST,PUT,PATCH,DELETE,OPTIONS';
const DEFAULT_ALLOWED_HEADERS = '*';
const DEFAULT_EXPOSE_HEADERS = '*';
const PREFLIGHT_MAX_AGE = '86400';
const DATA_API_PREFIX = '/api/';
const HEALTH_PATH = '/health';
const API_HEALTH_PATH = '/api/health';

function normaliseBase(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    parsed.pathname = parsed.pathname.replace(/\/$/, '');
    parsed.search = '';
    parsed.hash = '';
    return parsed.toString();
  } catch (error) {
    console.error('Invalid upstream origin', url, error);
    return null;
  }
}

function parseAllowedOrigins(value) {
  if (!value) return ['*'];
  if (Array.isArray(value)) return value.length ? value : ['*'];
  const trimmed = value.trim();
  if (!trimmed) return ['*'];
  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed) && parsed.length) {
      return parsed.map((item) => normaliseOrigin(item)).filter(Boolean);
    }
  } catch (error) {
    // fall through to CSV parsing
  }
  return trimmed
    .split(',')
    .map((item) => normaliseOrigin(item))
    .filter(Boolean)
    .filter((item, index, array) => array.indexOf(item) === index);
}

function normaliseOrigin(value) {
  if (!value) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const attempts = [trimmed];
  if (!/^https?:\/\//i.test(trimmed)) {
    attempts.push(`https://${trimmed}`);
  }
  for (const attempt of attempts) {
    try {
      const url = new URL(attempt);
      if (!url.host) continue;
      const scheme = url.protocol.replace(/:$/, '').toLowerCase();
      if (scheme !== 'https' && scheme !== 'http') {
        continue;
      }
      return `${scheme}://${url.host}`;
    } catch (error) {
      // try next attempt
    }
  }
  return null;
}

function resolveAllowOrigin(requestOrigin, allowedOrigins) {
  if (!Array.isArray(allowedOrigins) || !allowedOrigins.length) return '*';
  if (allowedOrigins.includes('*')) return '*';
  if (requestOrigin && allowedOrigins.includes(requestOrigin)) {
    return requestOrigin;
  }
  return allowedOrigins[0];
}

function buildCorsHeaders(request, env) {
  const allowHeaders = env.CORS_ALLOW_HEADERS || DEFAULT_ALLOWED_HEADERS;
  const exposeHeaders = env.CORS_EXPOSE_HEADERS || DEFAULT_EXPOSE_HEADERS;
  const requestOrigin = request.headers.get('Origin');
  const allowedOrigins = parseAllowedOrigins(env.ALLOWED_ORIGINS);
  const allowOrigin = resolveAllowOrigin(requestOrigin, allowedOrigins);

  const headers = {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': env.CORS_ALLOW_METHODS || DEFAULT_ALLOWED_METHODS,
    'Access-Control-Allow-Headers': allowHeaders,
    'Access-Control-Expose-Headers': exposeHeaders,
    'Access-Control-Max-Age': env.CORS_MAX_AGE || PREFLIGHT_MAX_AGE,
  };
  if (allowOrigin !== '*') {
    headers.Vary = 'Origin';
  }
  return headers;
}

function withCors(response, corsHeaders) {
  const headers = new Headers(response.headers);
  Object.entries(corsHeaders).forEach(([key, value]) => {
    headers.set(key, value);
  });
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function notFoundResponse(request, corsHeaders) {
  return new Response('Not found', {
    status: 404,
    headers: corsHeaders,
  });
}

function shouldProxy(pathname) {
  return (
    pathname === HEALTH_PATH ||
    pathname === API_HEALTH_PATH ||
    pathname.startsWith(DATA_API_PREFIX)
  );
}

function sanitiseHeaders(headers) {
  const cleaned = new Headers(headers);
  cleaned.delete('cookie');
  cleaned.delete('Cookie');
  cleaned.delete('cookie2');
  return cleaned;
}

async function handleProxy(request, env) {
  const corsHeaders = buildCorsHeaders(request, env);

  if (request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  const url = new URL(request.url);
  if (!shouldProxy(url.pathname)) {
    return notFoundResponse(request, corsHeaders);
  }

  if (url.pathname === API_HEALTH_PATH) {
    return new Response('ok', { status: 200, headers: corsHeaders });
  }

  const upstreamOrigin =
    normaliseBase(env.RENDER_ORIGIN || env.ORIGIN || env.RENDER_BASE || env.UPSTREAM_BASE);
  if (!upstreamOrigin) {
    return new Response('Missing upstream origin', {
      status: 500,
      headers: corsHeaders,
    });
  }

  const targetUrl = new URL(url.pathname + url.search, upstreamOrigin);
  const requestClone = request.clone();
  const method = requestClone.method || 'GET';
  const headers = sanitiseHeaders(requestClone.headers);
  const bodyAllowed = !['GET', 'HEAD'].includes(method.toUpperCase());
  const init = {
    method,
    headers,
    redirect: 'follow',
  };
  if (bodyAllowed) {
    init.body = requestClone.body;
  }

  let upstreamResponse;
  try {
    upstreamResponse = await fetch(targetUrl.toString(), init);
  } catch (error) {
    console.error('Upstream request failed', error);
    return new Response('Upstream fetch failed', {
      status: 502,
      headers: corsHeaders,
    });
  }

  return withCors(upstreamResponse, corsHeaders);
}

export default {
  async fetch(request, env) {
    try {
      return await handleProxy(request, env);
    } catch (error) {
      console.error('Worker proxy error', error);
      const corsHeaders = buildCorsHeaders(request, env);
      return new Response('Worker internal error', {
        status: 502,
        headers: corsHeaders,
      });
    }
  },
};
