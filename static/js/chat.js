// NeuroFinance GPT - AI Assistant Chat Handlers

async function handleChatSubmit(e) {
    if (e) e.preventDefault();

    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    if (!question) return;

    // Append User Message Bubble
    appendChatMessage(question, 'user');
    input.value = '';

    // Show Typing Indicator
    const typingId = appendTypingIndicator();

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                tx_context: activeTransactionContext
            })
        });

        removeTypingIndicator(typingId);
        const json = await res.json();

        if (json.status === 'success') {
            appendChatMessage(json.data.reply, 'ai');
        } else {
            appendChatMessage(`Error: ${json.message}`, 'ai');
        }
    } catch (err) {
        removeTypingIndicator(typingId);
        appendChatMessage("Sorry, I am temporarily unable to connect to the GPT engine.", 'ai');
    }
}

function sendQuickChat(promptText) {
    document.getElementById('chat-input').value = promptText;
    handleChatSubmit();
}

function askGPTAboutCurrentTx() {
    navigateTo('chat');
    if (activeTransactionContext) {
        sendQuickChat(`Why was transaction ${activeTransactionContext.transaction_id} classified as ${activeTransactionContext.risk_level}?`);
    } else {
        sendQuickChat('Why was this transaction flagged?');
    }
}

function appendChatMessage(text, sender) {
    const box = document.getElementById('chat-messages-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message-bubble ${sender === 'user' ? 'message-user' : 'message-ai'}`;
    
    // Support simple line breaks
    msgDiv.innerHTML = text.replace(/\n/g, '<br>');
    box.appendChild(msgDiv);
    
    // Auto-scroll to bottom
    box.scrollTop = box.scrollHeight;
}

function appendTypingIndicator() {
    const box = document.getElementById('chat-messages-box');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message-bubble message-ai';
    div.innerHTML = '<em>NeuroFinance GPT is thinking...</em>';
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}
