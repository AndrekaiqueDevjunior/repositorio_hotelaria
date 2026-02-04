from sqlalchemy.orm import Session
from app.db.base import get_session

def get_db() -> Session:
    """Dependency to get database session"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
