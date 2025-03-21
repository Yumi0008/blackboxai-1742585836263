from flask import Blueprint

inventory_bp = Blueprint('inventory', __name__,
                        template_folder='templates',
                        static_folder='static',
                        static_url_path='/inventory/static')

from . import routes, models

# Import routes after Blueprint creation to avoid circular imports
from .routes import *