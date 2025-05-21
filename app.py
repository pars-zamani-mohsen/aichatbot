from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import argparse
from chatbot_factory import ChatbotFactory
from utils.file_manager import create_static_files
from settings import (
    OPENAI_API_KEY, GOOGLE_API_KEY,
    PORT, HOST, DEBUG,
    DB_DIRECTORY, COLLECTION_NAME,
    MAX_TOKENS, TOKENS_PER_MIN,
    MAX_CHAT_HISTORY
)
from core.scrape_website import scrape_website
from core.process_data import process_website_data
from core.create_embeddings import create_embeddings
from core.create_knowledge_base import create_knowledge_base
import logging
from pathlib import Path

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.route('/api/register', methods=['POST'])
def register_website():
    """ثبت سایت و ساخت پایگاه دانش"""
    try:
        data = request.json
        url = data.get('url')
        max_pages = int(data.get('max_pages', 50))
        collection_name = data.get('collection')
        if not url or not collection_name:
            return jsonify({'error': 'URL and collection are required'}), 400
        base_dir = Path('processed_data') / collection_name
        base_dir.mkdir(parents=True, exist_ok=True)
        if not scrape_website(url, max_pages, base_dir / 'output.json'):
            return jsonify({'error': 'Website crawling failed'}), 500
        if not process_website_data(base_dir / 'output.json', base_dir):
            return jsonify({'error': 'Data processing failed'}), 500
        if not create_embeddings(
            input_file=base_dir / 'processed_data.csv',
            output_dir=base_dir,
            model_name='all-MiniLM-L6-v2',  # یا مقدار داینامیک از ورودی
            chunk_size=1000  # یا مقدار داینامیک از ورودی
        ):
            return jsonify({'error': 'Embedding creation failed'}), 500
        if not create_knowledge_base(
            embeddings_dir=base_dir,
            collection_name=collection_name,
            db_path=base_dir / 'knowledge_base'
        ):
            return jsonify({'error': 'Knowledge base creation failed'}), 500
        if not initialize_chatbot(collection_name=collection_name):
            return jsonify({'error': 'Chatbot initialization failed'}), 500
        return jsonify({
            'status': 'success',
            'message': 'Website registered and knowledge base created successfully',
            'collection': collection_name
        })
    except Exception as e:
        logger.error(f"خطا در ثبت سایت: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        chat_histories[session_id] = chat_histories[session_id][-MAX_CHAT_HISTORY:]

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