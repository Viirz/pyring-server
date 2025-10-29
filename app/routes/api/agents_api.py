from flask import Blueprint, jsonify, request
from app.services.db_service import insert_command, get_top_commands_by_uuid, get_user_by_email
from app.utils.jwt_utils import verify_jwt
from app.utils.jwt_utils import require_roles
from app.utils.agent_utils import add_agents, delete_agent
from app.utils.logging_utils import log_request_blueprint, log_response_blueprint
import uuid as uuid_gen
import time
import logging
from shlex import split
import os
from app.utils.pgp_utils import AGENT_PGP_DIR, gpg, get_server_public_key
from argon2 import PasswordHasher, exceptions as argon2_exceptions

agents_api_bp = Blueprint('agents_api', __name__, url_prefix='/api/agents')
logger = logging.getLogger('pyring.api.agents')

@agents_api_bp.before_request
def log_api_request():
    log_request_blueprint('pyring.api')

@agents_api_bp.after_request
def log_api_response(response):
    return log_response_blueprint(response, 'pyring.api')

@agents_api_bp.before_request
def token_required():
    token = request.cookies.get('token')  # Get JWT token from cookies
    if not token or not verify_jwt(token):  # Verify JWT token
        logger.warning(f"Unauthorized access attempt to {request.endpoint} from {request.remote_addr}")
        return jsonify({"msg": "Unauthorized"}), 401

@agents_api_bp.route('/', methods=['POST'])
@require_roles('admin', 'super-admin')
def create_new_agents():
    try:
        data = request.get_json()
        name = data.get("name") if data else None
        
        if not name:
            logger.warning(f"Agent creation failed: Missing name parameter")
            return jsonify({"msg": "Name is required"}), 400

        logger.info(f"Creating new agent with name: {name}")
        
        # Generate a new UUID for the agent
        result, status = add_agents(name)
        if status != 201:
            logger.error(f"Agent creation failed for name '{name}': {result}")
            return jsonify(result), status
        
        agent_uuid = result["uuid"]
        logger.info(f"Agent created successfully with UUID: {agent_uuid}")

        # Generate agent PGP keypair
        input_data = gpg.gen_key_input(
            name_real=name,
            name_email=f"{agent_uuid}@agent.id",
            key_type="RSA",
            key_length=2048,
            passphrase=agent_uuid
        )
        
        try:
            key = gpg.gen_key(input_data)
            logger.info(f"PGP keypair generated for agent {agent_uuid}")
        except Exception as e:
            logger.error(f"Key generation failed for agent {agent_uuid}: {e}")
            return jsonify({"msg": f"Key generation failed: {e}"}), 500

        # Export private and public keys (private shown only once)
        priv_key = gpg.export_keys(key.fingerprint, True, passphrase=agent_uuid)
        
        # Get server's public key from file
        server_pub_key = get_server_public_key()
        
        # Save public key to .pgp/{uuid}_pub.asc
        pub_key = gpg.export_keys(key.fingerprint, False,)
        pub_path = os.path.join(AGENT_PGP_DIR, f"{agent_uuid}_pub.asc")
        with open(pub_path, "w") as f:
            f.write(pub_key)

        logger.info(f"Agent {agent_uuid} setup completed successfully")
        
        # Do NOT store priv_key on server, only return it once
        return jsonify({
            "uuid": agent_uuid,
            "agent_private_key": priv_key,
            "server_public_key": server_pub_key
        }), 201
    except Exception as e:
        logger.error(f"Unexpected error in create_new_agents: {e}")
        return jsonify({"msg": f"Something went wrong: {e}"}), 500
    
@agents_api_bp.route('/<uuid>/command', methods=['POST', 'GET'])
@require_roles('admin', 'super-admin')
def handle_agent_command(uuid):
    try:
        if request.method == 'GET':
            logger.info(f"Retrieving commands for agent {uuid}")
            # Retrieve the top 5 commands based on timestamp
            commands = get_top_commands_by_uuid(uuid, limit=5)
            
            if not commands or isinstance(commands, Exception):
                logger.warning(f"No commands found for agent {uuid}")
                return jsonify({"msg": "No commands found"}), 404
            
            # Filter the fields to return only command_id, command, and response
            filtered_commands = [
                {
                    "command_id": cmd.get("command_id"),
                    "command": cmd.get("command"),
                    "response": cmd.get("response")
                }
                for cmd in commands
            ]

            logger.info(f"Retrieved {len(filtered_commands)} commands for agent {uuid}")
            return jsonify(filtered_commands), 200

        elif request.method == 'POST':
            data = request.get_json()
            command = data.get("command") if data else None
            
            if not command:
                logger.warning(f"Command creation failed for agent {uuid}: Missing command parameter")
                return jsonify({"msg": "Command is required"}), 400

            logger.info(f"Adding command for agent {uuid}: {command}")
            
            command_arr = split(command)
            
            command_data = {
                "uuid": uuid,
                "command_id": str(uuid_gen.uuid4()),
                "command": command,
                "timestamp": time.time(),
                "retrieved": False,
                "response": None
            }
            
            insert_command(command_data)
            logger.info(f"Command added successfully for agent {uuid} with ID: {command_data['command_id']}")
            
            return jsonify({"msg": "Command added successfully"}), 201

    except Exception as e:
        logger.error(f"Unexpected error in handle_agent_command for agent {uuid}: {e}")
        return jsonify({"msg": f"Something went wrong: {e}"}), 500

@agents_api_bp.route('/<uuid>', methods=['DELETE'])
@require_roles('admin', 'super-admin')
def delete_agent_endpoint(uuid):
    try:
        logger.info(f"Attempting to delete agent {uuid}")
        
        # Get current user from JWT
        token = request.cookies.get('token')
        decoded_token = verify_jwt(token)
        
        if not token or not decoded_token:
            logger.warning(f"Unauthorized agent deletion attempt for {uuid}")
            return jsonify({"msg": "Unauthorized"}), 401

        email = decoded_token.get('email') if decoded_token else None
        if not email:
            logger.warning(f"Agent deletion failed for {uuid}: Email not found in token")
            return jsonify({"msg": "Email not found in token"}), 401
        
        # Get the password from request body
        data = request.get_json()
        if not data:
            logger.warning(f"Agent deletion failed for {uuid}: Password is required")
            return jsonify({"msg": "Password is required"}), 400
            
        password = data.get("password")
        if not password:
            logger.warning(f"Agent deletion failed for {uuid}: Password is required")
            return jsonify({"msg": "Password is required"}), 400
        
        # Verify admin password
        user = get_user_by_email(email)
        if not user:
            logger.warning(f"Agent deletion failed for {uuid}: User {email} not found")
            return jsonify({"msg": "User not found"}), 404
        
        ph = PasswordHasher()
        try:
            ph.verify(user['password'], password)
            logger.info(f"Password verified for user {email} attempting to delete agent {uuid}")
        except argon2_exceptions.VerifyMismatchError:
            logger.warning(f"Agent deletion failed for {uuid}: Invalid password for user {email}")
            return jsonify({"msg": "Invalid password"}), 401
        
        # Delete the agent
        result, status = delete_agent(uuid)
        
        if status == 200:
            logger.info(f"Agent {uuid} deleted successfully by user {email}")
        else:
            logger.error(f"Agent deletion failed for {uuid}: {result}")
            
        return jsonify(result), status
        
    except Exception as e:
        logger.error(f"Unexpected error in delete_agent_endpoint for agent {uuid}: {e}")
        return jsonify({"msg": f"Something went wrong: {e}"}), 500