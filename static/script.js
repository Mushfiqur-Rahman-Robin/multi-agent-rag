document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();

    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const messagesContainer = document.getElementById('messages-container');
    const chatViewport = document.getElementById('chat-viewport');
    const welcomeScreen = document.getElementById('welcome-screen');
    const historyList = document.getElementById('history-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const fileInput = document.getElementById('file-input');
    const attachBtn = document.getElementById('attach-btn');
    const attachmentPreview = document.getElementById('attachment-preview');

    let currentThreadId = null;
    let selectedFiles = [];

    // --- Core Functions ---

    async function loadSessions() {
        try {
            const response = await fetch('/sessions');
            const sessions = await response.json();
            renderSessionList(sessions);
        } catch (error) {
            console.error('Error loading sessions:', error);
        }
    }

    function renderSessionList(sessions) {
        historyList.innerHTML = '';
        sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = `history-item ${currentThreadId === session.thread_id ? 'active' : ''}`;
            item.innerHTML = `
                <div class="title">${session.title || 'Untitled Chat'}</div>
                <div class="actions">
                    <i data-lucide="trash-2" class="delete-btn" data-id="${session.thread_id}"></i>
                </div>
            `;
            item.onclick = () => switchSession(session.thread_id);

            const delBtn = item.querySelector('.delete-btn');
            delBtn.onclick = (e) => {
                e.stopPropagation();
                deleteSession(session.thread_id);
            };

            historyList.appendChild(item);
        });
        lucide.createIcons();
    }

    // --- Utilities ---

    function parseMarkdown(text) {
        if (!text) return '';
        if (typeof text !== 'string') text = String(text);
        try {
            if (window.marked) {
                return typeof marked.parse === 'function' ? marked.parse(text) : marked(text);
            }
            return text;
        } catch (e) {
            console.error('Markdown parsing error:', e);
            return text;
        }
    }

    async function switchSession(threadId) {
        currentThreadId = threadId;
        welcomeScreen.style.display = 'none';
        messagesContainer.innerHTML = '<div class="loading">Loading conversation...</div>';

        try {
            const response = await fetch(`/sessions/${threadId}`);
            const messages = await response.json();
            messagesContainer.innerHTML = '';
            messages.forEach(msg => {
                let content = msg.content;
                if (typeof content === 'string') {
                    try {
                        content = JSON.parse(content);
                    } catch (e) {
                        // Keep as string if not JSON
                    }
                }
                addMessageToUI(msg.role === 'human' ? 'human' : 'ai', content);
            });
            scrollToBottom();
            loadSessions(); // Update active state
        } catch (error) {
            console.error('Error switching session:', error);
            messagesContainer.innerHTML = '<div class="error">Failed to load conversation.</div>';
        }
    }
    async function deleteSession(threadId) {
        if (!confirm('Are you sure you want to delete this chat?')) return;
        try {
            await fetch(`/sessions/${threadId}`, { method: 'DELETE' });
            if (currentThreadId === threadId) {
                resetChat();
            }
            loadSessions();
        } catch (error) {
            console.error('Error deleting session:', error);
        }
    }

    function resetChat() {
        currentThreadId = null;
        messagesContainer.innerHTML = '';
        welcomeScreen.style.display = 'flex';
        historyList.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
    }

    // --- Core Functions ---

    function addMessageToUI(role, content) {
        console.log(`[UI] Adding ${role} message. Content type: ${typeof content}`, content);
        welcomeScreen.style.display = 'none';

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        let htmlContent = '';
        if (role === 'human') {
            const text = typeof content === 'string' ? content : (content.message || JSON.stringify(content));
            htmlContent = `<div class="msg-content">${text}</div>`;
        } else {
            // AI message might have thought, response, research, plan, code
            const thoughtHtml = content.thought ? `
                <div class="agent-thought">
                    <i data-lucide="brain"></i>
                    <span>${content.thought}</span>
                </div>` : '';

            const responseHtml = content.response ? `
                <div class="final-response">${parseMarkdown(content.response)}</div>` : '';

            const researchHtml = content.research ? `
                <div class="agent-step">
                    <div class="step-header">Research Findings</div>
                    <div class="step-body">${parseMarkdown(content.research)}</div>
                </div>` : '';

            const planHtml = content.plan ? `
                <div class="agent-step">
                    <div class="step-header">Execution Plan</div>
                    <div class="step-body">${parseMarkdown(content.plan)}</div>
                </div>` : '';

            const codeHtml = content.code ? `
                <div class="agent-step">
                    <div class="step-header">Coded Implementation / Output</div>
                    <div class="step-body"><pre><code>${content.code}</code></pre></div>
                </div>` : '';

            // Construct the inner message structure
            htmlContent = `
                <div class="msg-content">
                    ${thoughtHtml}
                    ${responseHtml}
                    ${researchHtml}
                    ${planHtml}
                    ${codeHtml}
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-inner">
                <div class="msg-avatar">
                    <i data-lucide="${role === 'human' ? 'user' : 'bot'}"></i>
                </div>
                ${htmlContent}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        if (window.lucide) lucide.createIcons();
        scrollToBottom();
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text && selectedFiles.length === 0) return;

        // Temporarily disable input
        chatInput.value = '';
        chatInput.disabled = true;
        sendBtn.disabled = true;
        const tempFiles = [...selectedFiles];
        clearAttachments();

        // Add user message to UI immediately (optimistic)
        addMessageToUI('human', text);

        // Add a "Thinking..." placeholder
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message ai thinking';
        thinkingDiv.innerHTML = `
            <div class="message-inner">
                <div class="msg-avatar">
                    <i data-lucide="bot"></i>
                </div>
                <div class="msg-content">Thinking...</div>
            </div>
        `;
        messagesContainer.appendChild(thinkingDiv);
        if (window.lucide) lucide.createIcons();
        scrollToBottom();

        const formData = new FormData();
        formData.append('message', text);
        if (currentThreadId) formData.append('thread_id', currentThreadId);
        tempFiles.forEach(file => formData.append('files', file));

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            messagesContainer.removeChild(thinkingDiv);
            currentThreadId = data.thread_id;
            addMessageToUI('ai', data.response);
            loadSessions();
        } catch (error) {
            console.error('Error sending message:', error);
            messagesContainer.removeChild(thinkingDiv);
            alert('Error communicating with server.');
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
            updateSendButtonState();
        }
    }

    // --- UI Helpers ---

    function scrollToBottom() {
        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    function updateSendButtonState() {
        sendBtn.disabled = !chatInput.value.trim() && selectedFiles.length === 0;
    }

    function clearAttachments() {
        selectedFiles = [];
        attachmentPreview.innerHTML = '';
    }

    // --- Event Listeners ---

    chatInput.addEventListener('input', () => {
        updateSendButtonState();
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    newChatBtn.addEventListener('click', resetChat);

    attachBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        files.forEach(file => {
            selectedFiles.push(file);
            const reader = new FileReader();
            reader.onload = (ev) => {
                const div = document.createElement('div');
                div.className = 'preview-item';
                div.innerHTML = `
                    <img src="${file.type.startsWith('image/') ? ev.target.result : 'https://cdn-icons-png.flaticon.com/512/1250/1250461.png'}" />
                    <div class="remove-file">&times;</div>
                `;
                div.querySelector('.remove-file').onclick = () => {
                    selectedFiles = selectedFiles.filter(f => f !== file);
                    div.remove();
                    updateSendButtonState();
                };
                attachmentPreview.appendChild(div);
            };
            reader.readAsDataURL(file);
        });
        updateSendButtonState();
        fileInput.value = ''; // Reset for same file selection
    });

    // Initial Load
    loadSessions();
});
