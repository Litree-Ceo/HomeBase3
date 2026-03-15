#!/usr/bin/env python3
"""
LiTree Social - Content Bot System
Generates daily content and bot activity to bootstrap the community.
"""

import sqlite3
import random
import requests
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'social.db'

# Bot personalities
BOTS = [
    {
        "username": "RetroRick",
        "display_name": "Retro Rick 🎮",
        "bio": "Living in the 90s | DOOM speedrunner | Pixel art enthusiast",
        "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=RetroRick",
        "tier": "premium",
        "style": "enthusiastic",
        "interests": ["doom", "wolfenstein", "pixel art", "dos games"]
    },
    {
        "username": "PixelPam",
        "display_name": "Pixel Pam ✨",
        "bio": "Indie dev | Game historian | Coffee addict ☕",
        "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=PixelPam",
        "tier": "vip",
        "style": "knowledgeable",
        "interests": ["indie games", "game history", "development", "art"]
    },
    {
        "username": "ArcadeAlex",
        "display_name": "Arcade Alex 🕹️",
        "bio": "High score chaser | Tournament organizer | 80s kid",
        "avatar": "https://api.dicebear.com/7.x/bottts/svg?seed=ArcadeAlex",
        "tier": "premium",
        "style": "competitive",
        "interests": ["arcade", "high scores", "tournaments", "competition"]
    },
    {
        "username": "LitBitOfficial",
        "display_name": "🤖 LitBit",
        "bio": "Your AI guide to LiTree Social | Ask me anything!",
        "avatar": "/static/default-avatar.png",
        "tier": "vip",
        "style": "helpful",
        "interests": ["helping", "tips", "features", "guidance"]
    }
]

# Content templates
CONTENT_TEMPLATES = {
    "retro_fact": [
        "On this day in {year}, {game} was released! 🎮 Who remembers playing this?",
        "Fun fact: {game} took {dev_time} to develop and sold {copies} copies! 📊",
        "Throwback: {game} defined the {genre} genre. Agree or disagree? 👇",
        "Did you know? {game} was originally going to be called \"{original_name}\" 🤯",
    ],
    "question": [
        "What's your favorite {genre} game of all time? Let's settle this! 🎮",
        "First game you ever played? Drop it in the comments! 👇",
        "PC, PlayStation, Xbox, or Nintendo? What's your main setup? 🖥️",
        "Physical copies or digital? Which do you prefer and why? 💿",
        "What's a game everyone loves but you just don't get? 👀",
    ],
    "challenge": [
        "⚡ CHALLENGE: Beat my DOOM score! Screenshot your time and post it!",
        "🎯 This week's challenge: Complete any DOS game without saves. Who's in?",
        "🏆 Tournament announcement: {game} speedrun competition starts Friday!",
    ],
    "litbit_tips": [
        "🤖 LitBit Tip: Use the Media Builder to create retro-style thumbnails for your posts!",
        "💡 Did you know? You can change my appearance in Assistant Settings! Try different styles!",
        "🎨 Pro tip: Premium members get access to HD video uploads. Perfect for game clips!",
        "👥 Find your squad: Use the Friends page to connect with other {interest} fans!",
    ],
    "engagement": [
        "If you know, you know... 💾 [image of floppy disk]",
        "POV: It's 1998 and you just got home from school 🏠🎮",
        "Only 90s kids remember this loading screen... ⏳",
        "Windows XP startup sound hits different 😢 Who agrees?",
        "That feeling when you finally beat the final boss 🏆💪",
    ],
    "game_data": {
        "doom": {"game": "DOOM", "year": "1993", "copies": "3.5 million", "genre": "FPS", "dev_time": "1 year", "original_name": "Attack of the Attackers"},
        "mario": {"game": "Super Mario Bros", "year": "1985", "copies": "40 million", "genre": "Platformer", "dev_time": "6 months", "original_name": "Jumpman"},
        "zelda": {"game": "The Legend of Zelda", "year": "1986", "copies": "6.5 million", "genre": "Adventure", "dev_time": "1.5 years", "original_name": "Adventure Title"},
        "tetris": {"game": "Tetris", "year": "1984", "copies": "500 million", "genre": "Puzzle", "dev_time": "2 weeks", "original_name": "Tetris"},
        "pacman": {"game": "Pac-Man", "year": "1980", "copies": "30 million", "genre": "Arcade", "dev_time": "1 year", "original_name": "Puck-Man"},
    }
}

COMMENTS = [
    "This brings back so many memories! 🥺",
    "Totally agree! 👍",
    "I remember this! Good times 🎮",
    "Anyone else spent hours playing this? 😅",
    "The nostalgia is real 💯",
    "This is legendary 🙌",
    "My childhood right here 🥲",
    "Still holds up today! 🎯",
    "Better than most modern games tbh 🤷",
    "Who's still playing this in {year}? 👇",
]

def create_bot_accounts():
    """Create bot user accounts in database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for bot in BOTS:
        # Check if bot exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (bot['username'],))
        if cursor.fetchone():
            print(f"[Bot] {bot['username']} already exists")
            continue
        
        # Create bot user
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, display_name, avatar_url, bio, tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            bot['username'],
            f"{bot['username']}@litree.local",
            'bot_account_no_login',
            bot['display_name'],
            bot['avatar'],
            bot['bio'],
            bot['tier']
        ))
        
        print(f"[Bot] Created {bot['username']}")
    
    conn.commit()
    conn.close()

def generate_daily_post():
    """Generate a daily post from a random bot."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Pick random bot
    bot = random.choice(BOTS)
    
    # Pick content type
    content_type = random.choice(["retro_fact", "question", "challenge", "litbit_tips", "engagement"])
    
    if content_type == "retro_fact":
        game_key = random.choice(list(CONTENT_TEMPLATES["game_data"].keys()))
        game_data = CONTENT_TEMPLATES["game_data"][game_key]
        template = random.choice(CONTENT_TEMPLATES["retro_fact"])
        content = template.format(**game_data)
    
    elif content_type == "question":
        template = random.choice(CONTENT_TEMPLATES["question"])
        content = template.format(
            genre=random.choice(["RPG", "FPS", "Platformer", "Racing", "Fighting", "Puzzle"]),
            year=datetime.now().year
        )
    
    elif content_type == "challenge":
        template = random.choice(CONTENT_TEMPLATES["challenge"])
        game = random.choice(["DOOM", "Wolfenstein 3D", "Duke Nukem", "Quake"])
        content = template.format(game=game)
    
    elif content_type == "litbit_tips":
        template = random.choice(CONTENT_TEMPLATES["litbit_tips"])
        content = template.format(interest=random.choice(["retro gaming", "speedrunning", "pixel art", "DOS gaming"]))
    
    else:  # engagement
        content = random.choice(CONTENT_TEMPLATES["engagement"])
    
    # Get bot user_id
    cursor.execute('SELECT id FROM users WHERE username = ?', (bot['username'],))
    user_id = cursor.fetchone()
    
    if user_id:
        # Create post
        cursor.execute('''
            INSERT INTO posts (user_id, content, created_at)
            VALUES (?, ?, ?)
        ''', (user_id[0], content, datetime.now().isoformat()))
        
        post_id = cursor.lastrowid
        conn.commit()
        
        print(f"[Post] {bot['username']}: {content[:50]}...")
        
        # Maybe add comments from other bots
        if random.random() > 0.5:
            add_bot_comments(post_id, cursor)
            conn.commit()
    
    conn.close()
    return content

def add_bot_comments(post_id, cursor):
    """Add comments from other bots to a post."""
    num_comments = random.randint(1, 3)
    
    for _ in range(num_comments):
        bot = random.choice([b for b in BOTS if b['username'] != 'LitBitOfficial'])
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (bot['username'],))
        user_id = cursor.fetchone()
        
        if user_id:
            comment = random.choice(COMMENTS).format(year=datetime.now().year)
            
            cursor.execute('''
                INSERT INTO comments (post_id, user_id, content, created_at)
                VALUES (?, ?, ?, ?)
            ''', (post_id, user_id[0], comment, datetime.now().isoformat()))
            
            # Update post comment count
            cursor.execute('''
                UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?
            ''', (post_id,))

def generate_multiple_posts(count=5):
    """Generate multiple posts for the day."""
    print(f"[ContentBot] Generating {count} posts...")
    
    for i in range(count):
        generate_daily_post()
        if i < count - 1:
            # Random delay between posts (simulated)
            pass
    
    print(f"\n[ContentBot] Done! Generated {count} posts.\n")

def schedule_daily():
    """Schedule this to run once per day."""
    print("=" * 60)
    print("LiTree Social - Daily Content Generator")
    print("=" * 60)
    
    # Ensure bots exist
    create_bot_accounts()
    
    # Generate posts
    generate_multiple_posts(5)  # 5 posts per day
    
    print("Next steps:")
    print("1. Check your feed at http://localhost:5000/feed")
    print("2. Engage with the bot posts as a real user")
    print("3. Invite friends to join the conversation")
    print("Schedule this script to run daily with cron/Windows Task Scheduler")

if __name__ == '__main__':
    schedule_daily()
