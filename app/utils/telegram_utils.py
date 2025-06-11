import requests
import json
from app.services.db_service import get_telegram_settings

def send_telegram_notification(agent_name, agent_uuid, old_status, new_status):
    """Send Telegram notification when agent status changes"""
    try:
        # Get Telegram settings from database
        settings = get_telegram_settings()
        if not settings or not settings.get('enabled', False):
            return  # Notifications disabled
        
        bot_token = settings.get('bot_token')
        chat_id = settings.get('chat_id')
        
        if not bot_token or not chat_id:
            print("Telegram bot token or chat ID not configured", flush=True)
            return
        
        # Create status message templates
        status_messages = {
            0: "🔴 DISCONNECTED",
            1: "🟢 ONLINE", 
            2: "🟡 RECOVERY"
        }
        
        old_status_text = status_messages.get(old_status, f"Unknown ({old_status})")
        new_status_text = status_messages.get(new_status, f"Unknown ({new_status})")
        
        # Create message
        message = f"""
🚨 **Agent Status Change Alert**

**Agent:** `{agent_name}`
**UUID:** `{agent_uuid}`
**Status Change:** {old_status_text} → {new_status_text}
**Time:** {get_current_time()}

---
*PyRing Server Monitoring*
        """.strip()
        
        # Send message to Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"Telegram notification sent for agent {agent_name}", flush=True)
        else:
            print(f"Failed to send Telegram notification: {response.text}", flush=True)
            
    except Exception as e:
        print(f"Error sending Telegram notification: {e}", flush=True)

def get_current_time():
    """Get current time formatted for notifications"""
    from datetime import datetime
    return datetime.now().strftime('%d/%m/%Y - %H:%M:%S')

def test_telegram_connection(bot_token, chat_id):
    """Test Telegram bot connection"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': '🔧 **PyRing Server Test**\n\nTelegram notifications are working correctly!',
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "message": "Test message sent successfully!"}
        else:
            return {"success": False, "message": f"Failed to send message: {response.text}"}
            
    except Exception as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}