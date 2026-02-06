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
    const knowledgeBtn = document.getElementById('knowledge-btn');
    const knowledgeModal = document.getElementById('knowledge-modal');
    const closeModal = document.getElementById('close-modal');
    const kbUploadZone = document.getElementById('kb-upload-zone');
    const kbFileInput = document.getElementById('kb-file-input');
    const kbStatusList = document.getElementById('kb-status-list');
    const kbProgressContainer = document.getElementById('kb-progress-container');
    const kbProgressBar = document.getElementById('kb-progress-bar');

    let currentThreadId = null;
    let selectedFiles = [];
    let isRecording = false;

    // --- Knowledge Base Logic ---
    // --- Knowledge Base Logic ---
    knowledgeBtn.onclick = () => {
        knowledgeModal.style.display = 'block';
        loadKbFiles();
    };
    closeModal.onclick = () => knowledgeModal.style.display = 'none';
    window.onclick = (e) => { if (e.target === knowledgeModal) knowledgeModal.style.display = 'none'; };

    kbUploadZone.onclick = () => kbFileInput.click();
    kbFileInput.onchange = () => handleKbUpload(kbFileInput.files);

    async function loadKbFiles() {
        kbStatusList.innerHTML = '<div class="kb-status-item">Loading files...</div>';
        try {
            const response = await fetch('/knowledge/list');
            const data = await response.json();
            kbStatusList.innerHTML = '';

            if (data.files.length === 0) {
                kbStatusList.innerHTML = '<div style="text-align:center; color:var(--text-secondary); padding:1rem;">No files in knowledge base.</div>';
                return;
            }

            data.files.forEach(filename => {
                const item = document.createElement('div');
                item.className = 'kb-status-item';
                item.style.justifyContent = 'space-between';
                item.innerHTML = `
                    <div style="display:flex; align-items:center; gap:10px;">
                        <i data-lucide="file-text" style="width:16px; height:16px; color:var(--text-secondary);"></i>
                        <span>${filename}</span>
                    </div>
                `;

                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'delete-btn';
                deleteBtn.innerHTML = '<i data-lucide="trash-2"></i>';
                deleteBtn.onclick = () => deleteKbFile(filename);

                item.appendChild(deleteBtn);
                kbStatusList.appendChild(item);
            });
            lucide.createIcons();
        } catch (error) {
            kbStatusList.innerHTML = '<div class="kb-status-item" style="color: var(--error)">Failed to load files.</div>';
        }
    }

    async function deleteKbFile(filename) {
        if (!confirm(`Delete ${filename} from knowledge base?`)) return;
        try {
            const response = await fetch(`/knowledge/${encodeURIComponent(filename)}`, { method: 'DELETE' });
            if (response.ok) {
                loadKbFiles();
            } else {
                alert('Failed to delete file');
            }
        } catch (error) {
            console.error('Error deleting file:', error);
        }
    }

    async function handleKbUpload(files) {
        if (!files.length) return;
        kbStatusList.innerHTML = '';
        kbProgressContainer.style.display = 'block';
        kbProgressBar.style.width = '0%';

        const formData = new FormData();
        Array.from(files).forEach(file => formData.append('files', file));

        try {
            const data = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/knowledge/upload', true);

                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable) {
                        const percent = (e.loaded / e.total) * 100;
                        kbProgressBar.style.width = percent + '%';
                    }
                };

                xhr.onload = () => {
                    if (xhr.status === 200) resolve(JSON.parse(xhr.responseText));
                    else reject('Upload failed');
                };

                xhr.onerror = () => reject('Network error');
                xhr.send(formData);
            });

            setTimeout(() => {
                kbProgressContainer.style.display = 'none';
                kbProgressBar.style.width = '0%';
                loadKbFiles(); // Refresh list instead of just showing results
            }, 1000);

        } catch (error) {
            console.error(error);
            kbStatusList.innerHTML = '<div class="kb-status-item" style="color: var(--error)">Upload failed.</div>';
            kbProgressContainer.style.display = 'none';
        }
    }

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

            const delBtn = item.querySelector('.delete-btn');
            delBtn.onclick = (e) => {
                e.stopPropagation();
                deleteSession(session.thread_id);
            };

            item.onclick = () => switchSession(session.thread_id);
            historyList.appendChild(item);
        });
        lucide.createIcons();
    }

    async function switchSession(threadId) {
        currentThreadId = threadId;
        welcomeScreen.style.display = 'none';
        messagesContainer.innerHTML = '<div class="agent-thought" style="margin: 2rem;"><i data-lucide="loader"></i><span>Resuming thread...</span></div>';

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
            messagesContainer.innerHTML = '<div class="agent-thought" style="color: var(--error)">Failed to load conversation.</div>';
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
        chatInput.value = '';
        chatInput.style.height = 'auto';
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

        // Helper function to escape HTML in code
        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        let htmlContent = '';
        if (role === 'human') {
            const text = typeof content === 'string' ? content : (content.message || JSON.stringify(content));
            htmlContent = `<div class="msg-content">${parseMarkdown(text)}</div>`;
        } else {
            // Build implementation details for inside the thought bubble
            const researchHtml = (content.research_output || content.research) ? `
                <div class="agent-step">
                    <div class="step-header"><i data-lucide="search"></i> Research Data</div>
                    <div class="step-body">${parseMarkdown(content.research_output || content.research)}</div>
                </div>` : '';

            const planHtml = content.plan ? `
                <div class="agent-step">
                    <div class="step-header"><i data-lucide="map"></i> Strategic Plan</div>
                    <div class="step-body">${parseMarkdown(content.plan)}</div>
                </div>` : '';

            const codeHtml = content.code ? `
                <div class="agent-step">
                    <div class="step-header"><i data-lucide="terminal"></i> Implementation</div>
                    <div class="step-body"><pre><code>${escapeHtml(content.code)}</code></pre></div>
                </div>` : '';

            const hasProcess = researchHtml || planHtml || codeHtml;

            // Thought bubble with nested implementation details
            const thoughtHtml = content.thought ? `
                <div class="agent-thought ${hasProcess ? 'has-process' : ''}" onclick="this.classList.toggle('expanded')">
                    <div class="thought-bar">
                        <i data-lucide="brain"></i>
                        <span class="thought-summary">${content.thought}</span>
                        ${hasProcess ? '<i data-lucide="chevron-down" class="chevron"></i>' : ''}
                    </div>
                    ${hasProcess ? `<div class="thought-details">${researchHtml}${planHtml}${codeHtml}</div>` : ''}
                </div>` : '';

            // Main response
            const responseHtml = content.final_response || content.response ? `
                <div class="msg-content">${parseMarkdown(content.final_response || content.response)}</div>` : '';

            htmlContent = `
                <div class="msg-inner-container">
                    ${thoughtHtml}
                    ${responseHtml}
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-inner">
                <div class="msg-avatar shadow-lg">
                    <i data-lucide="${role === 'human' ? 'user' : 'zap'}"></i>
                </div>
                <div class="msg-content-wrapper" style="flex:1">
                    ${htmlContent}
                </div>
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
        chatInput.style.height = 'auto';
        chatInput.disabled = true;
        sendBtn.disabled = true;
        const tempFiles = [...selectedFiles];
        clearAttachments();

        addMessageToUI('human', text);

        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message ai';
        thinkingDiv.innerHTML = `
            <div class="message-inner">
                <div class="msg-avatar"><i data-lucide="zap"></i></div>
                <div class="msg-content-wrapper" style="flex:1">
                    <div class="agent-thought">
                        <i data-lucide="loader" class="spin"></i>
                        <span>Aura is orchestrating agents...</span>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.appendChild(thinkingDiv);
        lucide.createIcons();
        scrollToBottom();

        const formData = new FormData();
        formData.append('message', text);
        formData.append('model', model);
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

            const updateAiMessage = (newContent) => {
                // Build implementation details for inside the thought bubble
                const researchHtml = newContent.research ? `<div class="agent-step"><div class="step-header"><i data-lucide="search"></i> Research Data</div><div class="step-body">${parseMarkdown(newContent.research)}</div></div>` : '';
                const planHtml = newContent.plan ? `<div class="agent-step"><div class="step-header"><i data-lucide="map"></i> Strategic Plan</div><div class="step-body">${parseMarkdown(newContent.plan)}</div></div>` : '';
                const codeHtml = newContent.code ? `<div class="agent-step"><div class="step-header"><i data-lucide="terminal"></i> Implementation</div><div class="step-body"><pre><code>${escapeHtml(newContent.code)}</code></pre></div></div>` : '';

                const hasProcess = researchHtml || planHtml || codeHtml;

                // Thought bubble with nested implementation details
                const thoughtHtml = newContent.thought ? `
                    <div class="agent-thought ${hasProcess ? 'has-process' : ''}" onclick="this.classList.toggle('expanded')">
                        <div class="thought-bar">
                            <i data-lucide="brain"></i>
                            <span class="thought-summary">${newContent.thought}</span>
                            ${hasProcess ? '<i data-lucide="chevron-down" class="chevron"></i>' : ''}
                        </div>
                        ${hasProcess ? `<div class="thought-details">${researchHtml}${planHtml}${codeHtml}</div>` : ''}
                    </div>` : '';

                // Main response text
                const responseHtml = newContent.response ? `<div class="msg-content">${parseMarkdown(newContent.response)}</div>` : '';

                thinkingDiv.querySelector('.msg-content-wrapper').innerHTML = `
                    <div class="msg-inner-container">
                        ${thoughtHtml}
                        ${responseHtml}
                    </div>
                `;
                lucide.createIcons();
                scrollToBottom();
            };

            // Helper function to escape HTML in code
            function escapeHtml(text) {
                if (!text) return '';
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.thread_id) currentThreadId = data.thread_id;

                            if (data.update) {
                                // Update only the fields that are provided (non-empty)
                                if (data.update.thought) aiContent.thought = data.update.thought;
                                if (data.update.research_output) aiContent.research = data.update.research_output;
                                if (data.update.plan) aiContent.plan = data.update.plan;
                                if (data.update.code) aiContent.code = data.update.code;
                                if (data.update.final_response) aiContent.response = data.update.final_response;
                                updateAiMessage(aiContent);
                            }

                            if (data.final) {
                                // Final state - use these values as the definitive answer
                                updateAiMessage({
                                    thought: data.final.thought || aiContent.thought,
                                    response: data.final.final_response || data.final.response || aiContent.response,
                                    research: data.final.research_output || data.final.research || aiContent.research,
                                    plan: data.final.plan || aiContent.plan,
                                    code: data.final.code || aiContent.code
                                });
                            }
                        } catch (parseError) {
                            // Skip malformed JSON chunks (can happen with partial SSE data)
                            console.warn('Skipping malformed SSE chunk:', line);
                        }
                    }
                }
            }
            loadSessions();
        } catch (error) {
            console.error('Error:', error);
            thinkingDiv.querySelector('.msg-content-wrapper').innerHTML = '<div class="agent-thought" style="color: var(--error)">Error communicating with Aura.</div>';
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
            updateSendButtonState();
        }
    }

    // --- Voice Logic ---
    function startVoiceInput() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Voice recognition not supported.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.onstart = () => { isRecording = true; voiceBtn.classList.add('recording'); };
        recognition.onresult = (e) => { chatInput.value = e.results[0][0].transcript; updateSendButtonState(); };
        recognition.onend = () => { isRecording = false; voiceBtn.classList.remove('recording'); };
        recognition.start();
    }

    // --- Listeners ---
    menuToggle.onclick = () => sidebar.classList.toggle('open');
    voiceBtn.onclick = startVoiceInput;
    chatInput.oninput = () => {
        updateSendButtonState();
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight) + 'px';
    };
    chatInput.onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };
    sendBtn.onclick = sendMessage;
    newChatBtn.onclick = resetChat;
    attachBtn.onclick = () => fileInput.click();

    fileInput.onchange = (e) => {
        Array.from(e.target.files).forEach(file => {
            selectedFiles.push(file);
            const reader = new FileReader();
            reader.onload = (ev) => {
                const div = document.createElement('div');
                div.className = 'preview-item shadow-lg';
                div.innerHTML = `
                    <img src="${file.type.startsWith('image/') ? ev.target.result : 'https://cdn-icons-png.flaticon.com/512/1250/1250461.png'}" />
                    <div class="remove-file" style="position:absolute; top:-5px; right:-5px; background:var(--error); border-radius:50%; width:20px; height:20px; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:12px; border:2px solid var(--bg-dark)">&times;</div>
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
        chatViewport.scrollTo({ top: chatViewport.scrollHeight, behavior: 'smooth' });
    }

    loadSessions();
});
