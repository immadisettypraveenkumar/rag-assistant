/* ── RAGchat Frontend ─────────────────────────────────────────────── */
'use strict';

const API_BASE = '';          // same origin; change to http://localhost:8000 for dev
const STORAGE_KEY = 'ragchat_sessions';

// ── State ──────────────────────────────────────────────────────────────
let currentSessionId = null;
let sessions = {};            // { id: { title, messages: [{role,content,meta}] } }
let isLoading = false;

// ── DOM refs ───────────────────────────────────────────────────────────
const messagesEl     = document.getElementById('messages');
const messagesWrap   = document.getElementById('messagesWrap');
const inputEl        = document.getElementById('messageInput');
const sendBtn        = document.getElementById('sendBtn');
const newChatBtn     = document.getElementById('newChatBtn');
const sessionList    = document.getElementById('sessionList');
const sessionLabel   = document.getElementById('sessionLabel');
const statusDot      = document.getElementById('statusDot');
const metaBar        = document.getElementById('metaBar');
const typingIndicator= document.getElementById('typingIndicator');
const sidebarToggle  = document.getElementById('sidebarToggle');
const sidebar        = document.querySelector('.sidebar');
const welcomeScreen  = document.getElementById('welcomeScreen');

// ── Init ───────────────────────────────────────────────────────────────
function init() {
  loadSessions();
  checkHealth();
  setInterval(checkHealth, 30_000);

  // Restore last session or create new
  const ids = Object.keys(sessions);
  if (ids.length > 0) {
    loadSession(ids[ids.length - 1]);
  } else {
    startNewSession();
  }

  bindEvents();
}

// ── Health check ───────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    const dot = statusDot.querySelector('.dot');
    const txt = statusDot.querySelector('.status-text');
    if (data.status === 'healthy') {
      dot.className = 'dot healthy';
      txt.textContent = `${data.chunksIndexed} chunks indexed`;
    } else {
      dot.className = 'dot error';
      txt.textContent = 'Unhealthy';
    }
  } catch {
    const dot = statusDot.querySelector('.dot');
    statusDot.querySelector('.status-text').textContent = 'Offline';
    dot.className = 'dot error';
  }
}

// ── Session management ─────────────────────────────────────────────────
function generateId() {
  return 'sess_' + Math.random().toString(36).slice(2, 10) + '_' + Date.now().toString(36);
}

function startNewSession() {
  const id = generateId();
  sessions[id] = { title: 'New chat', messages: [] };
  currentSessionId = id;
  saveSessions();
  renderSessionList();
  renderMessages();
  updateSessionLabel();
}

function loadSession(id) {
  currentSessionId = id;
  renderMessages();
  updateSessionLabel();
  renderSessionList();
}

function updateSessionLabel() {
  const s = sessions[currentSessionId];
  sessionLabel.textContent = `Session: ${currentSessionId}`;
}

function renderSessionList() {
  sessionList.innerHTML = '';
  const ids = Object.keys(sessions).reverse();
  ids.forEach(id => {
    const s = sessions[id];
    const el = document.createElement('div');
    el.className = 'session-item' + (id === currentSessionId ? ' active' : '');
    el.textContent = s.title;
    el.title = id;
    el.addEventListener('click', () => {
      loadSession(id);
      sidebar.classList.remove('open');
    });
    sessionList.appendChild(el);
  });
}

function saveSessions() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch { /* storage full */ }
}

function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) sessions = JSON.parse(raw);
  } catch {
    sessions = {};
  }
}

// ── Message rendering ──────────────────────────────────────────────────
function renderMessages() {
  const s = sessions[currentSessionId];
  messagesEl.innerHTML = '';

  if (!s || s.messages.length === 0) {
    messagesEl.appendChild(buildWelcome());
    return;
  }

  s.messages.forEach(m => messagesEl.appendChild(buildBubble(m)));
  scrollToBottom();
}

function buildWelcome() {
  const div = document.createElement('div');
  div.className = 'welcome';
  div.id = 'welcomeScreen';
  div.innerHTML = `
    <span class="welcome-icon">◈</span>
    <h1>How can I help you?</h1>
    <p>Ask anything about accounts, billing, APIs, integrations, or troubleshooting.</p>
    <div class="suggested-chips">
      <button class="chip" data-q="How do I reset my password?">Reset password</button>
      <button class="chip" data-q="What subscription plans do you offer?">Subscription plans</button>
      <button class="chip" data-q="How do I use the REST API?">API usage</button>
      <button class="chip" data-q="How does offline mode work on mobile?">Offline mode</button>
      <button class="chip" data-q="What integrations are supported?">Integrations</button>
    </div>`;
  div.querySelectorAll('.chip').forEach(c => {
    c.addEventListener('click', () => sendMessage(c.dataset.q));
  });
  return div;
}

function buildBubble(msg) {
  const div = document.createElement('div');
  div.className = `msg ${msg.role}`;

  const avatarChar = msg.role === 'user' ? '▸' : '◈';
  const meta = msg.meta || {};

  let metaHtml = `<span class="msg-meta">${formatTime(msg.ts || Date.now())}`;
  if (msg.role === 'assistant') {
    if (meta.retrievedChunks != null)
      metaHtml += `<span class="chunk-badge">⬡ ${meta.retrievedChunks} chunks</span>`;
    if (meta.tokensUsed)
      metaHtml += `<span class="tokens-badge">${meta.tokensUsed} tokens</span>`;
  }
  metaHtml += '</span>';

  div.innerHTML = `
    <div class="avatar">${avatarChar}</div>
    <div class="bubble-wrap">
      <div class="bubble">${renderMarkdown(msg.content)}</div>
      ${metaHtml}
    </div>`;
  return div;
}

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Very lightweight markdown renderer
function renderMarkdown(text) {
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
    .replace(/^\s*[-*•] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(.+)$/gm, (line) =>
      line.startsWith('<') ? line : `<p>${line}</p>`)
    .replace(/<p><\/p>/g, '')
    .replace(/<p>(<ul>)/g, '$1')
    .replace(/<\/ul><\/p>/g, '</ul>');
}

function appendBubble(msg) {
  // Remove welcome screen if present
  const ws = messagesEl.querySelector('.welcome');
  if (ws) ws.remove();

  const el = buildBubble(msg);
  messagesEl.appendChild(el);
  scrollToBottom();
}

function scrollToBottom() {
  requestAnimationFrame(() => {
    messagesWrap.scrollTop = messagesWrap.scrollHeight;
  });
}

// ── Typing indicator ───────────────────────────────────────────────────
function showTyping() {
  // Insert typing indicator inside messages
  const ws = messagesEl.querySelector('.welcome');
  if (ws) ws.remove();

  const wrapper = document.createElement('div');
  wrapper.className = 'msg assistant';
  wrapper.id = 'typingMsg';
  wrapper.innerHTML = `
    <div class="avatar">◈</div>
    <div class="bubble-wrap">
      <div class="typing-indicator" style="display:flex">
        <span></span><span></span><span></span>
      </div>
    </div>`;
  messagesEl.appendChild(wrapper);
  scrollToBottom();
}

function hideTyping() {
  const el = document.getElementById('typingMsg');
  if (el) el.remove();
}

// ── Send message ───────────────────────────────────────────────────────
async function sendMessage(text) {
  text = (text || inputEl.value).trim();
  if (!text || isLoading) return;

  inputEl.value = '';
  autoResize();
  setLoading(true);

  const ts = Date.now();
  const userMsg = { role: 'user', content: text, ts };
  sessions[currentSessionId].messages.push(userMsg);

  // Auto-title from first message
  if (sessions[currentSessionId].messages.length === 1) {
    sessions[currentSessionId].title = text.slice(0, 36) + (text.length > 36 ? '…' : '');
    renderSessionList();
  }

  appendBubble(userMsg);
  showTyping();
  updateMetaBar(null);

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sessionId: currentSessionId, message: text }),
    });

    const data = await res.json();
    hideTyping();

    if (!res.ok) {
      const errMsg = { role: 'assistant', content: data.detail || data.error || 'Something went wrong.', ts: Date.now(), meta: {} };
      sessions[currentSessionId].messages.push(errMsg);
      appendBubble(errMsg);
    } else {
      const aiMsg = {
        role: 'assistant',
        content: data.reply,
        ts: Date.now(),
        meta: { tokensUsed: data.tokensUsed, retrievedChunks: data.retrievedChunks }
      };
      sessions[currentSessionId].messages.push(aiMsg);
      appendBubble(aiMsg);
      updateMetaBar(data);
    }
  } catch (err) {
    hideTyping();
    const errMsg = { role: 'assistant', content: 'Network error – please check your connection and try again.', ts: Date.now(), meta: {} };
    sessions[currentSessionId].messages.push(errMsg);
    appendBubble(errMsg);
  }

  saveSessions();
  setLoading(false);
}

function updateMetaBar(data) {
  if (!data) { metaBar.innerHTML = ''; return; }
  metaBar.innerHTML = `
    <span class="meta-badge">⬡ <span>${data.retrievedChunks}</span> chunks</span>
    <span class="meta-badge">⬡ <span>${data.tokensUsed}</span> tokens</span>`;
}

function setLoading(val) {
  isLoading = val;
  sendBtn.disabled = val;
  inputEl.disabled = val;
}

// ── Auto-resize textarea ───────────────────────────────────────────────
function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
}

// ── Bind events ────────────────────────────────────────────────────────
function bindEvents() {
  sendBtn.addEventListener('click', () => sendMessage());

  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  inputEl.addEventListener('input', autoResize);

  newChatBtn.addEventListener('click', () => {
    startNewSession();
    sidebar.classList.remove('open');
  });

  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
  });

  // Close sidebar when clicking outside on mobile
  messagesWrap.addEventListener('click', () => {
    sidebar.classList.remove('open');
  });

  // Chip clicks on initial welcome screen
  document.querySelectorAll('#suggestedChips .chip').forEach(c => {
    c.addEventListener('click', () => sendMessage(c.dataset.q));
  });
}

// ── Bootstrap ──────────────────────────────────────────────────────────
init();
