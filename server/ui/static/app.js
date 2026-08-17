const messagesEl = document.getElementById('messages');
const emptyStateEl = document.getElementById('empty-state');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send-btn');
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const ragToggle = document.getElementById('rag-toggle');
const modelNameEl = document.getElementById('model-name');

let history = [];
let isStreaming = false;

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
}
inputEl.addEventListener('input', autoResize);

inputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});
sendBtn.addEventListener('click', sendMessage);

function addMessage(role, content) {
  if (emptyStateEl) emptyStateEl.remove();
  const wrap = document.createElement('div');
  wrap.className = `message ${role}`;
  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? 'You' : 'AI';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = content;
  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text || isStreaming) return;

  inputEl.value = '';
  autoResize();
  addMessage('user', text);
  history.push({ role: 'user', content: text });

  const bubble = addMessage('assistant', '');
  const cursor = document.createElement('span');
  cursor.className = 'cursor';
  bubble.appendChild(cursor);

  isStreaming = true;
  sendBtn.disabled = true;
  statusDot.classList.add('streaming');

  let fullText = '';

  try {
    const resp = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: history,
        stream: true,
        use_rag: ragToggle.checked,
      }),
    });

    if (!resp.ok || !resp.body) {
      throw new Error(`Server responded ${resp.status}`);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const data = trimmed.slice(5).trim();
        if (data === '[DONE]') continue;
        try {
          const parsed = JSON.parse(data);
          const delta = parsed.choices?.[0]?.delta?.content
            ?? parsed.choices?.[0]?.message?.content
            ?? '';
          if (delta) {
            fullText += delta;
            bubble.textContent = fullText;
            bubble.appendChild(cursor);
            messagesEl.scrollTop = messagesEl.scrollHeight;
          }
        } catch {
          // ignore malformed / keep-alive lines
        }
      }
    }
  } catch (err) {
    fullText = fullText || `Error reaching AnvilLLM: ${err.message}`;
    bubble.textContent = fullText;
  } finally {
    cursor.remove();
    if (fullText) history.push({ role: 'assistant', content: fullText });
    isStreaming = false;
    sendBtn.disabled = false;
    statusDot.classList.remove('streaming');
  }
}

async function pollHealth() {
  try {
    const resp = await fetch('/healthz');
    const data = await resp.json();
    if (data.status === 'ok') {
      statusDot.classList.add('online');
      statusText.textContent = 'Online';
    } else {
      statusDot.classList.remove('online');
      statusText.textContent = 'llama-server unreachable';
    }
  } catch {
    statusDot.classList.remove('online');
    statusText.textContent = 'API unreachable';
  }
}

async function loadModel() {
  try {
    const resp = await fetch('/v1/models');
    const data = await resp.json();
    if (data.data?.[0]?.id) {
      modelNameEl.textContent = data.data[0].id;
    }
  } catch {
    // keep default label
  }
}

pollHealth();
loadModel();
setInterval(pollHealth, 15000);
