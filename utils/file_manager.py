# utils/file_manager.py

import os

def create_static_files():
    """ایجاد فایل‌های استاتیک مورد نیاز"""

    # ایجاد پوشه‌ها
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('utils', exist_ok=True)

    # ایجاد فایل‌های استاتیک
    files = {
        'templates/index.html': get_index_html_content(),
        'static/style.css': get_css_content(),
        'static/js/main.js': get_js_content()
    }

    for file_path, content in files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"فایل {file_path} ایجاد شد.")

def get_index_html_content():
    """محتوای فایل HTML اصلی"""
    return '''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>چت‌بات هوشمند</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <div class="chat-container">
            <div class="chat-header">
                <h1>چت‌بات هوشمند</h1>
                <button id="resetChat" class="reset-button">شروع مجدد گفتگو</button>
            </div>
            <div id="chatMessages" class="chat-messages"></div>
            <div class="chat-input">
                <textarea id="userInput" placeholder="پیام خود را بنویسید..." rows="3"></textarea>
                <button id="sendMessage">ارسال</button>
            </div>
        </div>
        <div id="sources" class="sources-container">
            <h3>منابع:</h3>
            <ul id="sourcesList"></ul>
        </div>
    </div>
    <script src="/static/js/main.js"></script>
</body>
</html>
'''

def get_css_content():
    """محتوای فایل CSS"""
    return '''
:root {
    --primary-color: #2196F3;
    --secondary-color: #E3F2FD;
    --text-color: #333;
    --background-color: #f5f5f5;
    --chat-background: #fff;
    --message-user: #E3F2FD;
    --message-bot: #fff;
}

body {
    font-family: Tahoma, Arial, sans-serif;
    direction: rtl;
    background-color: var(--background-color);
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: 20px;
}

.chat-container {
    background-color: var(--chat-background);
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 20px;
}

.chat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

.chat-header h1 {
    margin: 0;
    font-size: 1.5em;
    color: var(--text-color);
}

.chat-messages {
    height: 60vh;
    overflow-y: auto;
    padding: 10px;
    margin-bottom: 20px;
}

.message {
    margin-bottom: 15px;
    padding: 10px 15px;
    border-radius: 10px;
    max-width: 80%;
}

.user-message {
    background-color: var(--message-user);
    margin-left: auto;
}

.bot-message {
    background-color: var(--message-bot);
    border: 1px solid #eee;
    margin-right: auto;
}

.chat-input {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 10px;
}

textarea {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    resize: none;
    font-family: inherit;
}

button {
    padding: 10px 20px;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #1976D2;
}

.reset-button {
    background-color: #f44336;
}

.reset-button:hover {
    background-color: #d32f2f;
}

.sources-container {
    background-color: var(--chat-background);
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 20px;
}

.sources-container h3 {
    margin-top: 0;
    color: var(--text-color);
}

#sourcesList {
    padding-right: 20px;
}

#sourcesList li {
    margin-bottom: 10px;
}

#sourcesList a {
    color: var(--primary-color);
    text-decoration: none;
}

#sourcesList a:hover {
    text-decoration: underline;
}

@media (max-width: 768px) {
    .container {
        grid-template-columns: 1fr;
    }

    .chat-messages {
        height: 50vh;
    }

    .message {
        max-width: 90%;
    }
}
'''

def get_js_content():
    """محتوای فایل JavaScript"""
    return '''
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
'''