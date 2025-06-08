from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
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

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webcrawler.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Store chat histories for different sessions
chat_histories = {}

# Initialize chatbot as None
chatbot = None

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    crawls = db.relationship('Crawl', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Crawl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')
    pages_crawled = db.Column(db.Integer, default=0)
    max_pages = db.Column(db.Integer, default=100)
    max_depth = db.Column(db.Integer, default=3)
    include_links = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def initialize_chatbot(chatbot_type="online", collection_name=COLLECTION_NAME, db_directory=DB_DIRECTORY):
    """Initialize chatbot with specified type"""
    global chatbot
    try:
        if os.path.exists(db_directory):
            full_db_path = db_directory
        else:
            domain = collection_name.replace('_', '.')
            full_db_path = f"processed_data/{domain}/knowledge_base/{domain}"

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/crawl_request', methods=['GET', 'POST'])
@login_required
def crawl_request():
    if request.method == 'POST':
        url = request.form.get('url')
        max_pages = int(request.form.get('max_pages', 100))
        max_depth = int(request.form.get('max_depth', 3))
        include_links = bool(request.form.get('include_links', False))

        crawl = Crawl(
            url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            include_links=include_links,
            user_id=current_user.id
        )
        db.session.add(crawl)
        db.session.commit()

        # TODO: Start crawl process in background
        # This would typically be handled by a background task queue

        flash('Crawl request submitted successfully', 'success')
        return redirect(url_for('manage_crawls'))

    return render_template('crawl_request.html')

@app.route('/manage_crawls')
@login_required
def manage_crawls():
    crawls = Crawl.query.filter_by(user_id=current_user.id).order_by(Crawl.created_at.desc()).all()
    return render_template('manage_crawls.html', crawls=crawls)

@app.route('/view_crawl/<int:crawl_id>')
@login_required
def view_crawl(crawl_id):
    crawl = Crawl.query.get_or_404(crawl_id)
    if crawl.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('manage_crawls'))
    return render_template('view_crawl.html', crawl=crawl)

@app.route('/download_crawl/<int:crawl_id>')
@login_required
def download_crawl(crawl_id):
    crawl = Crawl.query.get_or_404(crawl_id)
    if crawl.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('manage_crawls'))
    
    # TODO: Implement crawl data download
    flash('Download functionality not implemented yet', 'warning')
    return redirect(url_for('manage_crawls'))

@app.route('/delete_crawl/<int:crawl_id>', methods=['POST'])
@login_required
def delete_crawl(crawl_id):
    crawl = Crawl.query.get_or_404(crawl_id)
    if crawl.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('manage_crawls'))
    
    db.session.delete(crawl)
    db.session.commit()
    flash('Crawl deleted successfully', 'success')
    return redirect(url_for('manage_crawls'))

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
    # Create database tables
    with app.app_context():
        db.create_all()

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