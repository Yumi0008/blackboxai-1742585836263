from flask import Blueprint

vendor_bp = Blueprint('vendor', __name__,
                     template_folder='templates',
                     static_folder='static',
                     static_url_path='/vendor/static')

from . import routes, models

# Import routes after Blueprint creation to avoid circular imports
from .routes import *