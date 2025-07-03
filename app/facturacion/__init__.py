from flask import Blueprint

facturacion_bp = Blueprint('facturacion', __name__, template_folder='templates/facturacion', static_folder='static')

from . import routes  # Import routes to register them with the blueprint
