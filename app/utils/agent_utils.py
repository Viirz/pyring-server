from app.services.db_service import insert_uuid, get_agents, update_agents, delete_agent_by_uuid
from app.utils.pgp_utils import delete_agent_pgp_keys
from datetime import datetime, timedelta
import uuid

def add_agents(name: str):
    try:
        # Generate a new UUID
        new_uuid = str(uuid.uuid4())
        
        # Create the status data
        status_data = {
            "uuid": new_uuid,
            "name": name,
            "status": 0
        }
        
        # Insert the status into the database
        insert_uuid(status_data)
        
        return {"msg": "Status added successfully", "uuid": new_uuid}, 201
    
    except Exception as e:
        return {"msg": f"Error adding status: {str(e)}"}, 500
    
def check_and_update_agent_status():
    try:
        agents = list(get_agents())
        current_time = datetime.now()

        for agent in agents:
            last_handshake = agent.get("last_handshake")
            if last_handshake:
                last_handshake_time = datetime.fromtimestamp(last_handshake)
                if (current_time - last_handshake_time) > timedelta(minutes=5):
                    # Update agent status to 0 (Unreachable)
                    agent["status"] = 0
                    update_agents(agent)  # Update the agent in the database
    except Exception as e:
        print(f"Error updating agent status: {e}")

def delete_agent(agent_uuid: str):
    """Delete agent and all associated data"""
    try:
        # Delete from database
        result = delete_agent_by_uuid(agent_uuid)
        if isinstance(result, Exception):
            raise result
            
        # Delete PGP keys
        delete_agent_pgp_keys(agent_uuid)
        
        return {"msg": "Agent deleted successfully"}, 200
    except Exception as e:
        return {"msg": f"Error deleting agent: {str(e)}"}, 500