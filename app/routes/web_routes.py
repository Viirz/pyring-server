from flask import Blueprint, request, render_template, redirect, url_for, make_response, jsonify
from app.services.db_service import get_user, get_agents, get_agents_by_uuid, get_user_by_email
from app.utils.jwt_utils import verify_jwt, blacklist_token

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    try:
        user = list(get_user())  # Convert cursor to list
        if not user:  # If no user exists
            return render_template("register.html")  # Render registration form

        return redirect(url_for('web.login'))
    except Exception as e:
        return make_response(jsonify({"msg": f"something went wrong: {e}"}), 500)

@web_bp.route('/login', methods=['GET'])
def login():
    try:
        token = request.cookies.get('token')  # Get JWT token from cookies
        if token and verify_jwt(token):  # Verify JWT token
            return redirect(url_for('web.dashboard'))

        return render_template("login.html")  # Render login form

    except Exception as e:
        return make_response(jsonify({"msg": f"something went wrong: {e}"}), 500)

from datetime import datetime

@web_bp.route('/dashboard')
def dashboard():
    token = request.cookies.get('token')  # Get JWT token from cookies
    decoded_token = verify_jwt(token)
    if not token or not decoded_token:  # Verify JWT token
        return redirect(url_for('web.login'))  # Redirect to login if token is invalid

    email = decoded_token.get('email') if decoded_token else None
    
    # Check if the jwt token contains the email
    if not email:
        return redirect(url_for('web.login'))
    
    user = get_user_by_email(email)
    if isinstance(user, Exception):  # Handle errors from the database service
        return make_response(jsonify({"msg": str(user)}), 404)
    
    if not user or user['email'] != email: # Check if the user exists
        return make_response(jsonify({"msg": "Invalid email"}), 401)
    
    # Fetch all agents documents
    agents = list(get_agents())
    
    # Initialize the counts dictionary
    counts = {"all": 0, 0: 0, 1: 0, 2: 0}

    # Format the 'last_handshake' field and count statuses
    for agent in agents:
        if 'last_handshake' in agent and agent['last_handshake']:
            # Convert the timestamp to a datetime object
            timestamp = datetime.fromtimestamp(agent['last_handshake'])
            # Format the datetime object to DD/MM/YYYY - HH:SS
            agent['last_handshake'] = timestamp.strftime('%d/%m/%Y - %H:%M:%S')
        else:
            agent['last_handshake'] = 'N/A'  # Default to 'null' if the field is missing or None
        
        # Count the status
        status = agent.get('status', 'null')
        if status in counts:
            counts[status] += 1
        counts["all"] += 1  # Increment the total count

    # Pass the agents and counts to the template
    return render_template("dashboard.html", agents=agents, counts=counts)

@web_bp.route('/logout')
def logout():
    token = request.cookies.get('token')  # Get JWT token from cookies
    if token and verify_jwt(token):
        blacklist_token(token) # Blacklist the token
        response = make_response(redirect(url_for('web.index')))
        response.delete_cookie('token')  # Remove the JWT token from cookies
        return response

    return make_response(jsonify({"msg": "Invalid or missing token"}), 401)

@web_bp.route('/account', methods=['GET'])
def account():
    token = request.cookies.get('token')
    if not token or not verify_jwt(token):
        return redirect(url_for('web.login'))
    
    decoded_token = verify_jwt(token)
    email = decoded_token.get('email') if decoded_token else None
    if not email:
        return redirect(url_for('web.login'))
    
    user = list(get_user())
    if not user or not any(u['email'] == email for u in user):
        return make_response(jsonify({"msg": "Invalid email"}), 401)
    
    return render_template("account.html", email=email)

@web_bp.route('/agent/<uuid>', methods=['GET'])
def agent_detail(uuid):
    # Validate JWT token
    token = request.cookies.get('token')  # Get JWT token from cookies
    if not token or not verify_jwt(token):  # Verify JWT token
        return redirect(url_for('web.login'))  # Redirect to login if token is invalid

    # Validate UUID and fetch agent data
    try:
        agent = get_agents_by_uuid(uuid)
        if not agent:  # If no agent found
            return make_response(jsonify({"msg": "Agent not found"}), 404)
        
        if isinstance(agent, Exception):  # Handle errors from the database service
            return make_response(jsonify({"msg": str(agent)}), 404)

        if 'last_handshake' in agent and agent['last_handshake']:
            # Convert the timestamp to a datetime object
            timestamp = datetime.fromtimestamp(agent['last_handshake'])
            # Format the datetime object to DD/MM/YYYY - HH:SS
            agent['last_handshake'] = timestamp.strftime('%d/%m/%Y - %H:%M:%S')
        else:
            agent['last_handshake'] = 'N/A'  # Default to 'null' if the field is missing or None
        
        # Render the agent.html template with the agent data
        return render_template("agent.html", agent=agent)
    except Exception as e:
        return make_response(jsonify({"msg": f"Something went wrong: {e}"}), 500)