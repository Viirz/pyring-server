from flask import Blueprint, jsonify, request, make_response, redirect, url_for
from app.services.db_service import (
    change_password,
    get_user_by_email,
    add_user,
    get_user,
    get_users,
    update_user_role,
    delete_user_by_email,
)
from app.utils.jwt_utils import verify_jwt, generate_jwt, blacklist_token, require_roles
from argon2 import PasswordHasher, exceptions as argon2_exceptions
import logging
from app.utils.logging_utils import log_request_blueprint, log_response_blueprint

users_api_bp = Blueprint('users_api', __name__, url_prefix='/api/users')
ph = PasswordHasher()
logger = logging.getLogger('pyring.api.users')

@users_api_bp.before_request
def log_api_request():
    log_request_blueprint('pyring.api')

@users_api_bp.after_request
def log_api_response(response):
    return log_response_blueprint(response, 'pyring.api')

@users_api_bp.route('/change_password', methods=['POST'])
def change_password_route():
    # Change the password for a user
    try:
        token = request.cookies.get('token')  # Get JWT token from cookies
        decoded_token = verify_jwt(token)
        
        if not token or not decoded_token:  # Verify JWT token
            return jsonify({"msg": "Unauthorized"}), 401

        email = decoded_token.get('email') if decoded_token else None
        if not email:
            return jsonify({"msg": "Email not found in token"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided"}), 400

        old_password = data.get("old_password")
        new_password = data.get("new_password")
        
        if not old_password or not new_password:
            return jsonify({"msg": "Old password and new password are required"}), 400
        
        user = get_user_by_email(email)
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        # Verify the old password
        try:
            ph.verify(user['password'], old_password)  # Verify old password
        except argon2_exceptions.VerifyMismatchError:
            return jsonify({"msg": "Old password is incorrect"}), 401
        
        # Hash the new password
        new_password_hash = ph.hash(new_password)

        # Call the change_password function to update the user's password
        change_password(email, new_password_hash)
        return jsonify({"msg": "Password changed successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500

@users_api_bp.route('/login', methods=['POST'])
def login_route():
    # Login a user
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided"}), 400

        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            return jsonify({"msg": "Email and password are required"}), 400
        
        user = get_user_by_email(email)
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        # Verify the password
        try:
            ph.verify(user['password'], password)  # Verify password
        except argon2_exceptions.VerifyMismatchError:
            return jsonify({"msg": "Invalid email or password"}), 401

        # Determine role; default to 'user' if missing
        role = user.get('role', 'user')
        # Generate JWT token with role
        token = generate_jwt(email, role)
        response = jsonify({"msg": "Login successful"})
        response.set_cookie('token', token, secure=False, httponly=True, samesite='Strict')  # Store JWT token in cookies
        return response, 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500
    
@users_api_bp.route('/register', methods=['POST'])
def register_route():
    # Register a new user (first user only)
    try:        
        # If there's already a user, return an error
        user = list(get_user())
        if user:
            return jsonify({"msg": "User already exists"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided"}), 400

        email = data.get("email")
        name = data.get("name")
        password = data.get("password")
        repeat_password = data.get("repeat_password")
        
        if not email or not name or not password or not repeat_password:
            return jsonify({"msg": "Email, password and repeat password are required"}), 400
        
        if password != repeat_password:
            return jsonify({"msg": "Passwords do not match"}), 400
        
        # Check if the user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({"msg": "User already exists"}), 400
        
        # Hash the password
        password_hash = ph.hash(password)

        # First user is super-admin
        user_data = {
            "email": email,
            "name": name,
            "password": password_hash,
            "role": "super-admin",
        }
        add_user(user_data)
        return jsonify({"msg": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500    
    
@users_api_bp.route('/logout', methods=['POST'])
def logout_route():
    # Logout a user
    token = request.cookies.get('token')  # Get JWT token from cookies
    if token and verify_jwt(token):
        decoded_token = verify_jwt(token)
        email = decoded_token.get('email') if decoded_token else 'Unknown'
        
        blacklist_token(token)  # Blacklist the token
        
        response = make_response(redirect(url_for('web.index')))
        response.delete_cookie('token')  # Remove the JWT token from cookies
        return response
    
    return jsonify({"msg": "Invalid token"}), 400


# ---------------- Super-admin only user management ----------------

@users_api_bp.route('/', methods=['GET'])
@require_roles('super-admin')
def list_users_route():
    try:
        users = list(get_users())
        return jsonify([
            {"email": u.get("email"), "name": u.get("name"), "role": u.get("role", "user")}
            for u in users
        ]), 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500


@users_api_bp.route('/create', methods=['POST'])
@require_roles('super-admin')
def create_user_route():
    try:
        data = request.get_json() or {}
        email = (data.get("email") or '').strip()
        name = (data.get("name") or '').strip()
        password = data.get("password") or ''
        repeat_password = data.get("repeat_password") or ''
        role = (data.get("role") or 'user').strip()

        if not email or not name or not password or not repeat_password or not role:
            return jsonify({"msg": "All fields are required"}), 400
        if password != repeat_password:
            return jsonify({"msg": "Passwords do not match"}), 400
        if role not in ["super-admin", "admin", "user"]:
            return jsonify({"msg": "Invalid role"}), 400
        if get_user_by_email(email):
            return jsonify({"msg": "User already exists"}), 400

        password_hash = ph.hash(password)
        add_user({
            "email": email,
            "name": name,
            "password": password_hash,
            "role": role,
        })
        return jsonify({"msg": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500


@users_api_bp.route('/<email>/role', methods=['PUT'])
@require_roles('super-admin')
def update_user_role_route(email):
    try:
        data = request.get_json() or {}
        role = (data.get("role") or '').strip()
        if role not in ["super-admin", "admin", "user"]:
            return jsonify({"msg": "Invalid role"}), 400
        result = update_user_role(email, role)
        if isinstance(result, Exception):
            return jsonify({"msg": str(result)}), 500
        return jsonify({"msg": "Role updated successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500


@users_api_bp.route('/<email>', methods=['DELETE'])
@require_roles('super-admin')
def delete_user_route(email):
    try:
        result = delete_user_by_email(email)
        if isinstance(result, Exception):
            return jsonify({"msg": str(result)}), 500
        return jsonify({"msg": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500