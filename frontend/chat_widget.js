// Internal Chat Widget - AZ Marketing
// Floating messenger-style widget (blue, bottom-right) with unread badge.
// Self-contained: injects its own CSS + HTML + logic.
(function () {
    'use strict';

    if (document.getElementById('azChatWidgetRoot')) return;

    var TOKEN_KEY = 'token';
    var ACTIVE_WINDOW_MIN = 20; // Match online panel logic (< 20 min = active)
    var POLL_MS = 5000;         // Poll every 5 seconds

    var state = {
        open: false,
        showAll: false,
        otherId: null,
        myId: null,
        myName: null,
        users: [],
        convs: [],
        lastMsgId: 0,
        lastMsgCount: 0
    };

    function token() { return localStorage.getItem(TOKEN_KEY); }
    function apiHeaders() {
        return { 'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json' };
    }

    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function displayName(u) { return u.full_name && u.full_name.trim() ? u.full_name : u.username; }
    function initialOf(u) { return esc((displayName(u) || '?').charAt(0).toUpperCase()); }

    function lastSeenDate(u) {
        if (!u || !u.last_seen) return null;
        return new Date(u.last_seen + (String(u.last_seen).endsWith('Z') ? '' : 'Z'));
    }

    function isActive(u) {
        var d = lastSeenDate(u);
        if (!d) return false;
        var diffMin = (new Date() - d) / 1000 / 60;
        return diffMin <= ACTIVE_WINDOW_MIN;
    }

    function fmtTime(iso) {
        if (!iso) return '';
        var d = new Date(iso + (String(iso).endsWith('Z') ? '' : 'Z'));
        if (isNaN(d)) return '';
        var now = new Date();
        var hm = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
        var sameDay = d.toDateString() === now.toDateString();
        if (sameDay) return hm;
        return String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0') + ' ' + hm;
    }

    function fmtAgo(iso) {
        var d = lastSeenDate({ last_seen: iso });
        if (!d) return '';
        var diffMin = Math.floor((new Date() - d) / 1000 / 60);
        if (diffMin < 1) return 'en línea';
        if (diffMin === 1) return 'hace 1 min';
        if (diffMin < 60) return 'hace ' + diffMin + ' min';
        var hours = Math.floor(diffMin / 60);
        if (hours < 24) return 'hace ' + hours + ' h';
        var days = Math.floor(hours / 24);
        return 'hace ' + days + ' d';
    }

    // ---------- DOM ----------
    var root, launcher, badge, panel, contactsView, threadView;

    function buildDom() {
        root = document.createElement('div');
        root.id = 'azChatWidgetRoot';
        root.innerHTML = `
            <style>
                #azChatLauncher{position:fixed;bottom:20px;right:20px;z-index:2147483640;width:60px;height:60px;border-radius:50%;background:#1a73e8;border:none;cursor:pointer;box-shadow:0 6px 18px rgba(26,115,232,.45);display:flex;align-items:center;justify-content:center;color:#fff;transition:transform .15s}
                #azChatLauncher:hover{transform:scale(1.08)}
                #azChatLauncher .az-ico{font-size:26px;line-height:1}
                #azChatBadge{position:absolute;top:-4px;right:-4px;min-width:20px;height:20px;padding:0 5px;border-radius:10px;background:#ef4444;color:#fff;font-size:12px;font-weight:700;display:none;align-items:center;justify-content:center;box-sizing:border-box;font-family:Arial,Helvetica,sans-serif}
                #azChatPanel{position:fixed;bottom:92px;right:20px;z-index:2147483641;width:340px;max-width:calc(100vw - 24px);height:480px;max-height:calc(100vh - 120px);background:#fff;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.3);display:none;flex-direction:column;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1e293b}
                #azChatPanel *{box-sizing:border-box}
                .az-chat-header{background:#1a73e8;color:#fff;padding:12px 14px;display:flex;align-items:center;gap:10px;flex-shrink:0}
                .az-chat-header h3{margin:0;font-size:15px;font-weight:600;flex:1;display:flex;align-items:center;gap:8px}
                .az-chat-close{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;line-height:1;padding:2px}
                .az-chat-close:hover{opacity:.8}
                .az-chat-body{flex:1;overflow:hidden;display:flex;flex-direction:column;position:relative}
                .az-contacts-toolbar{padding:8px 10px;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;justify-content:space-between;gap:8px}
                .az-toggle-btn{background:#f1f5f9;border:1px solid #cbd5e1;color:#334155;border-radius:14px;padding:4px 10px;font-size:12px;cursor:pointer;font-family:inherit}
                .az-toggle-btn:hover{background:#e2e8f0}
                .az-active-count{font-size:12px;color:#64748b}
                .az-contact-list{flex:1;overflow-y:auto}
                .az-contact{display:flex;align-items:center;gap:10px;padding:10px 12px;cursor:pointer;border-bottom:1px solid #f1f5f9}
                .az-contact:hover{background:#f8fafc}
                .az-contact.inactive{opacity:.5}
                .az-avatar{width:38px;height:38px;border-radius:50%;background:#1a73e8;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;flex-shrink:0;position:relative}
                .az-avatar .az-dot{position:absolute;bottom:-1px;right:-1px;width:12px;height:12px;border-radius:50%;border:2px solid #fff;background:#cbd5e1}
                .az-avatar .az-dot.on{background:#22c55e}
                .az-contact-info{flex:1;min-width:0}
                .az-contact-name{font-size:13.5px;font-weight:600;display:flex;justify-content:space-between;align-items:center;gap:6px}
                .az-contact-role{font-size:10.5px;color:#64748b;text-transform:uppercase;background:#f1f5f9;border-radius:4px;padding:1px 5px;flex-shrink:0}
                .az-contact-preview{font-size:12px;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}
                .az-contact-unread{background:#ef4444;color:#fff;border-radius:10px;min-width:18px;height:18px;padding:0 5px;font-size:11px;font-weight:700;display:none;align-items:center;justify-content:center;flex-shrink:0}
                .az-thread{display:none;flex-direction:column;flex:1;min-height:0}
                .az-thread-head{display:flex;align-items:center;gap:8px;padding:10px 12px;border-bottom:1px solid #e2e8f0;background:#f8fafc}
                .az-back-btn{background:none;border:none;color:#1a73e8;font-size:18px;cursor:pointer;padding:2px 6px}
                .az-thread-name{font-weight:600;font-size:14px}
                .az-thread-status{font-size:11.5px;color:#64748b}
                .az-msgs{flex:1;overflow-y:auto;padding:12px;background:#f1f5f9;display:flex;flex-direction:column;gap:6px}
                .az-msg{max-width:78%;padding:7px 11px;border-radius:14px;font-size:13.5px;line-height:1.35;word-wrap:break-word;white-space:pre-wrap}
                .az-msg.mine{align-self:flex-end;background:#1a73e8;color:#fff;border-bottom-right-radius:4px}
                .az-msg.theirs{align-self:flex-start;background:#fff;border:1px solid #e2e8f0;border-bottom-left-radius:4px}
                .az-msg-meta{font-size:10px;opacity:.75;margin-top:3px;text-align:right;display:flex;justify-content:flex-end;gap:5px;align-items:center}
                .az-msg-empty{text-align:center;color:#94a3b8;font-size:13px;margin:auto}
                .az-input-row{display:flex;gap:8px;padding:10px;border-top:1px solid #e2e8f0;background:#fff;flex-shrink:0}
                .az-input-row input{flex:1;border:1px solid #cbd5e1;border-radius:20px;padding:9px 14px;font-size:13.5px;outline:none;font-family:inherit;color:#1e293b}
                .az-input-row input:focus{border-color:#1a73e8}
                .az-send-btn{background:#1a73e8;border:none;color:#fff;border-radius:50%;width:38px;height:38px;cursor:pointer;font-size:15px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
                .az-send-btn:hover{background:#1967d2}
                .az-sep{text-align:center;font-size:11px;color:#94a3b8;margin:4px 0}
            </style>

            <button id="azChatLauncher" title="Mensajes">
                <span class="az-ico">&#128172;</span>
                <span id="azChatBadge">0</span>
            </button>

            <div id="azChatPanel">
                <div class="az-chat-header">
                    <h3><span>&#128172;</span> Mensajes</h3>
                    <button class="az-chat-close" id="azChatClose" title="Cerrar">&times;</button>
                </div>
                <div class="az-chat-body" id="azChatContacts">
                    <div class="az-contacts-toolbar">
                        <span class="az-active-count" id="azActiveCount">Cargando...</span>
                        <button class="az-toggle-btn" id="azToggleAll">Ver todos</button>
                    </div>
                    <div class="az-contact-list" id="azContactList"></div>
                </div>
                <div class="az-thread" id="azChatThread">
                    <div class="az-thread-head">
                        <button class="az-back-btn" id="azBackBtn">&#8592;</button>
                        <div>
                            <div class="az-thread-name" id="azThreadName">...</div>
                            <div class="az-thread-status" id="azThreadStatus"></div>
                        </div>
                    </div>
                    <div class="az-msgs" id="azMsgs"></div>
                    <div class="az-input-row">
                        <input id="azMsgInput" type="text" maxlength="2000" placeholder="Escribe un mensaje...">
                        <button class="az-send-btn" id="azSendBtn">&#10148;</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(root);

        launcher = document.getElementById('azChatLauncher');
        badge = document.getElementById('azChatBadge');
        panel = document.getElementById('azChatPanel');
        contactsView = document.getElementById('azChatContacts');
        threadView = document.getElementById('azChatThread');

        launcher.addEventListener('click', togglePanel);
        document.getElementById('azChatClose').addEventListener('click', closePanel);
        document.getElementById('azToggleAll').addEventListener('click', function () {
            state.showAll = !state.showAll;
            renderContacts();
        });
        document.getElementById('azBackBtn').addEventListener('click', function () {
            state.otherId = null;
            threadView.style.display = 'none';
            contactsView.style.display = 'flex';
            renderContacts();
        });
        document.getElementById('azSendBtn').addEventListener('click', sendMessage);
        document.getElementById('azMsgInput').addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
        });
    }

    // ---------- API ----------
    async function apiGet(url) {
        var res = await fetch(url, { headers: apiHeaders() });
        if (!res.ok) throw new Error('API ' + res.status);
        return res.json();
    }
    async function apiPost(url, body) {
        var res = await fetch(url, {
            method: 'POST',
            headers: apiHeaders(),
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error('API ' + res.status);
        return res.json();
    }

    async function loadMe() {
        var me = await apiGet('/users/me');
        state.myId = me.id;
        state.myName = displayName(me);
    }

    async function loadContacts() {
        var users = await apiGet('/chat/users');
        var convs = await apiGet('/chat/conversations');
        state.users = users.filter(function (u) { return u.id !== state.myId; });
        state.convs = convs;
    }

    // ---------- Rendering ----------
    function renderContacts() {
        var list = state.users.map(function (u) {
            var conv = state.convs.filter(function (c) { return c.id === u.id; })[0];
            return {
                u: u,
                active: isActive(u),
                unread: conv ? conv.unread : 0,
                last_at: conv ? conv.last_at : null,
                last_message: conv ? conv.last_message : ''
            };
        });

        var activeCount = list.filter(function (c) { return c.active; }).length;
        var elCount = document.getElementById('azActiveCount');
        elCount.textContent = state.showAll
            ? (list.length + ' usuarios')
            : (activeCount + ' activo' + (activeCount === 1 ? '' : 's'));

        document.getElementById('azToggleAll').textContent = state.showAll ? 'Solo activos' : 'Ver todos';

        var visible = state.showAll ? list : list.filter(function (c) { return c.active; });

        visible.sort(function (a, b) {
            if (a.active !== b.active) return a.active ? -1 : 1;
            var ta = a.last_at ? new Date(a.last_at + (String(a.last_at).endsWith('Z') ? '' : 'Z')).getTime() : 0;
            var tb = b.last_at ? new Date(b.last_at + (String(b.last_at).endsWith('Z') ? '' : 'Z')).getTime() : 0;
            return tb - ta;
        });

        var container = document.getElementById('azContactList');
        if (visible.length === 0) {
            container.innerHTML = '<div style="text-align:center;color:#94a3b8;font-size:13px;padding:2rem 1rem;">No hay usuarios activos.</div>';
            return;
        }

        container.innerHTML = visible.map(function (c) {
            var u = c.u;
            var unreadHtml = c.unread > 0 ? '<span class="az-contact-unread" style="display:flex;">' + (c.unread > 99 ? '99+' : c.unread) + '</span>' : '';
            var preview = c.last_message ? esc(c.last_message) : (c.active ? 'En línea' : '');
            return '<div class="az-contact' + (c.active ? '' : ' inactive') + '" data-id="' + u.id + '">' +
                '<div class="az-avatar">' + initialOf(u) + '<span class="az-dot' + (c.active ? ' on' : '') + '"></span></div>' +
                '<div class="az-contact-info">' +
                    '<div class="az-contact-name"><span>' + esc(displayName(u)) + '</span><span class="az-contact-role">' + esc(u.role) + '</span></div>' +
                    '<div class="az-contact-preview">' + preview + '</div>' +
                '</div>' +
                unreadHtml +
            '</div>';
        }).join('');

        Array.prototype.forEach.call(container.querySelectorAll('.az-contact'), function (row) {
            row.addEventListener('click', function () {
                openConversation(parseInt(row.getAttribute('data-id'), 10));
            });
        });
    }

    function renderThread(conversation) {
        var other = conversation.other;
        document.getElementById('azThreadName').textContent = displayName(other);
        var statusEl = document.getElementById('azThreadStatus');
        if (isActive(other)) {
            statusEl.innerHTML = '<span style="color:#22c55e;">&#9679;</span> En línea';
        } else {
            statusEl.textContent = fmtAgo(other.last_seen);
        }

        var container = document.getElementById('azMsgs');
        var msgs = conversation.messages;
        if (!msgs || msgs.length === 0) {
            container.innerHTML = '<div class="az-msg-empty">Aún no hay mensajes. ¡Saluda!</div>';
            state.lastMsgCount = 0;
            state.lastMsgId = 0;
            return;
        }

        var html = '';
        var prevDate = null;
        msgs.forEach(function (m) {
            var d = m.created_at ? new Date(m.created_at + (String(m.created_at).endsWith('Z') ? '' : 'Z')) : null;
            var dayKey = d ? d.toDateString() : '';
            if (dayKey && dayKey !== prevDate) {
                html += '<div class="az-sep">' + esc(d.toLocaleDateString('es-CO', { weekday: 'long', day: 'numeric', month: 'long' })) + '</div>';
                prevDate = dayKey;
            }
            var mine = m.sender_id === state.myId;
            var seen = (mine && m.read_at) ? '<span title="Visto">&#10003;&#10003;</span>' : '';
            html += '<div class="az-msg ' + (mine ? 'mine' : 'theirs') + '" data-msg-id="' + m.id + '">' +
                esc(m.message) +
                '<div class="az-msg-meta">' + fmtTime(m.created_at) + seen + '</div>' +
            '</div>';
        });
        container.innerHTML = html;
        container.scrollTop = container.scrollHeight;
        state.lastMsgCount = msgs.length;
        state.lastMsgId = msgs[msgs.length - 1].id;
    }

    // ---------- Actions ----------
    function togglePanel() {
        if (state.open) { closePanel(); } else { openPanel(); }
    }

    async function openPanel() {
        state.open = true;
        panel.style.display = 'flex';
        if (!state.myId) { try { await loadMe(); } catch (e) { return; } }
        try {
            await loadContacts();
            renderContacts();
        } catch (e) { console.error('Chat: error loading contacts', e); }
    }

    function closePanel() {
        state.open = false;
        panel.style.display = 'none';
        state.otherId = null;
        threadView.style.display = 'none';
        contactsView.style.display = 'flex';
    }

    async function openConversation(otherId) {
        state.otherId = otherId;
        contactsView.style.display = 'none';
        threadView.style.display = 'flex';
        document.getElementById('azMsgs').innerHTML = '<div class="az-msg-empty">Cargando...</div>';
        document.getElementById('azMsgInput').value = '';
        try {
            var conv = await apiGet('/chat/conversation/' + otherId);
            renderThread(conv);
            document.getElementById('azMsgInput').focus();
            refreshUnread();
        } catch (e) {
            console.error('Chat: error loading conversation', e);
            document.getElementById('azMsgs').innerHTML = '<div class="az-msg-empty">Error al cargar la conversación.</div>';
        }
    }

    async function sendMessage() {
        var input = document.getElementById('azMsgInput');
        var text = input.value.trim();
        if (!text || !state.otherId) return;
        input.value = '';
        try {
            var msg = await apiPost('/chat/send', { receiver_id: state.otherId, message: text });
            var container = document.getElementById('azMsgs');
            var empty = container.querySelector('.az-msg-empty');
            if (empty) container.innerHTML = '';
            var mine = msg.sender_id === state.myId;
            var html = '<div class="az-msg ' + (mine ? 'mine' : 'theirs') + '" data-msg-id="' + msg.id + '">' +
                esc(msg.message) +
                '<div class="az-msg-meta">' + fmtTime(msg.created_at) + '</div>' +
            '</div>';
            container.insertAdjacentHTML('beforeend', html);
            container.scrollTop = container.scrollHeight;
            state.lastMsgId = msg.id;
            state.lastMsgCount += 1;
        } catch (e) {
            console.error('Chat: error sending', e);
            alert('Error al enviar el mensaje. Intenta de nuevo.');
            input.value = text;
        }
    }

    // ---------- Badge ----------
    async function refreshUnread() {
        if (!token()) return;
        try {
            var data = await apiGet('/chat/unread-count');
            var count = data.count || 0;
            badge.textContent = count > 99 ? '99+' : String(count);
            badge.style.display = count > 0 ? 'flex' : 'none';
        } catch (e) {
            // silent: server may be unreachable
        }
    }

    // ---------- Polling ----------
    async function poll() {
        if (!token()) return;
        try { await refreshUnread(); } catch (e) { return; }
        if (!state.open) return;
        try {
            if (state.otherId) {
                var conv = await apiGet('/chat/conversation/' + state.otherId);
                var msgs = conv.messages || [];
                var changed = msgs.length !== state.lastMsgCount ||
                    (msgs.length > 0 && msgs[msgs.length - 1].id !== state.lastMsgId);
                if (changed) renderThread(conv);
            } else if (state.myId) {
                await loadContacts();
                renderContacts();
            }
        } catch (e) {
            // silent
        }
    }

    // ---------- Init ----------
    function init() {
        buildDom();
        refreshUnread();
        setInterval(poll, POLL_MS);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
