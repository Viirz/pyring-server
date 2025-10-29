import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from app.services.db_service import add_blacklisted_token, get_blacklisted_token, remove_expired_blacklisted_tokens
import os

JWT_SECRET = os.environ.get("JWT_SECRET") 
JWT_ALGORITHM = "HS256"

def generate_jwt(email, role):
    """Generate a JWT token for the given email including role."""
    expiration_time = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
    payload = {
        "email": email,
        "role": role,
        "exp": expiration_time
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def blacklist_token(token):
    # Add a token to the blacklist with its expiration time
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        expiration_time = datetime.fromtimestamp(decoded["exp"])
        add_blacklisted_token(token, expiration_time)
    except jwt.InvalidTokenError:
        pass  # Ignore invalid tokens

def verify_jwt(token):
    # Verify the given JWT token
    try:
        # Check if the token is blacklisted
        if get_blacklisted_token(token):
            return None  # Token is blacklisted

        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        return None  # Token has expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def cleanup_blacklist():
    # Remove expired tokens from the blacklist
    remove_expired_blacklisted_tokens()


def require_roles(*allowed_roles):
    """Decorator to enforce role-based access using JWT stored in cookies.

    Usage:
        @require_roles('admin', 'super-admin')
        def some_view():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = request.cookies.get('token')
            decoded = verify_jwt(token)
            if not token or not decoded:
                return jsonify({"msg": "Unauthorized"}), 401
            role = decoded.get("role", "user")
            # Expose current user payload for downstream use if needed
            g.current_user = decoded
            if allowed_roles and role not in allowed_roles:
                return jsonify({"msg": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator