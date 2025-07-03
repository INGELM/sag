from flask import Blueprint

programacion_bp = Blueprint('programacion', __name__, template_folder='templates/programacion', static_folder='static', static_url_path='/static/programacion')

from . import routes  # Import routes to register them with the blueprint

