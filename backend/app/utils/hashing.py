import hashlib
import bcrypt


def hash_password(raw: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(raw.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(raw: str, hashed: str) -> bool:
    if not hashed:
        return False

    # bcrypt
    if hashed.startswith('$2a$') or hashed.startswith('$2b$') or hashed.startswith('$2y$'):
        try:
            return bcrypt.checkpw(raw.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    # SHA256 legado
    try:
        return hashlib.sha256(raw.encode()).hexdigest() == hashed
    except Exception:
        return False