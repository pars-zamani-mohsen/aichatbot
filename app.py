from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import argparse
from chatbot_factory import ChatbotFactory
from utils.file_manager import create_static_files

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Global variables
COLLECTION_NAME = "website_data"  # Default collection name
DB_DIRECTORY = "knowledge_base"    # Default database directory
MAX_TOKENS = 8000                 # Maximum tokens per request
TOKENS_PER_MIN = 30000           # Rate limit tokens per minute

# Store chat histories for different sessions
chat_histories = {}

# Initialize chatbot as None
chatbot = None

# Load API keys from environment
try:
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
except ImportError:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

def initialize_chatbot(chatbot_type="online"):
    """Initialize chatbot with specified type"""
    global chatbot
    try:
        # Select API key based on chatbot type
        api_key = GOOGLE_API_KEY if chatbot_type == "gemini" else OPENAI_API_KEY

        # Create chatbot instance
        chatbot = ChatbotFactory.create_chatbot(
            chatbot_type=chatbot_type,
            db_directory=DB_DIRECTORY,
            collection_name=COLLECTION_NAME,
            api_key=api_key
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
    parser.add_argument('--port', type=int, default=5000,
                       help='Server port')
    parser.add_argument('--collection', type=str, default='website_data',
                       help='Knowledge base collection name')
    parser.add_argument('--db-dir', type=str, default='knowledge_base',
                       help='Knowledge base directory path')

    args = parser.parse_args()

    # Update global variables
    COLLECTION_NAME = args.collection
    DB_DIRECTORY = args.db_dir

    # Initialize application
    create_static_files()
    if initialize_chatbot(args.type):
        app.run(debug=True, host='0.0.0.0', port=args.port)