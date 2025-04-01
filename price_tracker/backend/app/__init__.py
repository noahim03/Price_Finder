from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os

# Initialize SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class='config.Config'):
    # Create and configure the app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize plugins
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS for frontend requests
    CORS(app)
    
    # Initialize database
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from app import models
        
        # Create tables if they don't exist
        db.create_all()
        
        # Check if the database has already been populated
        if models.Product.query.count() == 0:
            print("Creating initial database entries...")
            
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app 