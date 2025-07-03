from flask import Blueprint

ciudades_bp = Blueprint('ciudades', __name__, template_folder='templates/auxiliares', static_folder='static', static_url_path='/static/auxiliares')

vehiculos_bp = Blueprint('vehiculos', __name__, template_folder='templates/auxiliares', static_folder='static', static_url_path='/static/auxiliares')

tasa_bp = Blueprint('tasa', __name__, template_folder='templates/auxiliares', static_folder='static', static_url_path='/static/auxiliares')

from . import routes  # Import routes to register them with the blueprint
