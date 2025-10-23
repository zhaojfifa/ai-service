export const API_BASE = 'https://ai-service-x758.onrender.com'; // 替换为你的后端 URL

export async function apiJSON(path, body, method = 'POST') {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'omit',
    mode: 'cors',
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${method} ${path} ${response.status}: ${text}`);
  }
  return response.json();
}

export async function presignPut(filename, contentType, folder = 'assets/user') {
  return apiJSON('/api/r2/presign-put', {
    filename,
    content_type: contentType,
    folder,
  });
}

export async function putToR2(uploadUrl, file) {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': file.type },
    body: file,
  });
  if (!response.ok) {
    throw new Error(`R2 PUT failed: ${response.status}`);
  }
}

export async function generatePoster(payload) {
  return apiJSON('/api/generate-poster', payload, 'POST');
}
