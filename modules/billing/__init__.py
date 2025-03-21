from flask import Blueprint

billing_bp = Blueprint('billing', __name__, 
                      template_folder='templates',
                      static_folder='static',
                      static_url_path='/billing/static')

from . import routes, models

# Import routes after Blueprint creation to avoid circular imports
from .routes import *