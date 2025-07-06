"""Simple session storage using Flask's session with database backing"""
import json
import uuid
from datetime import datetime, timedelta
from flask import session, request
from app_new import db

class SimpleSessionData(db.Model):
    __tablename__ = 'simple_sessions'
    
    session_key = db.Column(db.String(255), primary_key=True)
    data = db.Column(db.Text, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_session():
    """Initialize session with permanent settings"""
    if 'session_key' not in session:
        session['session_key'] = str(uuid.uuid4())
        session.permanent = True
    return session['session_key']

def save_session_data(data):
    """Save data to database using Flask session key"""
    session_key = init_session()
    expires = datetime.utcnow() + timedelta(hours=1)
    
    # Clean up expired sessions
    SimpleSessionData.query.filter(SimpleSessionData.expires < datetime.utcnow()).delete()
    
    session_record = SimpleSessionData.query.get(session_key)
    if session_record:
        session_record.data = json.dumps(data)
        session_record.expires = expires
    else:
        session_record = SimpleSessionData(
            session_key=session_key,
            data=json.dumps(data),
            expires=expires
        )
        db.session.add(session_record)
    
    db.session.commit()
    print(f"🔧 Saved session data for key: {session_key}")
    return session_key

def load_session_data():
    """Load data from database using Flask session key"""
    session_key = session.get('session_key')
    if not session_key:
        print(f"🔧 No session key found")
        return {}
    
    session_record = SimpleSessionData.query.get(session_key)
    if session_record and session_record.expires > datetime.utcnow():
        try:
            data = json.loads(session_record.data)
            print(f"🔧 Loaded session data for key: {session_key} - {data}")
            return data
        except (json.JSONDecodeError, TypeError):
            pass
    
    print(f"🔧 No valid session data for key: {session_key}")
    return {}