import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(app):
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Set up file handler
    file_handler = RotatingFileHandler(
        'logs/management_system.log',
        maxBytes=10240,
        backupCount=10
    )
    
    # Set logging format
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # Set logging level
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # Set general logging level
    app.logger.setLevel(logging.INFO)
    app.logger.info('Management System startup')
    
    return app.logger

def get_module_logger(module_name):
    """Get a logger instance for a specific module"""
    logger = logging.getLogger(module_name)
    
    if not logger.handlers:
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
    
    return logger