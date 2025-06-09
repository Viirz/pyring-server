import jwt
from datetime import datetime, timedelta
from app.services.db_service import add_blacklisted_token, get_blacklisted_token, remove_expired_blacklisted_tokens
import os

JWT_SECRET = os.environ.get("JWT_SECRET") 
JWT_ALGORITHM = "HS256"

def generate_jwt(email):
    # Generate a JWT token for the given email
    expiration_time = datetime.now() + timedelta(hours=1)  # Token expires in 1 hour
    payload = {
        "email": email,
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