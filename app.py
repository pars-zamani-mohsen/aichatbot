from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import argparse
from chatbot_factory import ChatbotFactory
from utils.file_manager import create_static_files
from settings import (
    OPENAI_API_KEY, GOOGLE_API_KEY,
    PORT, HOST, DEBUG,
    DB_DIRECTORY, COLLECTION_NAME,
    MAX_TOKENS, TOKENS_PER_MIN
)

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Store chat histories for different sessions
chat_histories = {}

# Initialize chatbot as None
chatbot = None

def initialize_chatbot(chatbot_type="online", collection_name=COLLECTION_NAME, db_directory=DB_DIRECTORY):
    """Initialize chatbot with specified type"""
    global chatbot
    try:
        # اگر مسیر کامل دایرکتوری داده شده باشد
        if os.path.exists(db_directory):
            full_db_path = db_directory
        else:
            # ساخت مسیر کامل با توجه به نام کالکشن
            domain = collection_name.replace('_', '.')
            full_db_path = f"processed_data/{domain}/knowledge_base"

        print(f"Using database directory: {full_db_path}")

        chatbot = ChatbotFactory.create_chatbot(
            chatbot_type=chatbot_type,
            db_directory=full_db_path,
            collection_name=collection_name
        )
        print(f"Chatbot initialized successfully in {chatbot_type} mode")
        return True
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
        return False

# Routes
@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    if not chatbot:
        return jsonify({"error": "Chatbot not initialized"}), 500

    # Get request data
    data = request.json
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id', 'default')

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    try:
        # Initialize chat history for new sessions
        if session_id not in chat_histories:
            chat_histories[session_id] = []

        # Get response from chatbot
        answer, context = chatbot.answer_question(
            user_message,
            chat_history=chat_histories[session_id]
        )

        # Update chat history
        chat_histories[session_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer}
        ])

        # Keep only last 10 messages
        chat_histories[session_id] = chat_histories[session_id][-5:]

        # Extract sources from context
        sources = extract_sources(context)

        return jsonify({
            "answer": answer,
            "sources": sources
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_chat():
    """Reset chat history"""
    session_id = request.json.get('session_id', 'default')
    chat_histories[session_id] = []
    return jsonify({"status": "success"})

@app.route('/templates/<path:path>')
def send_template(path):
    """Serve template files"""
    return send_from_directory('templates', path)

def extract_sources(context):
    """Extract sources from context text"""
    sources = []
    if not context or "source" not in context.lower():
        return sources

    try:
        sections = context.split("=== Source")
        for section in sections[1:]:  # Skip first split which is before any source
            title_end = section.find("===")
            if title_end != -1:
                title = section[:title_end].strip()
                url_start = section.find("URL:") + 4
                url_end = section.find("\n", url_start)
                if url_start != -1 and url_end != -1:
                    url = section[url_start:url_end].strip()
                    sources.append({"title": title, "url": url})
    except Exception:
        pass  # Skip problematic sections

    return sources

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Chatbot Server')
    parser.add_argument('--type', choices=['local', 'online', 'gemini'],
                       default='online', help='Chatbot type')
    parser.add_argument('--port', type=int, default=PORT,
                       help='Server port')
    parser.add_argument('--collection', type=str, default=COLLECTION_NAME,
                       help='Knowledge base collection name')
    parser.add_argument('--db-dir', type=str, default=DB_DIRECTORY,
                       help='Knowledge base directory path')

    args = parser.parse_args()

    # Initialize application
    create_static_files()
    if initialize_chatbot(
        chatbot_type=args.type,
        collection_name=args.collection,
        db_directory=args.db_dir
    ):
        app.run(debug=DEBUG, host=HOST, port=args.port)