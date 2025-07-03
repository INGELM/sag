from flask import Blueprint

empleados_bp = Blueprint('empleados', __name__, template_folder='templates/empleados', static_folder='static')

from . import routes  # Import routes to register them with the blueprint
