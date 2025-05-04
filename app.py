# app.py

from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import argparse
from chatbot_factory import ChatbotFactory
from utils.file_manager import create_static_files

app = Flask(__name__, static_folder='static')

# تنظیمات پایه
DB_DIRECTORY = "knowledge_base"
COLLECTION_NAME = "website_data"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# متغیرهای سراسری
chatbot = None
chat_histories = {}

def initialize_chatbot(chatbot_type="online"):
    """راه‌اندازی چت‌بات با نوع مشخص شده"""
    global chatbot

    try:
        chatbot = ChatbotFactory.create_chatbot(
            chatbot_type=chatbot_type,
            db_directory=DB_DIRECTORY,
            collection_name=COLLECTION_NAME,
            api_key=OPENAI_API_KEY
        )
        print(f"چت‌بات با موفقیت در حالت {chatbot_type} راه‌اندازی شد.")
        return True
    except Exception as e:
        print(f"خطا در راه‌اندازی چت‌بات: {e}")
        return False

@app.route('/')
def index():
    """نمایش صفحه اصلی"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """پردازش درخواست‌های چت"""
    if not chatbot:
        return jsonify({"error": "چت‌بات راه‌اندازی نشده است"}), 500

    data = request.json
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({"error": "پیام کاربر خالی است"}), 400

    # مدیریت تاریخچه چت
    if session_id not in chat_histories:
        chat_histories[session_id] = []

    try:
        # دریافت پاسخ از چت‌بات
        answer, relevant_context = chatbot.answer_question(
            user_message,
            chat_history=chat_histories[session_id]
        )

        # به‌روزرسانی تاریخچه
        chat_histories[session_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer}
        ])

        # محدود کردن تاریخچه
        if len(chat_histories[session_id]) > 10:
            chat_histories[session_id] = chat_histories[session_id][-10:]

        # استخراج منابع
        sources = extract_sources(relevant_context)

        return jsonify({
            "answer": answer,
            "sources": sources
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    """بازنشانی تاریخچه چت"""
    session_id = request.json.get('session_id', 'default')
    chat_histories[session_id] = []
    return jsonify({"status": "success"})

@app.route('/templates/<path:path>')
def send_template(path):
    """ارسال فایل‌های قالب"""
    return send_from_directory('templates', path)

def extract_sources(context):
    """استخراج منابع از متن بافت"""
    sources = []
    if context and "منبع" in context:
        sections = context.split("=== منبع")
        for section in sections[1:]:
            try:
                title_end = section.find("===")
                if title_end != -1:
                    title = section[:title_end].strip()
                    url_start = section.find("URL:") + 4
                    url_end = section.find("\n", url_start)
                    if url_start != -1 and url_end != -1:
                        url = section[url_start:url_end].strip()
                        sources.append({"title": title, "url": url})
            except:
                continue
    return sources

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='سرور چت‌بات')
    parser.add_argument('--type', choices=['local', 'online'], default='online',
                       help='نوع چت‌بات (local یا online)')
    parser.add_argument('--port', type=int, default=5000,
                       help='پورت سرور')
    args = parser.parse_args()

    # ایجاد ساختار فایل‌ها
    create_static_files()

    # راه‌اندازی چت‌بات
    if initialize_chatbot(args.type):
        # اجرای سرور
        app.run(debug=True, host='0.0.0.0', port=args.port)