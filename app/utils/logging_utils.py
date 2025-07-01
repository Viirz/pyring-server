import logging
import json
import time
from datetime import datetime
from flask import request, g
import os

# Configure logging
def setup_logging():
    """Setup application logging configuration"""
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Create logs directory if it doesn't exist
    os.makedirs('/var/www/app/logs', exist_ok=True)
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler for main app logs
    app_handler = logging.FileHandler('/var/www/app/logs/app.log')
    app_handler.setLevel(getattr(logging, log_level))
    app_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler for web endpoint logs
    web_handler = logging.FileHandler('/var/www/app/logs/web_endpoint.log')
    web_handler.setLevel(logging.INFO)
    web_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler for web API endpoint logs
    web_api_handler = logging.FileHandler('/var/www/app/logs/web_api_endpoint.log')
    web_api_handler.setLevel(logging.INFO)
    web_api_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler for agent endpoint logs
    agent_handler = logging.FileHandler('/var/www/app/logs/agent_endpoint.log')
    agent_handler.setLevel(logging.INFO)
    agent_handler.setFormatter(logging.Formatter(log_format))
    
    # Setup main app logger
    app_logger = logging.getLogger('pyring')
    app_logger.setLevel(getattr(logging, log_level))
    app_logger.addHandler(app_handler)
    
    # Setup web endpoint logger
    web_logger = logging.getLogger('pyring.web')
    web_logger.setLevel(logging.INFO)
    web_logger.addHandler(web_handler)
    web_logger.propagate = False  # Prevent propagation to parent logger
    
    # Setup web API endpoint logger
    web_api_logger = logging.getLogger('pyring.api')
    web_api_logger.setLevel(logging.INFO)
    web_api_logger.addHandler(web_api_handler)
    web_api_logger.propagate = False  # Prevent propagation to parent logger
    
    # Setup agent endpoint logger
    agent_logger = logging.getLogger('pyring.agent')
    agent_logger.setLevel(logging.INFO)
    agent_logger.addHandler(agent_handler)
    agent_logger.propagate = False  # Prevent propagation to parent logger
    
    return app_logger

def get_client_ip():
    """Get the real client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def get_user_agent():
    """Get user agent from request"""
    return request.headers.get('User-Agent', 'Unknown')

def sanitize_data_for_logging(data):
    """Remove sensitive information from data before logging"""
    if not isinstance(data, dict):
        return data
    
    # Only password-related fields are sensitive
    sensitive_fields = ['password', 'old_password', 'new_password', 'repeat_password']
    sanitized = data.copy()
    
    for field in sensitive_fields:
        if field in sanitized:
            sanitized[field] = '***REDACTED***'
    
    return sanitized

def log_request_blueprint(logger_name):
    """Log incoming request details for a specific blueprint"""
    g.start_time = time.time()
    
    # Get request data safely
    request_data = None
    if request.content_type and 'application/json' in request.content_type:
        try:
            request_data = request.get_json(silent=True)
            if request_data:
                request_data = sanitize_data_for_logging(request_data)
        except Exception:
            request_data = "Failed to parse JSON"
    
    # Prepare log data with all headers
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'method': request.method,
        'path': request.path,
        'endpoint': request.endpoint,
        'client_ip': get_client_ip(),
        'user_agent': get_user_agent(),
        'content_type': request.content_type,
        'content_length': request.content_length,
        'headers': dict(request.headers),  # Include all headers
        'request_data': request_data
    }
    
    logger = logging.getLogger(logger_name)
    logger.info(f"REQUEST: {json.dumps(log_data, default=str)}")

def log_response_blueprint(response, logger_name):
    """Log response details for a specific blueprint"""
    # Calculate response time
    response_time = None
    if hasattr(g, 'start_time'):
        response_time = round((time.time() - g.start_time) * 1000, 2)  # in milliseconds
    
    # Get response data safely
    response_data = None
    if response.content_type and 'application/json' in response.content_type:
        try:
            response_data = response.get_json(silent=True)
            if response_data:
                response_data = sanitize_data_for_logging(response_data)
        except Exception:
            response_data = "Failed to parse JSON response"
    
    # Prepare log data
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'method': request.method,
        'path': request.path,
        'endpoint': request.endpoint,
        'status_code': response.status_code,
        'status': response.status,
        'response_time_ms': response_time,
        'content_type': response.content_type,
        'content_length': response.content_length,
        'client_ip': get_client_ip(),
        'response_data': response_data
    }
    
    logger = logging.getLogger(logger_name)
    
    # Log level based on status code
    if response.status_code >= 500:
        logger.error(f"RESPONSE: {json.dumps(log_data, default=str)}")
    elif response.status_code >= 400:
        logger.warning(f"RESPONSE: {json.dumps(log_data, default=str)}")
    else:
        logger.info(f"RESPONSE: {json.dumps(log_data, default=str)}")
    
    return response

# Keep the original functions for backward compatibility
def log_request():
    """Log incoming request details (fallback for global usage)"""
    log_request_blueprint('pyring')

def log_response(response):
    """Log response details (fallback for global usage)"""
    return log_response_blueprint(response, 'pyring')