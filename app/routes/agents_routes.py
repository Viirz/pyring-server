from flask import Blueprint, request
import time, json
from app.utils.request_utils import sanitize_input, validate_request_data
from app.services.db_service import update_agents, get_unretrieved_commands_by_uuid, update_command_response
from app.utils.pgp_utils import verify_and_decrypt_status, sign_and_encrypt_command

agents_bp = Blueprint('agents', __name__)

@agents_bp.route('/agents', methods=['POST'])
def receive_status():
    try:
        encrypted_data = request.data
        agent_uuid = request.headers.get("X-Agent-UUID")
        if not agent_uuid:
            raise ValueError("Missing agent UUID header")
        decrypted_json = verify_and_decrypt_status(encrypted_data, agent_uuid)
        request_data = json.loads(decrypted_json.strip())
        
        print(f"Received request data: {request_data}", flush=True)
        if not request_data:
            raise ValueError("Request data is required")
        
        status = request_data.get("status")

        if status is None:
            raise ValueError("Status is required")
        
        if status == 1 or status == 2: # Agent is reachable
            request_data.update({
                "last_handshake": time.time(),
                "last_ip": request.remote_addr,
                "uuid": agent_uuid
            })
            
            required_fields = {
                "status": int,
                "last_handshake": float,
                "last_ip": str,
                "uuid": str
            }
                    
            validate_request_data(request_data, required_fields)
            sanitized_data = sanitize_input(request_data)
            update_agents(sanitized_data)
                        
        elif status == 5: # Agent request for commands
            required_fields = {
                "status": int
            }
            
            validate_request_data(request_data, required_fields)
            sanitized_data = sanitize_input(request_data)
            
            commands = get_unretrieved_commands_by_uuid(agent_uuid)
            
            if not commands or isinstance(commands, Exception):
                return {"msg": "No commands found"}, 404
            
            filtered_commands = [{"command_id": cmd["command_id"], "command": cmd["command"]} for cmd in commands]
            filtered_commands = json.dumps(filtered_commands)
            encrypted_commands = sign_and_encrypt_command(filtered_commands, agent_uuid)
            
            return encrypted_commands, 200
        
        elif status == 6: # Agent sending commands response
            required_fields = {
                "status": int,
                "command_id": str,
                "response": str,
            }
            
            validate_request_data(request_data, required_fields)
            sanitized_data = sanitize_input(request_data)
            
            update_command_response(
                agent_uuid,
                sanitized_data["command_id"],
                sanitized_data["response"]
            )
        else:
            raise ValueError("Invalid status value")
        
    except Exception as e:
        return {"msg": f"something went wrong: {e}"}, 500
    
    encrypted_response = sign_and_encrypt_command(
        json.dumps({"msg": "OK"}),
        agent_uuid
    )
    
    if not encrypted_response:
        return {"msg": "Failed to encrypt response"}, 500
    
    return encrypted_response, 200