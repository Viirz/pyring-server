from flask import Blueprint, jsonify, request
from app.services.db_service import get_telegram_settings, update_telegram_settings, get_user_by_email
from app.utils.jwt_utils import verify_jwt
from app.utils.telegram_utils import test_telegram_connection
from app.utils.logging_utils import log_request_blueprint, log_response_blueprint
import logging

telegram_api_bp = Blueprint('telegram_api', __name__, url_prefix='/api/telegram')
logger = logging.getLogger('pyring.api.telegram')

@telegram_api_bp.before_request
def log_api_request():
    log_request_blueprint('pyring.api')

@telegram_api_bp.after_request
def log_api_response(response):
    return log_response_blueprint(response, 'pyring.api')

@telegram_api_bp.before_request
def token_required():
    token = request.cookies.get('token')  # Get JWT token from cookies
    if not token or not verify_jwt(token):  # Verify JWT token
        return jsonify({"msg": "Unauthorized"}), 401

@telegram_api_bp.route('/settings', methods=['GET'])
def get_settings():
    try:
        settings = get_telegram_settings()
        if not settings:
            # Return default settings if none exist
            settings = {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            }
        
        # Don't send the full bot token to frontend for security
        if settings.get("bot_token"):
            settings["bot_token"] = "***CONFIGURED***"
        
        return jsonify(settings), 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500

@telegram_api_bp.route('/settings', methods=['POST'])
def update_settings():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided"}), 400

        enabled = data.get("enabled", False)
        bot_token = data.get("bot_token", "").strip()
        chat_id = data.get("chat_id", "").strip()
        
        # Only validate required fields if enabling notifications
        if enabled and (not bot_token or not chat_id):
            return jsonify({"msg": "Bot token and chat ID are required when enabling notifications"}), 400
        
        # If bot_token is the masked value, get the real token from database
        if bot_token == "***CONFIGURED***":
            current_settings = get_telegram_settings()
            if current_settings and current_settings.get("bot_token"):
                bot_token = current_settings["bot_token"]
            else:
                return jsonify({"msg": "No bot token configured"}), 400
        
        # If disabling, preserve existing credentials
        if not enabled:
            current_settings = get_telegram_settings()
            if current_settings:
                # Keep existing credentials when disabling
                if not bot_token or bot_token == "***CONFIGURED***":
                    bot_token = current_settings.get("bot_token", "")
                if not chat_id:
                    chat_id = current_settings.get("chat_id", "")
        
        settings_data = {
            "enabled": enabled,
            "bot_token": bot_token,
            "chat_id": chat_id
        }
        
        result = update_telegram_settings(settings_data)
        if isinstance(result, Exception):
            raise result
        
        return jsonify({"msg": "Settings updated successfully"}), 200
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500

@telegram_api_bp.route('/test', methods=['POST'])
def test_connection():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"msg": "No data provided"}), 400

        bot_token = data.get("bot_token", "").strip()
        chat_id = data.get("chat_id", "").strip()
        thread_id = data.get("thread_id", "").strip()  # Optional
        
        if not bot_token or not chat_id:
            return jsonify({"msg": "Bot token and chat ID are required"}), 400
        
        # If bot_token is the masked value, get the real token from database
        if bot_token == "***CONFIGURED***":
            current_settings = get_telegram_settings()
            if current_settings and current_settings.get("bot_token"):
                bot_token = current_settings["bot_token"]
            else:
                return jsonify({"msg": "No bot token configured"}), 400
        
        # Pass thread_id to test function (None if empty)
        result = test_telegram_connection(bot_token, chat_id, thread_id if thread_id else None)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"msg": f"Something went wrong: {e}"}), 500