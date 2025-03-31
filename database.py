import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Optional
from config import DATABASE_PATH
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class Database:
    # Add this method to safely convert rows to dicts
    @staticmethod
    def row_to_dict(row):   
        return dict(row) if row else None
    
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            internal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            avatar_url TEXT,
            submitted_posts INTEGER DEFAULT 0,
            approved_posts INTEGER DEFAULT 0,
            rejected_posts INTEGER DEFAULT 0,
            role TEXT DEFAULT 'regular',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Posts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text_content TEXT,
            image_file_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            reviewed_by INTEGER,
            rejection_reason TEXT,
            FOREIGN KEY (user_id) REFERENCES users (internal_id),
            FOREIGN KEY (reviewed_by) REFERENCES users (internal_id)
        )
        """)
        
        # Feedback table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            admin_response TEXT,
            responded_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (internal_id),
            FOREIGN KEY (responded_by) REFERENCES users (internal_id)
        )
        """)
        
        conn.commit()

class Database:
    @staticmethod
    def create_post(user_id: int, text: str, image_file_id: str):
        """Create new post with transaction handling"""
        with get_db_connection() as conn:
            try:
                cursor = conn.cursor()
                
                # Insert post
                cursor.execute(
                    "INSERT INTO posts (user_id, text_content, image_file_id) VALUES (?, ?, ?)",
                    (user_id, text, image_file_id)
                )
                post_id = cursor.lastrowid
                
                # Update user stats
                cursor.execute(
                    "UPDATE users SET submitted_posts = submitted_posts + 1 WHERE internal_id = ?",
                    (user_id,)
                )
                
                conn.commit()
                return post_id
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Error creating post: {e}")
                raise
   
    @staticmethod
    def add_user(telegram_id: int, username: str, full_name: str):
        """Add new user to database"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (telegram_id, username, full_name) VALUES (?, ?, ?)",
                (telegram_id, username, full_name)
            )
            conn.commit()

# Good practice example
    @staticmethod
    def get_user(telegram_id: int):
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    @staticmethod
    def get_user_by_id(internal_id: int):
        """Get user by internal ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE internal_id = ?", (internal_id,))
            return cursor.fetchone()

    
    @staticmethod
    def get_user_posts(user_id: int):
        """Get all posts by user"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM posts 
                WHERE user_id = ?
                ORDER BY created_at DESC
                """, (user_id,))
            return cursor.fetchall()
    @staticmethod
    def get_all_users():
        """Get all users"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users 
                ORDER BY internal_id
                """)
            return cursor.fetchall()

    @staticmethod
    def update_user_stats(user_id: int, field: str, value: int = 1):
        """Update user statistics"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE users SET {field} = {field} + ? WHERE internal_id = ?",
                (value, user_id)
            )
            conn.commit()

    @staticmethod
    def block_user(user_id: int, admin_id: int, reason: str):
        """Block a user"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status = 'blocked' WHERE internal_id = ?",
                (user_id,)
            )
            cursor.execute(
                "INSERT INTO user_blocks (user_id, admin_id, reason) VALUES (?, ?, ?)",
                (user_id, admin_id, reason)
            )
            conn.commit()

    @staticmethod
    def unblock_user(user_id: int, admin_id: int, reason: str):
        """Unblock a user"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET status = 'active' WHERE internal_id = ?",
                (user_id,)
            )
            cursor.execute(
                """UPDATE user_blocks 
                SET unblocked_at = CURRENT_TIMESTAMP, unblock_reason = ? 
                WHERE user_id = ? AND unblocked_at IS NULL""",
                (reason, user_id)
            )
            conn.commit()

    # ======================
    # Post Methods
    # ======================
    
    @staticmethod
    def get_post(post_id: int):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, u.username, u.telegram_id 
                FROM posts p
                JOIN users u ON p.user_id = u.internal_id
                WHERE p.post_id = ?
                """, (post_id,))
            return cursor.fetchone()
    @staticmethod
    def get_posts_by_status(status: str):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, u.username, u.telegram_id 
                FROM posts p
                JOIN users u ON p.user_id = u.internal_id
                WHERE p.status = ?
                ORDER BY p.created_at
                """, (status,))
            return cursor.fetchall()
    # @staticmethod
    # def update_post_status(post_id: int, status: str, admin_id: int, rejection_reason: str = None):
    #     with get_db_connection() as conn:
    #         cursor = conn.cursor()
    #         cursor.execute(
    #             """UPDATE posts 
    #             SET status = ?, 
    #                 reviewed_at = datetime('now'), 
    #                 reviewed_by = ?,
    #                 rejection_reason = ?
    #             WHERE post_id = ?""",
    #             (status, admin_id, rejection_reason, post_id)
    #         )
            
    #         # Update user statistics
    #         cursor.execute("SELECT user_id FROM posts WHERE post_id = ?", (post_id,))
    #         post = cursor.fetchone()
    #         if post:
    #             column = 'approved_posts' if status == 'approved' else 'rejected_posts'
    #             cursor.execute(
    #                 f"UPDATE users SET {column} = {column} + 1 WHERE internal_id = ?",
    #                 (post['user_id'],)
    #             )
    #         conn.commit()
    @staticmethod
    def update_post_status(post_id: int, status: str, admin_id: int, rejection_reason: str = None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if rejection_reason:
                cursor.execute(
                    """UPDATE posts 
                    SET status = ?, 
                        reviewed_at = datetime('now'), 
                        reviewed_by = ?,
                        rejection_reason = ?
                    WHERE post_id = ?""",
                    (status, admin_id, rejection_reason, post_id)
                )
            else:
                cursor.execute(
                    """UPDATE posts 
                    SET status = ?, 
                        reviewed_at = datetime('now'), 
                        reviewed_by = ?
                    WHERE post_id = ?""",
                    (status, admin_id, post_id)
                )
            
            # Update user statistics
            cursor.execute("SELECT user_id FROM posts WHERE post_id = ?", (post_id,))
            post = cursor.fetchone()
            if post:
                column = 'approved_posts' if status == 'approved' else 'rejected_posts'
                cursor.execute(
                    f"UPDATE users SET {column} = {column} + 1 WHERE internal_id = ?",
                    (post['user_id'],)
                )
            conn.commit()
    # ======================
    # Feedback Methods
    # ======================
    
    @staticmethod
    def create_feedback(user_id: int, message: str):
        """Create new feedback"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedback (user_id, message) 
                VALUES (?, ?)
                """, (user_id, message))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_feedback(feedback_id: int):
        """Get feedback by ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, u.username, u.telegram_id 
                FROM feedback f
                JOIN users u ON f.user_id = u.internal_id
                WHERE f.feedback_id = ?
                """, (feedback_id,))
            return cursor.fetchone()

    @staticmethod  
    def get_pending_feedback():
        """Get pending feedback"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, u.username, u.telegram_id 
                FROM feedback f
                JOIN users u ON f.user_id = u.internal_id
                WHERE f.admin_response IS NULL
                ORDER BY f.created_at DESC
                """)
            return cursor.fetchall()

    @staticmethod
    def respond_to_feedback(feedback_id: int, admin_id: int, response: str):
        """Add response to feedback"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE feedback 
                SET admin_response = ?, 
                    responded_by = ?, 
                    responded_at = datetime('now') 
                WHERE feedback_id = ?
                """, (response, admin_id, feedback_id))
            conn.commit()

    # ======================
    # Statistics Methods
    # ======================
    

    @staticmethod
    def get_top_users(metric: str, limit: int = 5):
        """Get top users by metric"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT internal_id, username, {metric} 
                FROM users 
                WHERE role = 'regular' 
                ORDER BY {metric} DESC 
                LIMIT ?
                """, (limit,))
            return cursor.fetchall()
    # ======================
    # Utility Methods
    # ======================
    
    @staticmethod
    def get_admin_ids() -> List[int]:
        """Get all admin Telegram IDs"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM users WHERE role = 'admin'")
            return [row['telegram_id'] for row in cursor.fetchall()]
        
    @staticmethod
    def update_user(telegram_id: int, updates: dict):
        """Update user information in the database"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values())
            values.append(telegram_id)
            
            cursor.execute(
                f"UPDATE users SET {set_clause} WHERE telegram_id = ?",
                values
            )
            conn.commit()

    @staticmethod
    def add_user(telegram_id: int, username: str, full_name: str):
        """Add new user or update existing one"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users (telegram_id, username, full_name)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) 
                DO UPDATE SET username = excluded.username, full_name = excluded.full_name""",
                (telegram_id, username, full_name)
            )
            conn.commit()

    @staticmethod
    def get_post_with_details(post_id: int):
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row  # Ensure Row factory is set
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.*,
                    u.username as user_username,
                    u.telegram_id as user_telegram_id,
                    a.username as admin_username
                FROM posts p
                JOIN users u ON p.user_id = u.internal_id
                LEFT JOIN users a ON p.reviewed_by = a.internal_id
                WHERE p.post_id = ?
            """, (post_id,))
            result = cursor.fetchone()
            return dict(result) if result else None


    @staticmethod
    def get_post(post_id: int):
        """Get basic post information"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE post_id = ?", (post_id,))
            return cursor.fetchone()

    @staticmethod
    def notify_admins(notification_type: str, data: dict):
        """Get all admin IDs for notifications"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM users WHERE role = 'admin'")
            return [admin['telegram_id'] for admin in cursor.fetchall()]
        
    @staticmethod
    def get_all_users_for_notify():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT telegram_id, username, status 
                FROM users 
                WHERE status = 'active'
                ORDER BY internal_id
            """)
            return cursor.fetchall()