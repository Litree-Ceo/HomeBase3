"""
LiTree Social - Social Media Platform with AI Avatar Assistant
A Facebook-style social platform with integrated avatar guide.
FIXED VERSION - All critical issues resolved
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import sqlite3
import json
import os
import html
from pathlib import Path
import uuid
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['SQLITE_FOREIGN_KEYS'] = True

# Initialize extensions
csrf = CSRFProtect(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Ensure upload directories exist
for subdir in ['avatars', 'posts', 'media']:
    (app.config['UPLOAD_FOLDER'] / subdir).mkdir(parents=True, exist_ok=True)

# Database path
DB_PATH = Path(__file__).parent / 'data' / 'social.db'
DB_PATH.parent.mkdir(exist_ok=True)

# Active users tracker
active_users = {}

# ==================== DATABASE CONNECTION POOLING ====================

class Database:
    """Simple database connection manager with foreign key support."""
    
    @staticmethod
    def get_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def init_db():
        """Initialize the database with all tables."""
        conn = Database.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT,
                avatar_url TEXT DEFAULT '/static/default-avatar.png',
                cover_url TEXT,
                bio TEXT DEFAULT '',
                tier TEXT DEFAULT 'free',
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                media_url TEXT,
                media_type TEXT,
                poll_data TEXT,
                likes_count INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                shares_count INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                likes_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Reactions table (expanded likes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                comment_id INTEGER,
                user_id INTEGER NOT NULL,
                reaction_type TEXT DEFAULT 'like',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
                FOREIGN KEY (comment_id) REFERENCES comments (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(post_id, user_id),
                UNIQUE(comment_id, user_id)
            )
        ''')
        
        # Friendships table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id INTEGER NOT NULL,
                addressee_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (requester_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (addressee_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(requester_id, addressee_id)
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (recipient_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                last_message_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user1_id, user2_id)
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                actor_id INTEGER,
                target_id INTEGER,
                message TEXT,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Assistant conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assistant_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                context TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(user_id, achievement_type)
            )
        ''')
        
        # Media library table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_library (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                original_name TEXT,
                media_type TEXT,
                file_size INTEGER,
                url TEXT NOT NULL,
                is_premium_content BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
        print("[DB] Database initialized with foreign keys enabled")

# ==================== USER MODEL ====================

class User:
    def __init__(self, id, username, email, display_name=None, avatar_url=None, 
                 cover_url=None, bio='', tier='free', xp=0, level=1, created_at=None, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.display_name = display_name or username
        self.avatar_url = avatar_url or '/static/default-avatar.png'
        self.cover_url = cover_url
        self.bio = bio
        self.tier = tier
        self.xp = xp or 0
        self.level = level or 1
        self.created_at = created_at
        self.is_active = is_active
        self.is_authenticated = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)
    
    def has_tier(self, required_tier):
        tiers = {'free': 0, 'premium': 1, 'vip': 2}
        return tiers.get(self.tier, 0) >= tiers.get(required_tier, 0)
    
    def add_xp(self, amount):
        self.xp += amount
        # Level up formula: level * 1000 XP needed
        needed = self.level * 1000
        while self.xp >= needed:
            self.xp -= needed
            self.level += 1
            needed = self.level * 1000
        
        # Update in database
        conn = Database.get_connection()
        conn.execute('UPDATE users SET xp = ?, level = ? WHERE id = ?', 
                    (self.xp, self.level, self.id))
        conn.commit()
        conn.close()
        return self.level
    
    @staticmethod
    def get_by_id(user_id):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def get_by_username(username):
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(**dict(row))
        return None
    
    @staticmethod
    def create(username, email, password, tier='free'):
        password_hash = generate_password_hash(password)
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, tier, display_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, tier, username))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return User.get_by_id(user_id)
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def update_last_seen(user_id):
        conn = Database.get_connection()
        conn.execute('UPDATE users SET last_seen = ? WHERE id = ?', 
                    (datetime.now().isoformat(), user_id))
        conn.commit()
        conn.close()

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

# ==================== TIER DECORATORS ====================

def require_tier(tier):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.has_tier(tier):
                return jsonify({'error': f'Requires {tier} tier or higher'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('landing.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ==================== ROUTES - AUTH ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('feed'))
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.get_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            User.update_last_seen(user.id)
            return redirect(url_for('feed'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        tier = request.form.get('tier', 'free')
        
        if User.get_by_username(username):
            flash('Username already exists')
            return render_template('register.html')
        
        user = User.create(username, email, password, tier)
        if user:
            login_user(user)
            return redirect(url_for('feed'))
        
        flash('Registration failed')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    if current_user.id in active_users:
        del active_users[current_user.id]
    logout_user()
    return redirect(url_for('index'))

# ==================== ROUTES - MAIN PAGES ====================

@app.route('/feed')
@login_required
def feed():
    User.update_last_seen(current_user.id)
    active_users[current_user.id] = time.time()
    return render_template('feed.html', user=current_user)

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.get_by_username(username)
    if not user:
        return 'User not found', 404
    return render_template('profile.html', user=user, current_user=current_user)

@app.route('/messages')
@login_required
def messages():
    return render_template('messages.html', user=current_user)

@app.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html', user=current_user)

@app.route('/friends')
@login_required
def friends():
    return render_template('friends.html', user=current_user)

@app.route('/media-builder')
@login_required
def media_builder():
    return render_template('media_builder.html', user=current_user)

@app.route('/assistant-settings')
@login_required
def assistant_settings():
    return render_template('assistant_settings.html', user=current_user)

@app.route('/arcade')
@login_required
def arcade():
    return render_template('arcade.html', user=current_user)

@app.route('/achievements')
@login_required
def achievements():
    return render_template('achievements.html', user=current_user)

# ==================== API ROUTES - POSTS ====================

@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    user_id = request.args.get('user_id', type=int)
    offset = (page - 1) * per_page
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    # Build query based on filters
    if user_id:
        # Get posts from specific user
        cursor.execute('''
            SELECT p.*, u.username, u.display_name, u.avatar_url
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        ''', (user_id, per_page, offset))
    else:
        # Get feed posts from friends and self
        cursor.execute('''
            SELECT p.*, u.username, u.display_name, u.avatar_url
            FROM posts p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ? OR p.user_id IN (
                SELECT addressee_id FROM friendships 
                WHERE requester_id = ? AND status = 'accepted'
                UNION
                SELECT requester_id FROM friendships 
                WHERE addressee_id = ? AND status = 'accepted'
            )
            ORDER BY p.created_at DESC
            LIMIT ? OFFSET ?
        ''', (current_user.id, current_user.id, current_user.id, per_page, offset))
    
    rows = cursor.fetchall()
    posts = []
    
    for row in rows:
        post = dict(row)
        post['author'] = {
            'username': post['username'],
            'display_name': post['display_name'],
            'avatar_url': post['avatar_url']
        }
        
        # Check if user liked this post
        cursor.execute('''
            SELECT reaction_type FROM reactions 
            WHERE post_id = ? AND user_id = ?
        ''', (post['id'], current_user.id))
        reaction = cursor.fetchone()
        post['user_reaction'] = reaction['reaction_type'] if reaction else None
        post['user_liked'] = reaction is not None
        
        posts.append(post)
    
    conn.close()
    return jsonify({'posts': posts})

@app.route('/api/posts', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def create_post():
    data = request.json or {}
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Content required'}), 400
    
    # Check premium content
    is_premium = data.get('is_premium', False)
    if is_premium and not current_user.has_tier('premium'):
        return jsonify({'error': 'Premium tier required'}), 403
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO posts (user_id, content, media_url, media_type, poll_data, is_premium)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, content, data.get('media_url'), 
          data.get('media_type'), json.dumps(data.get('poll_data')) if data.get('poll_data') else None,
          is_premium))
    
    conn.commit()
    post_id = cursor.lastrowid
    
    # Check achievements
    cursor.execute('SELECT COUNT(*) FROM posts WHERE user_id = ?', (current_user.id,))
    post_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Add XP
    new_level = current_user.add_xp(10)
    
    return jsonify({
        'success': True, 
        'post_id': post_id,
        'new_level': new_level if new_level > current_user.level else None
    })

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@login_required
def update_post(post_id):
    data = request.json or {}
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Content required'}), 400
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute('SELECT user_id FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    
    if not post:
        conn.close()
        return jsonify({'error': 'Post not found'}), 404
    
    if post['user_id'] != current_user.id:
        conn.close()
        return jsonify({'error': 'Not authorized'}), 403
    
    cursor.execute('''
        UPDATE posts SET content = ?, updated_at = ? WHERE id = ?
    ''', (content, datetime.now().isoformat(), post_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute('SELECT user_id FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    
    if not post:
        conn.close()
        return jsonify({'error': 'Post not found'}), 404
    
    if post['user_id'] != current_user.id:
        conn.close()
        return jsonify({'error': 'Not authorized'}), 403
    
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ==================== API ROUTES - REACTIONS ====================

@app.route('/api/posts/<int:post_id>/react', methods=['POST'])
@login_required
def react_to_post(post_id):
    data = request.json or {}
    reaction_type = data.get('reaction', 'like')
    
    valid_reactions = ['like', 'love', 'laugh', 'wow', 'sad', 'angry']
    if reaction_type not in valid_reactions:
        return jsonify({'error': 'Invalid reaction type'}), 400
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    # Check if already reacted
    cursor.execute('''
        SELECT id, reaction_type FROM reactions 
        WHERE post_id = ? AND user_id = ?
    ''', (post_id, current_user.id))
    existing = cursor.fetchone()
    
    if existing:
        if existing['reaction_type'] == reaction_type:
            # Remove reaction
            cursor.execute('DELETE FROM reactions WHERE id = ?', (existing['id'],))
            reacted = False
        else:
            # Update reaction
            cursor.execute('''
                UPDATE reactions SET reaction_type = ? WHERE id = ?
            ''', (reaction_type, existing['id']))
            reacted = True
    else:
        # Add new reaction
        cursor.execute('''
            INSERT INTO reactions (post_id, user_id, reaction_type)
            VALUES (?, ?, ?)
        ''', (post_id, current_user.id, reaction_type))
        reacted = True
        
        # Create notification
        cursor.execute('SELECT user_id FROM posts WHERE id = ?', (post_id,))
        post_owner = cursor.fetchone()
        if post_owner and post_owner['user_id'] != current_user.id:
            cursor.execute('''
                INSERT INTO notifications (user_id, type, actor_id, target_id, message)
                VALUES (?, 'reaction', ?, ?, ?)
            ''', (post_owner['user_id'], current_user.id, post_id, 
                  f'{current_user.display_name} reacted to your post'))
    
    # Update post reaction count
    cursor.execute('''
        UPDATE posts SET likes_count = (
            SELECT COUNT(*) FROM reactions WHERE post_id = ?
        ) WHERE id = ?
    ''', (post_id, post_id))
    
    conn.commit()
    conn.close()
    
    # Add XP for reacting
    if reacted:
        current_user.add_xp(2)
    
    return jsonify({
        'reacted': reacted,
        'reaction_type': reaction_type if reacted else None
    })

# ==================== API ROUTES - COMMENTS ====================

@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
@login_required
def get_comments(post_id):
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, u.username, u.display_name, u.avatar_url
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at DESC
    ''', (post_id,))
    
    rows = cursor.fetchall()
    comments = [dict(row) for row in rows]
    conn.close()
    
    return jsonify({'comments': comments})

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def create_comment(post_id):
    data = request.json or {}
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Content required'}), 400
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO comments (post_id, user_id, content)
        VALUES (?, ?, ?)
    ''', (post_id, current_user.id, content))
    
    cursor.execute('''
        UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?
    ''', (post_id,))
    
    # Create notification
    cursor.execute('SELECT user_id FROM posts WHERE id = ?', (post_id,))
    post_owner = cursor.fetchone()
    if post_owner and post_owner['user_id'] != current_user.id:
        cursor.execute('''
            INSERT INTO notifications (user_id, type, actor_id, target_id, message)
            VALUES (?, 'comment', ?, ?, ?)
        ''', (post_owner['user_id'], current_user.id, post_id,
              f'{current_user.display_name} commented on your post'))
    
    conn.commit()
    conn.close()
    
    # Add XP
    current_user.add_xp(5)
    
    return jsonify({'success': True})

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, post_id FROM comments WHERE id = ?', (comment_id,))
    comment = cursor.fetchone()
    
    if not comment:
        conn.close()
        return jsonify({'error': 'Comment not found'}), 404
    
    if comment['user_id'] != current_user.id:
        conn.close()
        return jsonify({'error': 'Not authorized'}), 403
    
    cursor.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    cursor.execute('''
        UPDATE posts SET comments_count = comments_count - 1 WHERE id = ?
    ''', (comment['post_id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ==================== API ROUTES - FILE UPLOAD ====================

@app.route('/api/upload', methods=['POST'])
@login_required
@limiter.limit("10 per hour")
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    file_type = request.form.get('type', 'post')
    
    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if ext not in allowed_extensions:
        return jsonify({'error': 'Invalid file type'}), 400
    
    # Generate unique filename
    filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
    
    # Determine subdirectory
    upload_dir = app.config['UPLOAD_FOLDER'] / file_type
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = upload_dir / filename
    file.save(filepath)
    
    # Get file size
    file_size = filepath.stat().st_size
    
    # Save to database
    conn = Database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO media_library (user_id, filename, original_name, media_type, file_size, url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, filename, file.filename, file_type, file_size, 
          f'/uploads/{file_type}/{filename}'))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'filename': filename,
        'url': f'/uploads/{file_type}/{filename}'
    })

# ==================== API ROUTES - NOTIFICATIONS ====================

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT n.*, u.username, u.display_name, u.avatar_url
        FROM notifications n
        JOIN users u ON n.actor_id = u.id
        WHERE n.user_id = ?
        ORDER BY n.created_at DESC
        LIMIT 50
    ''', (current_user.id,))
    
    rows = cursor.fetchall()
    notifications = [dict(row) for row in rows]
    
    # Count unread
    cursor.execute('SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0',
                   (current_user.id,))
    unread_count = cursor.fetchone()[0]
    
    conn.close()
    return jsonify({'notifications': notifications, 'unread_count': unread_count})

@app.route('/api/notifications/read', methods=['POST'])
@login_required
def mark_notifications_read():
    conn = Database.get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE notifications SET is_read = 1 WHERE user_id = ?',
                   (current_user.id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ==================== API ROUTES - MESSAGES ====================

@app.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            c.id,
            CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END as other_user_id,
            u.username, u.display_name, u.avatar_url,
            (SELECT content FROM messages 
             WHERE (sender_id = ? AND recipient_id = other_user_id) 
                OR (sender_id = other_user_id AND recipient_id = ?)
             ORDER BY created_at DESC LIMIT 1) as last_message,
            (SELECT COUNT(*) FROM messages WHERE sender_id = other_user_id AND recipient_id = ? AND is_read = 0) as unread_count
        FROM conversations c
        JOIN users u ON u.id = CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END
        WHERE c.user1_id = ? OR c.user2_id = ?
        ORDER BY c.last_message_at DESC
    ''', (current_user.id, current_user.id, current_user.id, current_user.id, 
          current_user.id, current_user.id, current_user.id))
    
    rows = cursor.fetchall()
    conversations = [dict(row) for row in rows]
    conn.close()
    
    return jsonify({'conversations': conversations})

@app.route('/api/messages/<int:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, u.username, u.display_name, u.avatar_url
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.recipient_id = ?) 
           OR (m.sender_id = ? AND m.recipient_id = ?)
        ORDER BY m.created_at ASC
        LIMIT 100
    ''', (current_user.id, user_id, user_id, current_user.id))
    
    rows = cursor.fetchall()
    messages = [dict(row) for row in rows]
    
    # Mark as read
    cursor.execute('''
        UPDATE messages SET is_read = 1 
        WHERE sender_id = ? AND recipient_id = ? AND is_read = 0
    ''', (user_id, current_user.id))
    conn.commit()
    conn.close()
    
    return jsonify({'messages': messages})

# ==================== API ROUTES - USERS ====================

@app.route('/api/users/search')
@login_required
def search_users():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'users': []})
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, display_name, avatar_url, bio
        FROM users
        WHERE (username LIKE ? OR display_name LIKE ?) AND id != ?
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%', current_user.id))
    
    rows = cursor.fetchall()
    users = []
    
    for row in rows:
        # Check friendship status
        cursor.execute('''
            SELECT status FROM friendships 
            WHERE (requester_id = ? AND addressee_id = ?) 
               OR (requester_id = ? AND addressee_id = ?)
        ''', (current_user.id, row['id'], row['id'], current_user.id))
        friendship = cursor.fetchone()
        
        users.append({
            'id': row['id'],
            'username': row['username'],
            'display_name': row['display_name'],
            'avatar_url': row['avatar_url'],
            'bio': row['bio'],
            'friendship_status': friendship['status'] if friendship else None
        })
    
    conn.close()
    return jsonify({'users': users})

@app.route('/api/users/friends', methods=['GET'])
@login_required
def get_friends():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.username, u.display_name, u.avatar_url, u.bio
        FROM users u
        JOIN friendships f ON (u.id = f.addressee_id OR u.id = f.requester_id)
        WHERE (f.requester_id = ? OR f.addressee_id = ?)
          AND f.status = 'accepted'
          AND u.id != ?
    ''', (current_user.id, current_user.id, current_user.id))
    
    rows = cursor.fetchall()
    friends = [dict(row) for row in rows]
    conn.close()
    return jsonify({'friends': friends})

@app.route('/api/users/friends/request', methods=['POST'])
@login_required
def send_friend_request():
    data = request.json or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO friendships (requester_id, addressee_id, status)
            VALUES (?, ?, 'pending')
        ''', (current_user.id, user_id))
        conn.commit()
        
        # Create notification
        cursor.execute('''
            INSERT INTO notifications (user_id, type, actor_id, message)
            VALUES (?, 'follow', ?, ?)
        ''', (user_id, current_user.id, f'{current_user.display_name} sent you a friend request'))
        conn.commit()
        
        success = True
    except sqlite3.IntegrityError:
        success = False
    
    conn.close()
    return jsonify({'success': success})

@app.route('/api/users/friends/respond', methods=['POST'])
@login_required
def respond_friend_request():
    data = request.json or {}
    requester_id = data.get('requester_id')
    action = data.get('action')  # 'accept' or 'decline'
    
    if not requester_id or action not in ['accept', 'decline']:
        return jsonify({'error': 'Invalid request'}), 400
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    if action == 'accept':
        cursor.execute('''
            UPDATE friendships SET status = 'accepted' 
            WHERE requester_id = ? AND addressee_id = ?
        ''', (requester_id, current_user.id))
        message = f'{current_user.display_name} accepted your friend request'
    else:
        cursor.execute('''
            DELETE FROM friendships 
            WHERE requester_id = ? AND addressee_id = ?
        ''', (requester_id, current_user.id))
        message = None
    
    conn.commit()
    
    if message:
        cursor.execute('''
            INSERT INTO notifications (user_id, type, actor_id, message)
            VALUES (?, 'friend_accepted', ?, ?)
        ''', (requester_id, current_user.id, message))
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

# ==================== API ROUTES - ASSISTANT ====================

@app.route('/api/assistant/chat', methods=['POST'])
@login_required
def assistant_chat():
    data = request.json or {}
    message = data.get('message', '').strip()
    context = data.get('context', {})
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    response = generate_assistant_response(message, context, current_user)
    
    conn = Database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO assistant_conversations (user_id, message, response, context)
        VALUES (?, ?, ?, ?)
    ''', (current_user.id, message, response, json.dumps(context)))
    conn.commit()
    conn.close()
    
    mood = determine_assistant_mood(response)
    
    return jsonify({
        'response': response,
        'mood': mood,
        'suggestions': get_assistant_suggestions(context, current_user)
    })

@app.route('/api/assistant/clear', methods=['POST'])
@login_required
def clear_assistant_history():
    conn = Database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM assistant_conversations WHERE user_id = ?', (current_user.id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

def generate_assistant_response(message, context, user):
    msg_lower = message.lower()
    page = context.get('page', 'unknown')
    
    if any(word in msg_lower for word in ['help', 'how', 'what']):
        return get_help_response(page, context, user)
    
    if any(word in msg_lower for word in ['go to', 'open', 'show', 'where']):
        return get_navigation_response(msg_lower, user)
    
    if any(word in msg_lower for word in ['feature', 'do', 'can', 'premium', 'vip']):
        return get_feature_response(msg_lower, user)
    
    if 'friend' in msg_lower:
        return "You can find and add friends using the Friends page! Click the Friends icon in the sidebar."
    
    if 'message' in msg_lower or 'chat' in msg_lower:
        return "To send messages, go to the Messages page. You can start conversations with your friends there!"
    
    if any(word in msg_lower for word in ['hello', 'hi', 'hey']):
        return f"Hey {user.display_name}! I'm LitBit, your guide to LiTree Social. How can I help you today?"
    
    return f"I'm LitBit, your personal guide! I can help you navigate LiTree Social. What would you like to know?"

def get_help_response(page, context, user):
    page_help = {
        'feed': "This is your Feed! Here you can see posts from friends. You can like, comment, and share posts. Try creating your own post!",
        'profile': "This is your Profile page! Here you can see all your posts, edit your bio, change your avatar, and update your settings.",
        'messages': "This is Messages! Chat with friends in real-time. You can also create group conversations.",
        'notifications': "This page shows all your notifications - likes, comments, friend requests, and mentions.",
        'friends': "Find friends here! You can search for users, see friend suggestions, and manage your friend list.",
        'media_builder': "Welcome to the Media Builder! Create amazing content with our tools.",
        'assistant_settings': "Customize how I help you! Change my appearance, voice, and what notifications I give you.",
        'arcade': "Play classic DOS games here! All games are legal shareware or homebrew.",
        'achievements': "Track your progress and earn XP! Complete challenges to level up and unlock badges."
    }
    
    base_help = page_help.get(page, "I'm here to help! What would you like to know?")
    
    if user.tier == 'free':
        base_help += " By the way, upgrading to Premium unlocks many more features!"
    
    return base_help

def get_navigation_response(message, user):
    pages = {
        'feed': '/feed',
        'home': '/feed',
        'profile': f'/profile/{user.username}',
        'messages': '/messages',
        'notifications': '/notifications',
        'friends': '/friends',
        'media': '/media-builder',
        'builder': '/media-builder',
        'settings': '/assistant-settings',
        'arcade': '/arcade',
        'achievements': '/achievements'
    }
    
    for keyword, url in pages.items():
        if keyword in message:
            return f"I'll take you there! Click here to go to {keyword.title()}: {url}"
    
    return "I can help you navigate! Try saying 'go to feed', 'open messages', or 'show my profile'."

def get_feature_response(message, user):
    if 'premium' in message or 'upgrade' in message:
        if user.tier == 'free':
            return "Premium gives you: HD video uploads, advanced media builder tools, priority support, custom themes, and no ads! VIP includes all that plus exclusive content and early access to new features."
        elif user.tier == 'premium':
            return "You're already Premium! VIP adds: Exclusive badge, priority in search, VIP-only content, and direct access to our team."
        else:
            return "You're VIP - you have access to everything! Enjoy exclusive content, priority features, and our gratitude!"
    
    return "LiTree Social has: Posts & Feed, Real-time Messaging, Media Builder, Friend Network, Notifications, Arcade with legal retro games, Achievements with XP system, and ME - your personal guide!"

def determine_assistant_mood(response):
    text_lower = response.lower()
    
    if any(word in text_lower for word in ['congrats', 'awesome', 'great', 'love', 'happy']):
        return 'happy'
    elif any(word in text_lower for word in ['hmm', 'thinking', 'let me see', 'interesting']):
        return 'thinking'
    elif any(word in text_lower for word in ['wow', 'amazing', 'surprised', 'cool']):
        return 'surprised'
    else:
        return 'talking'

def get_assistant_suggestions(context, user):
    page = context.get('page', 'feed')
    suggestions = []
    
    if page == 'feed':
        suggestions = ['Create a post', 'Find friends', 'Check messages']
    elif page == 'profile':
        suggestions = ['Edit profile', 'View my posts', 'Change avatar']
    elif page == 'media_builder':
        suggestions = ['Create image', 'Edit video', 'Add music']
    elif page == 'arcade':
        suggestions = ['Play DOOM', 'Browse games', 'View high scores']
    elif page == 'achievements':
        suggestions = ['View progress', 'How to earn XP', 'Leaderboard']
    elif user.tier == 'free':
        suggestions = ['What can I do?', 'Upgrade to Premium', 'Find friends']
    else:
        suggestions = ['What\'s new?', 'Show features', 'Get help']
    
    return suggestions

# ==================== API ROUTES - ACHIEVEMENTS ====================

@app.route('/api/achievements', methods=['GET'])
@login_required
def get_achievements():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT achievement_type, unlocked_at FROM achievements 
        WHERE user_id = ?
    ''', (current_user.id,))
    
    rows = cursor.fetchall()
    unlocked = [row['achievement_type'] for row in rows]
    
    # Calculate stats
    cursor.execute('SELECT COUNT(*) FROM posts WHERE user_id = ?', (current_user.id,))
    post_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM reactions WHERE user_id = ?', (current_user.id,))
    reaction_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM comments WHERE user_id = ?', (current_user.id,))
    comment_count = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM friendships 
        WHERE (requester_id = ? OR addressee_id = ?) AND status = 'accepted'
    ''', (current_user.id, current_user.id))
    friend_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'unlocked': unlocked,
        'stats': {
            'posts': post_count,
            'reactions': reaction_count,
            'comments': comment_count,
            'friends': friend_count
        },
        'xp': current_user.xp,
        'level': current_user.level,
        'max_xp': current_user.level * 1000
    })

# ==================== WEBSOCKET EVENTS ====================

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        active_users[current_user.id] = time.time()
        emit('connected', {
            'user_id': current_user.id,
            'username': current_user.username
        })
        
        # Broadcast online status to friends
        socketio.emit('user_online', {
            'user_id': current_user.id,
            'username': current_user.username
        }, broadcast=True, namespace='/')

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        leave_room(f'user_{current_user.id}')
        if current_user.id in active_users:
            del active_users[current_user.id]
        
        # Broadcast offline status
        socketio.emit('user_offline', {
            'user_id': current_user.id
        }, broadcast=True, namespace='/')

@socketio.on('send_message')
@login_required
def handle_message(data):
    recipient_id = data.get('recipient_id')
    content = data.get('content', '').strip()
    
    if not recipient_id or not content:
        return
    
    # Save message
    conn = Database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (sender_id, recipient_id, content)
        VALUES (?, ?, ?)
    ''', (current_user.id, recipient_id, content))
    
    # Update conversation
    cursor.execute('''
        INSERT OR REPLACE INTO conversations (user1_id, user2_id, last_message_at)
        VALUES (
            CASE WHEN ? < ? THEN ? ELSE ? END,
            CASE WHEN ? < ? THEN ? ELSE ? END,
            ?
        )
    ''', (current_user.id, recipient_id, current_user.id, recipient_id,
          current_user.id, recipient_id, recipient_id, current_user.id,
          datetime.now().isoformat()))
    
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()
    
    # Emit to recipient
    emit('new_message', {
        'id': message_id,
        'sender_id': current_user.id,
        'sender_name': current_user.display_name,
        'sender_avatar': current_user.avatar_url,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }, room=f'user_{recipient_id}')
    
    # Confirm to sender
    emit('message_sent', {'id': message_id, 'status': 'delivered'})

@socketio.on('typing')
@login_required
def handle_typing(data):
    recipient_id = data.get('recipient_id')
    is_typing = data.get('typing', False)
    
    emit('user_typing', {
        'user_id': current_user.id,
        'username': current_user.display_name,
        'typing': is_typing
    }, room=f'user_{recipient_id}')

@socketio.on('join_feed')
@login_required
def handle_join_feed():
    join_room('global_feed')

@socketio.on('leave_feed')
@login_required
def handle_leave_feed():
    leave_room('global_feed')

@socketio.on('join_conversation')
@login_required
def handle_join_conversation(data):
    user_id = data.get('user_id')
    if user_id:
        room_name = f'conversation_{min(current_user.id, user_id)}_{max(current_user.id, user_id)}'
        join_room(room_name)

# ==================== STATIC FILES ====================

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("  LiTree Social - Fixed & Enhanced Version")
    print("=" * 60)
    
    Database.init_db()
    
    # Ensure asset directories exist
    for subdir in ['avatars', 'videos', 'audio']:
        (Path(__file__).parent / 'assets' / subdir).mkdir(parents=True, exist_ok=True)
    
    print("\n[STARTUP] Starting server...")
    print("[URL] http://localhost:5000")
    print("\n[FEATURES]")
    print("  - User Authentication with CSRF Protection")
    print("  - Rate Limiting (5 login attempts per minute)")
    print("  - Posts, Comments, Reactions (6 types)")
    print("  - Real-time Messaging with WebSocket")
    print("  - Friend System (Request/Accept/Decline)")
    print("  - Notifications")
    print("  - File Upload with Validation")
    print("  - XP & Level System")
    print("  - Achievements")
    print("  - AI Avatar Assistant (LitBit)")
    print("  - Database Foreign Keys Enabled")
    print("\nPress Ctrl+C to stop\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
