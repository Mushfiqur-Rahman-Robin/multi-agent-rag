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
    const modelSelect = document.getElementById('model-select');
    const voiceBtn = document.getElementById('voice-btn');
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');

    let currentThreadId = null;
    let selectedFiles = [];
    let isRecording = false;

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
                <div class="title">${session.title || 'Untitled Thread'}</div>
                <div class="actions">
                    <button class="delete-btn" title="Delete thread">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            `;

            // Fix Delete Button: Event Delegation / Immediate attachment
            const delBtn = item.querySelector('.delete-btn');
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteSession(session.thread_id);
            });

            item.addEventListener('click', () => switchSession(session.thread_id));
            historyList.appendChild(item);
        });
        lucide.createIcons();
    }

    async function switchSession(threadId) {
        currentThreadId = threadId;
        welcomeScreen.style.display = 'none';
        messagesContainer.innerHTML = '<div class="loading">Resuming thread...</div>';

        try {
            const response = await fetch(`/sessions/${threadId}`);
            const messages = await response.json();
            messagesContainer.innerHTML = '';
            messages.forEach(msg => {
                let content = msg.content;
                if (typeof content === 'string') {
                    try { content = JSON.parse(content); } catch (e) { }
                }
                addMessageToUI(msg.role === 'human' ? 'human' : 'ai', content);
            });
            scrollToBottom();
            loadSessions();
        } catch (error) {
            console.error('Error switching session:', error);
            messagesContainer.innerHTML = '<div class="error">Failed to load conversation.</div>';
        }
    }

    async function deleteSession(threadId) {
        if (!confirm('Permanently delete this thread?')) return;
        try {
            const res = await fetch(`/sessions/${threadId}`, { method: 'DELETE' });
            if (res.ok) {
                if (currentThreadId === threadId) resetChat();
                loadSessions();
            }
        } catch (error) {
            console.error('Error deleting session:', error);
        }
    }

    function resetChat() {
        currentThreadId = null;
        messagesContainer.innerHTML = '';
        welcomeScreen.style.display = 'block';
        loadSessions();
    }

    // --- UI Helpers ---

    function parseMarkdown(text) {
        if (!text) return '';
        try {
            return marked.parse(String(text));
        } catch (e) {
            return text;
        }
    }

    function addMessageToUI(role, content) {
        welcomeScreen.style.display = 'none';

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        let htmlContent = '';
        if (role === 'human') {
            const text = typeof content === 'string' ? content : (content.message || JSON.stringify(content));
            htmlContent = `<div class="msg-content">${parseMarkdown(text)}</div>`;
        } else {
            const thoughtHtml = content.thought ? `
                <div class="agent-thought">
                    <i data-lucide="brain"></i>
                    <span>${content.thought}</span>
                </div>` : '';

            const responseHtml = content.response ? `
                <div class="final-response">${parseMarkdown(content.response)}</div>` : '';

            const researchHtml = content.research ? `
                <div class="agent-step">
                    <div class="step-header"><i data-lucide="search"></i> Research Data</div>
                    <div class="step-body">${parseMarkdown(content.research)}</div>
                </div>` : '';

            const planHtml = content.plan ? `
                <div class="agent-step">
                    <div class="step-header"><i data-lucide="map"></i> Strategic Roadmap</div>
                    <div class="step-body">${parseMarkdown(content.plan)}</div>
                </div>` : '';

            const codeHtml = content.code ? `
                <div class="agent-step">
                    <div class="step-header"><i data-lucide="terminal"></i> Implementation Output</div>
                    <div class="step-body"><pre><code>${content.code}</code></pre></div>
                </div>` : '';

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
                    <i data-lucide="${role === 'human' ? 'user' : 'zap'}"></i>
                </div>
                ${htmlContent}
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        lucide.createIcons();
        scrollToBottom();
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        const model = modelSelect.value;
        if (!text && selectedFiles.length === 0) return;

        chatInput.value = '';
        chatInput.disabled = true;
        sendBtn.disabled = true;
        const tempFiles = [...selectedFiles];
        clearAttachments();

        addMessageToUI('human', text);

        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message ai thinking';
        thinkingDiv.innerHTML = `
            <div class="message-inner">
                <div class="msg-avatar"><i data-lucide="zap"></i></div>
                <div class="msg-content">
                    <div class="agent-thought"><i data-lucide="loader"></i> Aura is orchestrating agents...</div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(thinkingDiv);
        lucide.createIcons();
        scrollToBottom();

        const formData = new FormData();
        formData.append('message', text);
        formData.append('model', model); // Pass selected model
        if (currentThreadId) formData.append('thread_id', currentThreadId);
        tempFiles.forEach(file => formData.append('files', file));

        try {
            const response = await fetch('/chat/stream', {
                method: 'POST',
                body: formData
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiContent = { thought: '', response: '', research: '', plan: '', code: '' };

            // Logic to update the UI message live
            const updateAiMessage = (newContent) => {
                const thoughtHtml = newContent.thought ? `<div class="agent-thought"><i data-lucide="brain"></i><span>${newContent.thought}</span></div>` : '';
                const responseHtml = newContent.response ? `<div class="final-response">${parseMarkdown(newContent.response)}</div>` : '';
                const researchHtml = newContent.research ? `<div class="agent-step"><div class="step-header"><i data-lucide="search"></i> Research Data</div><div class="step-body">${parseMarkdown(newContent.research)}</div></div>` : '';
                const planHtml = newContent.plan ? `<div class="agent-step"><div class="step-header"><i data-lucide="map"></i> Strategic Roadmap</div><div class="step-body">${parseMarkdown(newContent.plan)}</div></div>` : '';
                const codeHtml = newContent.code ? `<div class="agent-step"><div class="step-header"><i data-lucide="terminal"></i> Implementation Output</div><div class="step-body"><pre><code>${newContent.code}</code></pre></div></div>` : '';

                thinkingDiv.innerHTML = `
                    <div class="message-inner">
                        <div class="msg-avatar"><i data-lucide="zap"></i></div>
                        <div class="msg-content">
                            ${thoughtHtml}
                            ${responseHtml}
                            ${researchHtml}
                            ${planHtml}
                            ${codeHtml}
                        </div>
                    </div>
                `;
                lucide.createIcons();
                scrollToBottom();
            };

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        if (data.thread_id) currentThreadId = data.thread_id;

                        if (data.update) {
                            // Map updates to aiContent
                            if (data.update.thought) aiContent.thought = data.update.thought;
                            if (data.update.research_output) aiContent.research = data.update.research_output;
                            if (data.update.plan) aiContent.plan = data.update.plan;
                            if (data.update.code) aiContent.code = data.update.code;
                            if (data.update.final_response) aiContent.response = data.update.final_response;
                            updateAiMessage(aiContent);
                        }

                        if (data.final) {
                            thinkingDiv.className = 'message ai'; // Remove thinking state
                            updateAiMessage(data.final);
                        }
                    }
                }
            }
            loadSessions();
        } catch (error) {
            console.error('Error:', error);
            messagesContainer.removeChild(thinkingDiv);
            const errorDiv = document.createElement('div');
            errorDiv.className = 'message ai error';
            errorDiv.innerHTML = '<div class="message-inner">Error communicating with Aura.</div>';
            messagesContainer.appendChild(errorDiv);
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
            updateSendButtonState();
        }
    }

    // --- Voice Logic (Web Speech API) ---
    function startVoiceInput() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Voice recognition not supported in this browser.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            voiceBtn.classList.add('recording');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            updateSendButtonState();
        };

        recognition.onerror = () => {
            isRecording = false;
            voiceBtn.classList.remove('recording');
        };

        recognition.onend = () => {
            isRecording = false;
            voiceBtn.classList.remove('recording');
        };

        recognition.start();
    }

    // --- Event Listeners ---

    menuToggle.onclick = () => sidebar.classList.toggle('open');
    voiceBtn.onclick = startVoiceInput;

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

    sendBtn.onclick = sendMessage;
    newChatBtn.onclick = resetChat;
    attachBtn.onclick = () => fileInput.click();

    fileInput.onchange = (e) => {
        Array.from(e.target.files).forEach(file => {
            selectedFiles.push(file);
            const reader = new FileReader();
            reader.onload = (ev) => {
                const div = document.createElement('div');
                div.className = 'preview-item';
                div.innerHTML = `
                    <img src="${file.type.startsWith('image/') ? ev.target.result : 'https://cdn-icons-png.flaticon.com/512/1250/1250461.png'}" />
                    <div class="remove-file" style="position:absolute; top:0; right:0; background:rgba(0,0,0,0.5); border-radius:50%; cursor:pointer;">&times;</div>
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
    };

    function updateSendButtonState() {
        sendBtn.disabled = !chatInput.value.trim() && selectedFiles.length === 0;
    }

    function clearAttachments() {
        selectedFiles = [];
        attachmentPreview.innerHTML = '';
    }

    function scrollToBottom() {
        chatViewport.scrollTop = chatViewport.scrollHeight;
    }

    loadSessions();
});
