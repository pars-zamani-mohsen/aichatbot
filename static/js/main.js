
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendMessage');
    const resetButton = document.getElementById('resetChat');
    const sourcesList = document.getElementById('sourcesList');

    let sessionId = Date.now().toString();

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function updateSources(sources) {
        sourcesList.innerHTML = '';
        sources.forEach(source => {
            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = source.url;
            a.textContent = source.title;
            a.target = '_blank';
            li.appendChild(a);
            sourcesList.appendChild(li);
        });
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        userInput.value = '';
        userInput.style.height = 'auto';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            const data = await response.json();

            if (data.error) {
                addMessage('خطا: ' + data.error);
            } else {
                addMessage(data.answer);
                updateSources(data.sources);
            }
        } catch (error) {
            addMessage('خطا در ارتباط با سرور');
        }
    }

    async function resetChat() {
        sessionId = Date.now().toString();
        chatMessages.innerHTML = '';
        sourcesList.innerHTML = '';

        try {
            await fetch('/api/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });
        } catch (error) {
            addMessage('خطا در بازنشانی گفتگو');
        }
    }

    // Event Listeners
    sendButton.addEventListener('click', sendMessage);

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    resetButton.addEventListener('click', resetChat);
});
