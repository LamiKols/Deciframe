"""Database-backed session storage for Flask"""
import json
import uuid
from datetime import datetime, timedelta
from flask import request
from app import db

class SessionData(db.Model):
    __tablename__ = 'session_data'
    
    id = db.Column(db.String(255), primary_key=True)
    data = db.Column(db.Text, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DatabaseSessionInterface:
    """Database-backed session interface"""
    
    def __init__(self):
        self.session_lifetime = timedelta(hours=1)
        self._current_session_id = None
    
    def get_session_id(self):
        """Get session ID from cookie or create new one (cached per request)"""
        if self._current_session_id:
            return self._current_session_id
            
        session_id = request.cookies.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self._current_session_id = session_id
        print(f"🔧 Session ID from cookie: {request.cookies.get('session_id')}")
        print(f"🔧 Using session ID: {session_id}")
        return session_id
    
    def load_session(self):
        """Load session data from database"""
        session_id = self.get_session_id()
        
        # Clean up expired sessions
        expired = datetime.utcnow()
        SessionData.query.filter(SessionData.expires < expired).delete()
        db.session.commit()
        
        # Load current session
        session_record = SessionData.query.get(session_id)
        if session_record and session_record.expires > datetime.utcnow():
            try:
                return json.loads(session_record.data)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return {}
    
    def save_session(self, session_data):
        """Save session data to database"""
        session_id = self.get_session_id()
        expires = datetime.utcnow() + self.session_lifetime
        
        # Always save, even if session_data is empty
        session_record = SessionData.query.get(session_id)
        if session_record:
            session_record.data = json.dumps(session_data)
            session_record.expires = expires
        else:
            session_record = SessionData(
                id=session_id,
                data=json.dumps(session_data),
                expires=expires
            )
            db.session.add(session_record)
        
        db.session.commit()
        return session_id

# Global session interface instance
db_session = DatabaseSessionInterface()