import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const appJs = readFileSync(new URL('../frontend/app.js', import.meta.url), 'utf8');
const [utilsSnippet] = appJs.split('const STORAGE_KEYS = {');

const sandbox = {
  window: { App: {} },
  document: {
    querySelector: () => null,
    body: { dataset: {} },
    getElementById: () => null,
  },
  localStorage: {
    getItem: () => null,
    setItem: () => undefined,
  },
  sessionStorage: {
    getItem: () => null,
    setItem: () => undefined,
  },
  STORAGE_KEYS: { apiBase: 'marketing-poster-api-base' },
  console,
  URL,
  TextEncoder,
  Response,
  Request,
  Headers,
  setTimeout,
  clearTimeout,
  fetch: async () => new Response(JSON.stringify({ status: 'ok' }), { status: 200 }),
};

vm.runInNewContext(`${utilsSnippet}\nmodule.exports = window.App.utils;`, sandbox, {
  filename: 'app-utils-snippet.js',
});

const utils = sandbox.module.exports;

sandbox.fetch = async (url, options = {}) => {
  const href = typeof url === 'string' ? url : url.url;
  if (href.includes('primary.example.com/api/health')) {
    throw new Error('primary offline');
  }
  if (href.includes('primary.example.com/health')) {
    throw new Error('primary offline 2');
  }
  if (href.includes('backup.example.com/api/health')) {
    return new Response(JSON.stringify({ status: 'ok' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  if (href.includes('/api/demo')) {
    const body = options.body ? JSON.parse(options.body) : {};
    return new Response(JSON.stringify({ echo: body, base: href.split('/api/')[0] }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }
  return new Response(JSON.stringify({ status: 'ok' }), { status: 200 });
};

const bases = ['https://primary.example.com', 'https://backup.example.com'];

await utils.warmUp(bases, { force: true });
const healthy = await utils.pickHealthyBase(bases);
console.log('healthy base:', healthy);

const payload = { demo: 'value' };
const response = await utils.postJsonWithRetry(bases, '/api/demo', payload, 1);
console.log('demo response:', await response.json());
