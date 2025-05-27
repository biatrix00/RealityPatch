import sqlite3
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any, Optional
from config import Config

class Database:
    def __init__(self, db_path: str = Config.DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Claims table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    claim_text TEXT NOT NULL,
                    subject TEXT,
                    predicate TEXT,
                    object TEXT,
                    status TEXT,
                    confidence REAL,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Agent results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    claim_id INTEGER,
                    agent_name TEXT NOT NULL,
                    confidence REAL,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (claim_id) REFERENCES claims (id)
                )
            """)
            
            conn.commit()
    
    def create_user(self, username: str, password_hash: str) -> Optional[int]:
        """Create a new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "password_hash": row[2]
                }
            return None
    
    def create_session(self, user_id: int) -> str:
        """Create a new session for user"""
        import secrets
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=Config.SESSION_EXPIRY_DAYS)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
                (user_id, session_token, expires_at)
            )
            return session_token
    
    def validate_session(self, session_token: str) -> Optional[int]:
        """Validate session token and return user_id if valid"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id FROM sessions 
                WHERE session_token = ? AND expires_at > CURRENT_TIMESTAMP
                """,
                (session_token,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def save_claim(self, user_id: int, claim_data: Dict[str, Any]) -> int:
        """Save a new claim and its analysis results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert claim
            cursor.execute(
                """
                INSERT INTO claims (
                    user_id, claim_text, subject, predicate, object,
                    status, confidence, explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    claim_data["claim_text"],
                    claim_data.get("subject"),
                    claim_data.get("predicate"),
                    claim_data.get("object"),
                    claim_data.get("status"),
                    claim_data.get("confidence"),
                    claim_data.get("explanation")
                )
            )
            claim_id = cursor.lastrowid
            
            # Insert agent results
            for agent_result in claim_data.get("agent_results", []):
                cursor.execute(
                    """
                    INSERT INTO agent_results (
                        claim_id, agent_name, confidence, explanation
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        claim_id,
                        agent_result["agent_name"],
                        agent_result["confidence"],
                        agent_result["explanation"]
                    )
                )
            
            return claim_id
    
    def get_user_claims(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all claims for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.*, GROUP_CONCAT(
                    json_object(
                        'agent_name', ar.agent_name,
                        'confidence', ar.confidence,
                        'explanation', ar.explanation
                    )
                ) as agent_results
                FROM claims c
                LEFT JOIN agent_results ar ON c.id = ar.claim_id
                WHERE c.user_id = ?
                GROUP BY c.id
                ORDER BY c.created_at DESC
                """,
                (user_id,)
            )
            
            claims = []
            for row in cursor.fetchall():
                claim = {
                    "id": row[0],
                    "user_id": row[1],
                    "claim_text": row[2],
                    "subject": row[3],
                    "predicate": row[4],
                    "object": row[5],
                    "status": row[6],
                    "confidence": row[7],
                    "explanation": row[8],
                    "created_at": row[9],
                    "agent_results": json.loads(f"[{row[10]}]") if row[10] else []
                }
                claims.append(claim)
            
            return claims 