from flask import Blueprint

login_bp = Blueprint('login', __name__, template_folder='templates/login', static_folder='static')

from . import routes  # Import routes to register them with the blueprint
