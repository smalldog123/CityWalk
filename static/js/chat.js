let currentSessionId = null;
let currentUserId = 'web_user_' + Math.random().toString(36).substring(2, 8);
let isStreaming = false;

function generateSessionId() {
    return 'sess_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8);
}

function ensureSession() {
    if (!currentSessionId) {
        currentSessionId = generateSessionId();
    }
    return currentSessionId;
}

function sendQuickAction(text) {
    document.getElementById('chat-input').value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message || isStreaming) return;

    input.value = '';
    autoResize(input);
    ensureSession();

    const welcome = document.getElementById('chat-welcome');
    if (welcome) welcome.style.display = 'none';

    appendMessage('user', message);
    const assistantEl = appendAssistantMessage();

    isStreaming = true;
    updateSendButton();

    try {
        await streamChat(message, assistantEl);
    } catch (err) {
        removeTypingIndicator(assistantEl);
        renderError(assistantEl, err.message || '网络连接失败，请检查服务是否正常运行');
    } finally {
        isStreaming = false;
        updateSendButton();
        removeTypingIndicator(assistantEl);
    }
}

async function streamChat(message, assistantEl) {
    let response;
    try {
        response = await fetch(chatStreamUrl(), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                user_id: currentUserId,
                message: message,
            }),
        });
    } catch (err) {
        throw new Error('网络连接失败，请检查服务是否正常运行');
    }

    if (!response.ok) {
        throw new Error(`服务返回错误 (HTTP ${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';
    let routeRecommendations = [];
    let hasError = false;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
            if (!line.startsWith('data:')) continue;
            const data = line.substring(5).trim();
            if (!data || data === '[DONE]') continue;

            try {
                const event = JSON.parse(data);

                if (event.type === 'error') {
                    hasError = true;
                    removeTypingIndicator(assistantEl);
                    renderError(assistantEl, event.content || '未知错误');
                    return;
                }

                handleSSEEvent(event, assistantEl, fullText);
                if (event.type === 'text' && event.content) {
                    fullText += event.content;
                }
                if (event.type === 'route_recommendations' && event.routes) {
                    routeRecommendations = event.routes;
                }
            } catch (e) {
                // skip malformed data
            }
        }
    }

    if (routeRecommendations.length > 0) {
        renderRouteRecommendations(assistantEl, routeRecommendations);
    }

    if (fullText && !hasError) {
        renderMarkdown(assistantEl, fullText);
    }
}

function handleSSEEvent(event, assistantEl, currentText) {
    switch (event.type) {
        case 'text':
            removeTypingIndicator(assistantEl);
            appendToElement(assistantEl, event.content || '');
            break;
        case 'tool_call':
            appendToolCall(assistantEl, event.tool_name, event.arguments);
            break;
        case 'tool_result':
            break;
        case 'route_recommendations':
            break;
    }
}

function appendMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = `message ${role}`;

    const avatar = role === 'user' ? 'U' : 'AI';
    const roleName = role === 'user' ? '你' : 'CityWalk 助手';

    msg.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-role">${roleName}</div>
            <div class="message-text">${escapeHtml(content)}</div>
        </div>`;

    container.appendChild(msg);
    scrollToBottom();
    return msg;
}

function appendAssistantMessage() {
    const container = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = 'message assistant';

    msg.innerHTML = `
        <div class="message-avatar">AI</div>
        <div class="message-content">
            <div class="message-role">CityWalk 助手</div>
            <div class="message-text">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        </div>`;

    container.appendChild(msg);
    scrollToBottom();
    return msg;
}

function appendToElement(el, text) {
    const textEl = el.querySelector('.message-text');
    if (!textEl) return;

    const typing = textEl.querySelector('.typing-indicator');
    const errorEl = textEl.querySelector('.error-message');
    if (typing) {
        textEl.textContent = text;
    } else if (errorEl) {
        return;
    } else {
        textEl.textContent += text;
    }
    scrollToBottom();
}

function removeTypingIndicator(el) {
    const typing = el.querySelector('.typing-indicator');
    if (typing) typing.remove();
}

function renderError(el, message) {
    const textEl = el.querySelector('.message-text');
    if (!textEl) return;

    textEl.innerHTML = `
        <div class="error-message" style="
            padding: 12px 16px;
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            color: #991b1b;
            font-size: 14px;
            line-height: 1.6;
        ">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;font-weight:600">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                智能助手暂时不可用
            </div>
            <div>${escapeHtml(message)}</div>
            <div style="margin-top:8px;font-size:12px;color:#b91c1c;opacity:0.8">
                请检查：1) .env 文件中的 OPENAI_API_KEY 是否配置正确 &nbsp; 2) 网络是否能访问 AI 服务 &nbsp; 3) OPENAI_BASE_URL 是否正确
            </div>
        </div>`;
    scrollToBottom();
}

function renderMarkdown(el, text) {
    const textEl = el.querySelector('.message-text');
    if (!textEl) return;

    const errorEl = textEl.querySelector('.error-message');
    if (errorEl) return;

    let html = escapeHtml(text);

    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/《(.*?)》/g, '<strong>《$1》</strong>');

    html = html.replace(/^### (.+)$/gm, '<h4 style="font-size:15px;font-weight:600;margin:12px 0 6px">$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3 style="font-size:16px;font-weight:600;margin:12px 0 6px">$1</h3>');

    html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    html = '<p>' + html + '</p>';
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>\s*(<h[34])/g, '$1');
    html = html.replace(/(<\/h[34]>)\s*<\/p>/g, '$1');
    html = html.replace(/<p>\s*(<ul>)/g, '$1');
    html = html.replace(/(<\/ul>)\s*<\/p>/g, '$1');

    textEl.innerHTML = html;
    scrollToBottom();
}

function appendToolCall(el, toolName, args) {
    const textEl = el.querySelector('.message-text');
    if (!textEl) return;

    const toolDiv = document.createElement('div');
    toolDiv.className = 'message-tool-call';

    const nameMap = {
        search_routes: '搜索路线',
        search_knowledge: '知识检索',
        get_user_preference: '获取偏好',
        update_user_preference: '更新偏好',
    };

    const label = nameMap[toolName] || toolName;
    let desc = '';
    if (args) {
        if (args.city) desc += args.city + ' ';
        if (args.difficulty) desc += args.difficulty + ' ';
        if (args.keyword) desc += `"${args.keyword}" `;
        if (args.query) desc += `"${args.query}" `;
        if (args.tags) desc += args.tags.join(', ') + ' ';
    }

    toolDiv.innerHTML = `<span class="tool-name">${label}</span>${desc ? ' - ' + desc.trim() : ''}`;
    textEl.appendChild(toolDiv);
    scrollToBottom();
}

function renderRouteRecommendations(el, routes) {
    const textEl = el.querySelector('.message-text');
    if (!textEl) return;

    const container = document.createElement('div');
    container.className = 'message-routes';

    routes.forEach(route => {
        const diff = DIFFICULTY_MAP[route.difficulty] || { label: route.difficulty, class: '' };
        const card = document.createElement('div');
        card.className = 'message-route-card';
        card.onclick = () => showRouteDetail(route._id);
        card.innerHTML = `
            <div class="route-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
                    <polyline points="9 22 9 12 15 12 15 22"/>
                </svg>
            </div>
            <div class="route-info">
                <h4>${route.name}</h4>
                <div class="route-meta">
                    <span>${route.city}</span>
                    <span>${route.distance_km}km</span>
                    <span class="badge ${diff.class}" style="font-size:11px;padding:1px 8px">${diff.label}</span>
                </div>
            </div>`;
        container.appendChild(card);
    });

    textEl.appendChild(container);
    scrollToBottom();
}

function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
    });
}

function updateSendButton() {
    const btn = document.getElementById('send-btn');
    btn.disabled = isStreaming;
}

function handleInputKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
