const API_BASE = '/api/v1';

async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
}

async function apiPost(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
}

async function apiDelete(path) {
    const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
}

async function fetchRoutes(params = {}) {
    const body = {
        city: params.city || undefined,
        difficulty: params.difficulty || undefined,
        keyword: params.keyword || undefined,
        min_distance: params.minDistance || undefined,
        max_distance: params.maxDistance || undefined,
        tags: params.tags || undefined,
        limit: params.limit || 20,
        offset: params.offset || 0,
    };
    Object.keys(body).forEach(k => body[k] === undefined && delete body[k]);
    return apiPost('/routes/search', body);
}

async function fetchRouteDetail(routeId) {
    return apiGet(`/routes/${routeId}`);
}

async function chatWithAgent(sessionId, userId, message) {
    return apiPost('/agent/chat', {
        session_id: sessionId,
        user_id: userId,
        message: message,
    });
}

function chatStreamUrl() {
    return `${API_BASE}/agent/chat/stream`;
}

async function fetchSessionHistory(sessionId) {
    return apiGet(`/agent/sessions/${sessionId}/history`);
}

async function clearSession(sessionId) {
    return apiDelete(`/agent/sessions/${sessionId}`);
}
