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
            div.innerText = `${conv.type} - ${conv.id.substring(0, 8)}...`;
            div.onclick = () => loadConversation(conv.id);
            list.appendChild(div);
        });
    } catch (error) {
        console.error('Erro ao carregar conversas:', error);
    }
}

async function createConversation() {
    const participantsStr = document.getElementById('new-conv-participants').value;
    const type = document.getElementById('new-conv-type').value;
    let participants = participantsStr.split(',').map(id => id.trim()).filter(id => id);

    if (!currentUser) return;

    // Ensure current user is in participants
    if (!participants.includes(currentUser.id)) {
        participants.push(currentUser.id);
    }

    try {
        const response = await fetch(`${API_URL}/conversations/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type, participants })
        });
        const data = await response.json();
        if (response.ok) {
            alert(`Conversa criada! ID: ${data.id}`);
            loadUserConversations();
            loadConversation(data.id);
        } else {
            alert('Erro ao criar conversa: ' + JSON.stringify(data));
        }
    } catch (error) {
        console.error('Erro:', error);
    }
}

function loadConversation(conversationId) {
    if (!conversationId) return;
    currentConversationId = conversationId;
    document.getElementById('chat-title').innerText = `Conversa: ${conversationId}`;
    document.getElementById('messages').innerHTML = '';
    
    if (pollInterval) clearInterval(pollInterval);
    fetchMessages();
    pollInterval = setInterval(fetchMessages, 2000); // Poll every 2 seconds
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
            <div>${msg.content || '[Arquivo]'}</div>
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
                type: 'text'
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
