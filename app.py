from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
from logger import setup_logger
import os

# Initialize SQLAlchemy instance
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Setup logging
    setup_logger(app)
    
    # Register blueprints
    from modules.billing import billing_bp
    from modules.inventory import inventory_bp
    from modules.vendor import vendor_bp
    from modules.hotel.room_service import room_service_bp
    from modules.hotel.laundry import laundry_bp
    
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(vendor_bp, url_prefix='/vendor')
    app.register_blueprint(room_service_bp, url_prefix='/hotel/room-service')
    app.register_blueprint(laundry_bp, url_prefix='/hotel/laundry')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f'Page not found: {error}')
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        return render_template('errors/500.html'), 500
        
    # Create database tables
    with app.app_context():
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000)