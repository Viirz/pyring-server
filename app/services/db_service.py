from pymongo import MongoClient
import datetime
import os

# Connection setup
client = MongoClient('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/')
db = client[os.environ['MONGODB_DATABASE']] 

def uuid_exists(uuid: str) -> bool:
    try:
        return db.agents.find_one({"uuid": uuid}) is not None
    except Exception as e:
        return False
    
def update_agents(data: dict):
    try:
        if not uuid_exists(data["uuid"]):
            raise Exception("UUID not found")
        
        objectId = db.agents.find_one({"uuid": data["uuid"]})["_id"]
        db.agents.update_one(
            {"_id": objectId}, 
            {"$set": data})
        
    except Exception as e:
        return e

def insert_logs(data: dict):
    try:
        if not uuid_exists(data["uuid"]):
            raise Exception("UUID not found")
        
        db.logs.insert_one(data)
    except Exception as e:
        return e
    
def insert_uuid(data: dict):
    try:
        db.agents.insert_one(data)
    except Exception as e:
        return e

def get_agents() -> dict:
    try:
        return db.agents.find()
    except Exception as e:
        return e
    
def get_agents_by_uuid(uuid: str) -> dict:
    try:
        agent = db.agents.find_one({"uuid": uuid})
        return agent
    except Exception as e:
        return e

def get_logs_by_uuid(uuid: str) -> dict:
    try:
        log = db.logs.find_one({"uuid": uuid})
        return log
    except Exception as e:
        return e

def get_user() -> dict:
    try:
        return db.users.find()
    except Exception as e:
        return e
    
def get_user_by_email(email: str) -> dict:
    try:
        user = db.users.find_one({"email": email})
        return user
    except Exception as e:
        return e

def change_password(email: str, new_password: str):
    try:
        db.users.update_one(
            {"email": email}, 
            {"$set": {"password": new_password}})
    except Exception as e:
        return e

def add_user(user_data: dict):
    try:
        db.users.insert_one(user_data)
    except Exception as e:
        return e
    
def insert_command(data: dict):
    try:
        db.commands.insert_one(data)
    except Exception as e:
        return e

def get_commands_by_uuid(uuid: str):
    try:
        commands = db.commands.find({"uuid": uuid})  # Find a single document
        if commands:
            return commands
        else:
            raise Exception("Command not found or invalid document structure")
    except Exception as e:
        return e
    
def get_unretrieved_commands_by_uuid(uuid: str):
    try:
        commands = db.commands.find({"uuid": uuid, "retrieved": False}).to_list()
        db.commands.update_many({"uuid": uuid, "retrieved": False}, {"$set": {"retrieved": True}})
        if commands:
            return commands
        else:
            raise Exception("Command not found or invalid document structure")
    except Exception as e:
        return e
    
def update_command_response(uuid: str, command_id: str, response: str):
    try:
        if not uuid_exists(uuid):
            raise Exception("UUID not found")
        
        objectId = db.commands.find_one({"command_id": command_id})["_id"]
        db.commands.update_one(
            {"_id": objectId}, 
            {"$set": {"response": response}})
        
    except Exception as e:
        return e

def get_top_commands_by_uuid(uuid: str, limit: int = 5):
    try:
        # Query the top `limit` commands sorted by timestamp in descending order
        commands = db.commands.find({"uuid": uuid}).sort("timestamp", -1).limit(limit)
        return list(commands)
    except Exception as e:
        return e

def add_blacklisted_token(token: str, expiration_time: datetime):
    try:
        db.blacklist_jwt.insert_one({"token": token, "exp_time": expiration_time})
    except Exception as e:
        return e

def get_blacklisted_token(token: str) -> dict:
    try:
        return db.blacklist_jwt.find_one({"token": token})
    except Exception as e:
        return e

def remove_expired_blacklisted_tokens():
    try:
        now = datetime.now()
        db.blacklist_jwt.delete_many({"exp_time": {"$lt": now}})
    except Exception as e:
        return e

def delete_agent_by_uuid(uuid: str):
    try:
        if not uuid_exists(uuid):
            raise Exception("UUID not found")
        
        # Delete agent from agents collection
        db.agents.delete_one({"uuid": uuid})
        
        # Delete all commands for this agent
        db.commands.delete_many({"uuid": uuid})
        
        # Delete all logs for this agent
        db.logs.delete_many({"uuid": uuid})
        
        return True
    except Exception as e:
        return e