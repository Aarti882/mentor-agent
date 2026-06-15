import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mca_mentor.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    """Utility to hash user passwords using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Initializes the database schema if tables do not exist, and runs migrations if needed."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Migration Check: If users table exists but does not contain roadmap_json, drop tables to refresh schema
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'roadmap_json' not in columns:
            print("[Database] Outdated schema found (missing roadmap_json). Migrating database...")
            cursor.execute("DROP TABLE IF EXISTS predictions")
            cursor.execute("DROP TABLE IF EXISTS learning_paths")
            cursor.execute("DROP TABLE IF EXISTS users")
            conn.commit()
            
    # Create updated users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            target_role TEXT,
            timeline_months INTEGER,
            resume_text TEXT,
            roadmap_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create learning_paths table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS learning_paths (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            week_number INTEGER,
            topic TEXT,
            deliverable TEXT,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    
    # Create predictions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            skill_match_score REAL,
            resume_opt_score REAL,
            project_count INTEGER,
            company_type TEXT,
            callback_probability REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    conn.close()

def register_user(name, email, password):
    """Registers a new user and hashes their password. Returns the new user ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    try:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, (name, email.strip().lower(), password_hash))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("A user with this email address already exists.")

def authenticate_user(email, password):
    """Authenticates credentials against database. Returns user dict or None."""
    conn = get_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute("""
        SELECT id, name, email, target_role, timeline_months, resume_text, roadmap_json
        FROM users 
        WHERE email = ? AND password_hash = ?
    """, (email.strip().lower(), password_hash))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_profile(user_id, target_role, timeline_months, resume_text, roadmap_json=None):
    """Updates the career goals, resume text and generated roadmap of a user profile."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users 
        SET target_role = ?, timeline_months = ?, resume_text = ?, roadmap_json = ?
        WHERE id = ?
    """, (target_role, timeline_months, resume_text, roadmap_json, user_id))
    
    conn.commit()
    conn.close()

def save_user(name, email, target_role, timeline_months, resume_text):
    """Legacy helper for backward compatibility - saves user details."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if row:
        user_id = row['id']
        cursor.execute("""
            UPDATE users 
            SET name = ?, target_role = ?, timeline_months = ?, resume_text = ?
            WHERE id = ?
        """, (name, target_role, timeline_months, resume_text, user_id))
    else:
        # Create a dummy password hash if using legacy save helper
        password_hash = hash_password("legacy_mode_default_password")
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, target_role, timeline_months, resume_text)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, password_hash, target_role, timeline_months, resume_text))
        user_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    return user_id

def get_user(user_id):
    """Retrieves user profile details by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, target_role, timeline_months, resume_text, roadmap_json, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users():
    """Retrieves list of all users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, target_role FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_learning_path(user_id, milestones):
    """Saves a list of milestones for a user.
    milestones: list of dicts with keys 'week_number', 'topic', 'deliverable'
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM learning_paths WHERE user_id = ?", (user_id,))
    
    for milestone in milestones:
        cursor.execute("""
            INSERT INTO learning_paths (user_id, week_number, topic, deliverable, completed)
            VALUES (?, ?, ?, ?, 0)
        """, (user_id, milestone['week_number'], milestone['topic'], milestone['deliverable']))
        
    conn.commit()
    conn.close()

def update_milestone_status(user_id, week_number, completed):
    """Updates whether a specific week's milestone is completed (1) or not (0)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE learning_paths
        SET completed = ?
        WHERE user_id = ? AND week_number = ?
    """, (1 if completed else 0, user_id, week_number))
    conn.commit()
    conn.close()

def get_learning_path(user_id):
    """Retrieves learning path milestones for a user, sorted by week."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM learning_paths 
        WHERE user_id = ? 
        ORDER BY week_number ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_prediction(user_id, skill_match_score, resume_opt_score, project_count, company_type, callback_probability):
    """Saves a historical prediction entry for a user."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (user_id, skill_match_score, resume_opt_score, project_count, company_type, callback_probability)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, skill_match_score, resume_opt_score, project_count, company_type, callback_probability))
    conn.commit()
    conn.close()

def get_predictions_history(user_id):
    """Retrieves the history of predictions for a user, sorted by timestamp ascending."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM predictions 
        WHERE user_id = ? 
        ORDER BY timestamp ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Run schema setup and migrations
init_db()
