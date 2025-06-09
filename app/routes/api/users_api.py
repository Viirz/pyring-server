from flask import Blueprint, jsonify, request, make_response, redirect, url_for
from app.services.db_service import change_password, get_user_by_email, add_user, get_user
from app.utils.jwt_utils import verify_jwt, generate_jwt, blacklist_token
from argon2 import PasswordHasher, exceptions as argon2_exceptions

users_api_bp = Blueprint('users_api', __name__, url_prefix='/api/users')
ph = PasswordHasher()

# @users_api_bp.before_request
# def token_required():
#     token = request.cookies.get('token')  # Get JWT token from cookies
#     if not token or not verify_jwt(token):  # Verify JWT token
#         return jsonify({"msg": "Unauthorized"}), 401

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
        
        # Generate JWT token
        token = generate_jwt(email)
        response = jsonify({"msg": "Login successful"})
        response.set_cookie('token', token, secure=False, httponly=True)  # Store JWT token in cookies
        return response, 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500
    
@users_api_bp.route('/register', methods=['POST'])
def register_route():
    # Register a new user
    try:
        # If there's already a user, return an error
        user = list(get_user())
        if user:
            return jsonify({"msg": "User already exists"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided"}), 400

        email = data.get("email")
        password = data.get("password")
        repeat_password = data.get("repeat_password")
        
        if not email or not password or not repeat_password:
            return jsonify({"msg": "Email, password and repeat password are required"}), 400
        
        if password != repeat_password:
            return jsonify({"msg": "Passwords do not match"}), 400
        
        # Check if the user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({"msg": "User already exists"}), 400
        
        # Hash the password
        password_hash = ph.hash(password)

        # Call the add_user function to create a new user
        user_data = {
            "email": email,
            "password": password_hash
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
        blacklist_token(token)  # Blacklist the token
        response = make_response(redirect(url_for('web.index')))
        response.delete_cookie('token')  # Remove the JWT token from cookies
        return response
    return jsonify({"msg": "Invalid token"}), 400