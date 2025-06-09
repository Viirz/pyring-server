from flask import Blueprint, request
import json
import time
from app.utils.request_utils import sanitize_input, validate_request_data
from app.services.db_service import insert_logs
from app.utils.pgp_utils import verify_and_decrypt_status, sign_and_encrypt_command

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs', methods=['POST'])
def receive_logs():
    try:
        # Get encrypted data and agent UUID from header
        encrypted_data = request.data
        agent_uuid = request.headers.get("X-Agent-UUID")
        if not agent_uuid:
            raise ValueError("Missing agent UUID header")
        
        # Decrypt and verify the PGP data
        decrypted_json = verify_and_decrypt_status(encrypted_data, agent_uuid)
        request_data = json.loads(decrypted_json.strip())
        
        print(f"Received logs data: {request_data}", flush=True)
        
        # Add timestamp and UUID to the request data
        request_data.update({
            "timestamp": time.time(),
            "uuid": agent_uuid  # Add UUID from header to data
        })
        
        # Validate the decrypted data
        required_fields = {
            "uuid": str,
            "timestamp": float,
            "ip_route": str,
            "journalctl": str,
            "tracepath": str,
            "dmsg": str,
            "network_int": str
        }
        
        validate_request_data(request_data, required_fields)
        sanitized_data = sanitize_input(request_data)
        
        # Insert logs into database
        insert_logs(sanitized_data)
        
        # Sign and encrypt the response
        encrypted_response = sign_and_encrypt_command(
            json.dumps({"msg": "OK"}),
            agent_uuid
        )
        
        if not encrypted_response:
            raise Exception("Failed to encrypt response")
        
        return encrypted_response, 200, {'Content-Type': 'application/pgp-encrypted'}
        
    except Exception as e:
        print(f"Error in receive_logs: {e}", flush=True)
        
        # Try to send encrypted error response if we have agent_uuid
        try:
            if 'agent_uuid' in locals():
                encrypted_error = sign_and_encrypt_command(
                    json.dumps({"msg": f"something went wrong: {e}"}),
                    agent_uuid
                )
                return encrypted_error, 500, {'Content-Type': 'application/pgp-encrypted'}
        except:
            pass
        
        # Fallback to plain text error
        return {"msg": f"something went wrong: {e}"}, 500