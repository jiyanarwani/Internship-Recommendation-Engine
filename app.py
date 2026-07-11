import os
from flask import Flask
from config import Config
from models import db

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.candidate_routes import candidate_bp
    from routes.admin_routes import admin_bp
    from routes.main_routes import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(candidate_bp, url_prefix='/api/candidate')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(main_bp)  # Root prefix
    
    # Create tables
    with app.app_context():
        db.create_all()
        from models import Internship
        if Internship.query.first() is None:
            print("Database is empty. Auto-seeding default opportunities...")
            try:
                from seed import perform_seed
                perform_seed()
            except Exception as e:
                print(f"Failed to auto-seed database: {e}")
        
    return app

if __name__ == '__main__':
    app = create_app()
    # Runs on port 5000 in debug mode
    app.run(host='0.0.0.0', port=5000, debug=True)
