from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='template', static_folder='static')
    
    # Import and register blueprints
    from app.routes.agents_routes import agents_bp
    from app.routes.logs_routes import logs_bp
    from app.routes.web_routes import web_bp
    from app.routes.api.agents_api import agents_api_bp  
    from app.routes.api.users_api import users_api_bp
    
    app.register_blueprint(agents_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(agents_api_bp)
    app.register_blueprint(users_api_bp)
     
    return app