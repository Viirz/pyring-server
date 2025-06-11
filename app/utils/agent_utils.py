from app.services.db_service import insert_uuid, get_agents, update_agents, delete_agent_by_uuid, get_agents_by_uuid
from app.utils.pgp_utils import delete_agent_pgp_keys
from app.utils.telegram_utils import send_telegram_notification
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

def update_agent_with_notification(agent_data):
    """Update agent and send notification if status changed"""
    try:
        agent_uuid = agent_data.get("uuid")
        new_status = agent_data.get("status")
        
        # Get current agent data to compare status
        current_agent = get_agents_by_uuid(agent_uuid)
        if not current_agent:
            raise Exception("Agent not found")
        
        old_status = current_agent.get("status")
        agent_name = current_agent.get("name", "Unknown")
        
        # Update the agent
        result = update_agents(agent_data)
        if isinstance(result, Exception):
            raise result
        
        # Send notification if status actually changed
        if old_status is not None and old_status != new_status:
            print(f"Agent {agent_name} status changed: {old_status} -> {new_status}", flush=True)
            send_telegram_notification(agent_name, agent_uuid, old_status, new_status)
        
        return True
    except Exception as e:
        print(f"Error updating agent with notification: {e}", flush=True)
        return e
    
def check_and_update_agent_status():
    try:
        agents = list(get_agents())
        current_time = datetime.now()

        for agent in agents:
            last_handshake = agent.get("last_handshake")
            if not last_handshake:
                continue
            
            last_handshake_time = datetime.fromtimestamp(last_handshake)
            if (current_time - last_handshake_time) <= timedelta(minutes=5):
                continue
            
            # Only update if status is not already 0
            if agent.get("status") == 0:
                continue
            
            agent["status"] = 0
            update_agent_with_notification(agent)
    
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