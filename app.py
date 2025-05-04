# app.py

from flask import Flask, request, jsonify, render_template
import os
from chatbot_rag import RAGChatbot

app = Flask(__name__, static_folder='static')

# تنظیمات
DB_DIRECTORY = "knowledge_base"
COLLECTION_NAME = "website_data"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL_NAME = "gpt-3.5-turbo"

# ایجاد نمونه چت‌بات
try:
    chatbot = RAGChatbot(
        db_directory=DB_DIRECTORY,
        collection_name=COLLECTION_NAME,
        api_key=OPENAI_API_KEY,
        model_name=MODEL_NAME
    )
    print("چت‌بات با موفقیت راه‌اندازی شد.")
except Exception as e:
    print(f"خطا در راه‌اندازی چت‌بات: {e}")
    chatbot = None

# تاریخچه چت برای هر نشست
chat_histories = {}

@app.route('/')
def index():
    """صفحه اصلی"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API پاسخگویی به پرسش‌های کاربر"""

    if not chatbot:
        return jsonify({"error": "چت‌بات راه‌اندازی نشده است"}), 500

    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({"error": "پیام کاربر خالی است"}), 400

    # دریافت تاریخچه چت برای این نشست
    if session_id not in chat_histories:
        chat_histories[session_id] = []

    # پاسخ به پرسش
    try:
        answer, relevant_context = chatbot.answer_question(
            user_message,
            chat_history=chat_histories[session_id]
        )

        # به‌روزرسانی تاریخچه چت
        chat_histories[session_id].append({"role": "user", "content": user_message})
        chat_histories[session_id].append({"role": "assistant", "content": answer})

        # محدود کردن طول تاریخچه چت
        if len(chat_histories[session_id]) > 10:
            chat_histories[session_id] = chat_histories[session_id][-10:]

        # آماده‌سازی منابع برای نمایش
        sources = []
        if relevant_context and "منبع" in relevant_context:
            sections = relevant_context.split("=== منبع")
            for section in sections[1:]:  # اولین بخش قبل از "منبع 1" است
                try:
                    title_end = section.find("===")
                    if title_end != -1:
                        title = section[:title_end].strip()

                        url_start = section.find("URL:") + 4
                        url_end = section.find("\n", url_start)
                        if url_start != -1 and url_end != -1:
                            url = section[url_start:url_end].strip()

                            sources.append({
                                "title": title,
                                "url": url
                            })
                except:
                    continue

        return jsonify({
            "answer": answer,
            "sources": sources
        })

    except Exception as e:
        return jsonify({"error": f"خطا در پاسخگویی: {str(e)}"}), 500

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    """بازنشانی تاریخچه چت"""

    data = request.json
    session_id = data.get('session_id', 'default')

    if session_id in chat_histories:
        chat_histories[session_id] = []

    return jsonify({"status": "تاریخچه چت بازنشانی شد"})

# اضافه کردن پوشه ساختاری HTML
@app.route('/templates/<path:path>')
def send_template(path):
    return send_from_directory('templates', path)

if __name__ == '__main__':
    # ایجاد پوشه‌های مورد نیاز
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    # ایجاد فایل HTML اصلی اگر وجود ندارد
    index_html_path = 'templates/index.html'
    if not os.path.exists(index_html_path):
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write('''<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>چت‌بات هوشمند</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
    <style>
        body {
            font-family: Tahoma, Arial, sans-serif;
            background-color: #f5f5f5;
        }
        .chat-container {
            max-width: 800px;
            margin: 50px auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .chat-header {
            background: #007bff;
            color: white;
            padding: 15px;
            text-align: center;
        }
        .chat-messages {
            padding: 20px;
            height: 400px;
            overflow-y: auto;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 5px;
            max-width: 80%;
        }
        .user-message {
            background: #e6f2ff;
            margin-left: auto;
        }
        .bot-message {
            background: #f1f1f1;
            margin-right: auto;
        }
        .message-input {
            padding: 15px;
            border-top: 1px solid #ddd;
            display: flex;
        }
        .message-input input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-left: 10px;
        }
        .message-input button {
            padding: 10px 15px;
        }
        .sources {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }
        .sources a {
            color: #007bff;
            text-decoration: none;
        }
        .sources a:hover {
            text-decoration: underline;
        }
        .loading {
            text-align: center;
            color: #666;
            padding: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="chat-container">
            <div class="chat-header">
                <h2>چت‌بات هوشمند</h2>
            </div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot-message">
                    سلام! چطور می‌توانم کمکتان کنم؟
                </div>
            </div>
            <div class="message-input">
                <input type="text" id="userInput" placeholder="پیام خود را بنویسید..." class="form-control">
                <button class="btn btn-primary" id="sendBtn">ارسال</button>
                <button class="btn btn-secondary ms-2" id="resetBtn">شروع مجدد</button>
            </div>
        </div>
    </div>

    <script>
        // تنظیم ID نشست منحصربفرد
        const sessionId = Date.now().toString();
        const chatMessages = document.getElementById('chatMessages');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const resetBtn = document.getElementById('resetBtn');

        // ارسال پیام کاربر
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;

            // نمایش پیام کاربر
            addMessage(message, 'user');
            userInput.value = '';

            // نمایش وضعیت بارگذاری
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = 'در حال تایپ...';
            chatMessages.appendChild(loadingDiv);

            try {
                // ارسال پیام به سرور
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

                // حذف وضعیت بارگذاری
                chatMessages.removeChild(loadingDiv);

                if (data.error) {
                    addMessage('خطا: ' + data.error, 'bot');
                } else {
                    // نمایش پاسخ چت‌بات
                    addMessage(data.answer, 'bot', data.sources);
                }
            } catch (error) {
                // حذف وضعیت بارگذاری
                chatMessages.removeChild(loadingDiv);
                addMessage('خطا در برقراری ارتباط با سرور', 'bot');
            }
        }

        // افزودن پیام به چت
        function addMessage(text, sender, sources = []) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = text;

            // افزودن منابع
            if (sources && sources.length > 0) {
                const sourcesDiv = document.createElement('div');
                sourcesDiv.className = 'sources';
                sourcesDiv.innerHTML = '<strong>منابع:</strong> ';

                sources.forEach((source, index) => {
                    const sourceLink = document.createElement('a');
                    sourceLink.href = source.url;
                    sourceLink.textContent = source.title || `منبع ${index + 1}`;
                    sourceLink.target = '_blank';

                    sourcesDiv.appendChild(sourceLink);

                    if (index < sources.length - 1) {
                        sourcesDiv.appendChild(document.createTextNode(' | '));
                    }
                });

                messageDiv.appendChild(sourcesDiv);
            }

            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // بازنشانی چت
        async function resetChat() {
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

                // پاک کردن تاریخچه چت
                chatMessages.innerHTML = '';
                addMessage('سلام! چطور می‌توانم کمکتان کنم؟', 'bot');

            } catch (error) {
                console.error('خطا در بازنشانی چت:', error);
            }
        }

        // رویدادها
        sendBtn.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', event => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
        resetBtn.addEventListener('click', resetChat);
    </script>
</body>
</html>''')

    # ایجاد فایل CSS اصلی
    css_path = 'static/style.css'
    if not os.path.exists(css_path):
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write('''body {
    font-family: Tahoma, Arial, sans-serif;
    direction: rtl;
    background-color: #f5f5f5;
}''')

    # اجرای سرور
    app.run(debug=True, host='0.0.0.0', port=5000)