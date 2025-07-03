from flask import Blueprint

clientes_bp = Blueprint('clientes', __name__, template_folder='templates/clientes', static_folder='static', static_url_path='/static/clientes')

from . import routes  # Import routes to register them with the blueprint

