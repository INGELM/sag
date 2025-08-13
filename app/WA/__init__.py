from flask import Blueprint

wa_bp = Blueprint('wa', __name__)

from . import routes