const API_URL = '/api/v1';
let currentConversationId = null;
let currentUser = null;
let pollInterval = null;

async function login() {
    const displayNameInput = document.getElementById('login-display-name').value.trim();

    if (!displayNameInput) {
        alert('Por favor, insira seu nome.');
        return;
    }

    const payload = { display_name: displayNameInput };

    try {
        const response = await fetch(`${API_URL}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('app-container').style.display = 'flex';
            document.getElementById('user-info').innerText = `Logado como: ${currentUser.display_name} (${currentUser.id})`;
            loadUserConversations();
        } else {
            alert('Erro no login: ' + await response.text());
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conectar com o servidor.');
    }
}

function toggleGroupTitle() {
    const type = document.getElementById('new-conv-type').value;
    const titleInput = document.getElementById('new-group-title');
    if (type === 'GROUP') {
        titleInput.style.display = 'inline-block';
    } else {
        titleInput.style.display = 'none';
    }
}

async function loadUserConversations() {
    if (!currentUser) return;
    try {
        const response = await fetch(`${API_URL}/conversations/user/${currentUser.id}`);
        const conversations = await response.json();
        const list = document.getElementById('conversation-list');
        list.innerHTML = '';
        
        conversations.forEach(conv => {
            const div = document.createElement('div');
            div.style.padding = '10px';
            div.style.cursor = 'pointer';
            div.style.borderBottom = '1px solid #eee';
            
            let displayName = conv.id.substring(0, 8) + '...';
            
            if (conv.type === 'GROUP') {
                displayName = (conv.metadata && conv.metadata.title) ? conv.metadata.title : 'Grupo sem nome';
            } else if (conv.type === 'PRIVATE') {
                // Find the other participant's name
                if (conv.participant_names && conv.participant_names.length > 0) {
                    const otherNames = conv.participant_names.filter(name => name !== currentUser.display_name);
                    if (otherNames.length > 0) {
                        displayName = otherNames[0];
                    } else {
                        displayName = currentUser.display_name; // Chat with self?
                    }
                }
            }

            div.innerText = displayName;
            div.onclick = () => loadConversation(conv.id, displayName);
            list.appendChild(div);
        });
    } catch (error) {
        console.error('Erro ao carregar conversas:', error);
    }
}

async function createConversation() {
    const participantsStr = document.getElementById('new-conv-participants').value;
    const type = document.getElementById('new-conv-type').value;
    const groupTitle = document.getElementById('new-group-title').value;
    
    // Split by comma and trim whitespace
    let participantNames = participantsStr.split(',').map(name => name.trim()).filter(name => name);

    if (!currentUser) return;

    // Ensure current user is in participants (by name)
    if (!participantNames.includes(currentUser.display_name)) {
        participantNames.push(currentUser.display_name);
    }

    const payload = { 
        type, 
        participant_names: participantNames,
        participants: [], // Send empty list of IDs
        metadata: {}
    };

    if (type === 'GROUP' && groupTitle) {
        payload.metadata.title = groupTitle;
    }

    try {
        const response = await fetch(`${API_URL}/conversations/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (response.ok) {
            alert(`Conversa criada!`);
            loadUserConversations();
            // Determine display name for immediate load
            let displayName = data.id;
            if (type === 'GROUP' && groupTitle) displayName = groupTitle;
            // For private, we'd need to know the other person, but let's just reload list
            loadConversation(data.id, displayName);
        } else {
            alert('Erro ao criar conversa: ' + JSON.stringify(data));
        }
    } catch (error) {
        console.error('Erro:', error);
    }
}

function loadConversation(conversationId, title) {
    if (!conversationId) return;
    currentConversationId = conversationId;
    document.getElementById('chat-title').innerText = title || `Conversa: ${conversationId}`;
    document.getElementById('messages').innerHTML = '';
    
    if (pollInterval) clearInterval(pollInterval);
    fetchMessages();
    pollInterval = setInterval(fetchMessages, 2000); // Poll every 2 seconds
}

async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file || !currentUser || !currentConversationId) return;

    try {
        // 1. Get Upload URL
        const uploadReq = {
            filename: file.name,
            mime_type: file.type || 'application/octet-stream',
            size: file.size,
            uploader_id: currentUser.id,
            conversation_id: currentConversationId
        };

        const urlRes = await fetch(`${API_URL}/files/upload-url`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(uploadReq)
        });

        if (!urlRes.ok) throw new Error('Falha ao obter URL de upload');
        const uploadData = await urlRes.json();

        // 2. Upload File to MinIO/S3 (using the presigned URL)
        // Note: In a real scenario with MinIO presigned PUT, we send the file directly.
        // However, the backend implementation of generate_upload_url might return a URL that expects a PUT.
        // Let's assume standard PUT to presigned URL.
        
        const uploadRes = await fetch(uploadData.upload_url, {
            method: 'PUT',
            body: file
        });

        if (!uploadRes.ok) throw new Error('Falha ao fazer upload do arquivo');

        // 3. Send Message with Attachment
        const msgPayload = {
            conversation_id: currentConversationId,
            sender_id: currentUser.id,
            type: 'FILE',
            content: file.name, // Or empty
            attachments: [{
                file_id: uploadData.file_id,
                url: uploadData.public_url, // Or internal URL
                mime_type: file.type,
                size: file.size,
                filename: file.name
            }]
        };

        const msgRes = await fetch(`${API_URL}/messages/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(msgPayload)
        });

        if (msgRes.ok) {
            fileInput.value = ''; // Clear input
            fetchMessages();
        } else {
            alert('Erro ao enviar mensagem com arquivo');
        }

    } catch (error) {
        console.error('Erro no upload:', error);
        alert('Erro ao enviar arquivo: ' + error.message);
    }
}

async function fetchMessages() {
    if (!currentConversationId) return;
    try {
        const response = await fetch(`${API_URL}/conversations/${currentConversationId}/messages?limit=50`);
        const messages = await response.json();
        renderMessages(messages);
    } catch (error) {
        console.error('Erro ao buscar mensagens:', error);
    }
}

function renderMessages(messages) {
    const container = document.getElementById('messages');
    container.innerHTML = '';
    // Sort by timestamp
    messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    messages.forEach(msg => {
        const div = document.createElement('div');
        const isMe = msg.sender_id === currentUser.id;
        div.className = `message ${isMe ? 'sent' : 'received'}`;
        
        let statusIcon = '';
        if (msg.status === 'PENDING') statusIcon = '🕒';
        else if (msg.status === 'SENT') statusIcon = '✓';
        else if (msg.status === 'DELIVERED') statusIcon = '✓✓';
        else if (msg.status === 'READ') statusIcon = '👁️';
        else if (msg.status === 'FAILED') statusIcon = '❌';

        div.innerHTML = `
            <div style="font-size: 0.7em; color: #aaa; margin-bottom: 2px;">${msg.sender_id.substring(0,8)}</div>
            <div>${msg.content || ''}</div>
            ${msg.attachments && msg.attachments.length > 0 ? 
                msg.attachments.map(att => `<div><a href="${att.url}" target="_blank">📎 ${att.filename}</a></div>`).join('') 
                : ''}
            <div class="status">${statusIcon} ${msg.status}</div>
        `;
        container.appendChild(div);
    });
    container.scrollTop = container.scrollHeight;
}

async function sendMessage() {
    const content = document.getElementById('message-input').value;

    if (!content || !currentUser || !currentConversationId) {
        alert('Preencha a mensagem.');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/messages/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: currentConversationId,
                sender_id: currentUser.id,
                content: content,
                type: 'TEXT'
            })
        });
        
        if (response.ok) {
            document.getElementById('message-input').value = '';
            fetchMessages();
        } else {
            alert('Erro ao enviar mensagem');
        }
    } catch (error) {
        console.error('Erro:', error);
    }
}
