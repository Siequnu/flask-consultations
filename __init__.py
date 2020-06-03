from flask import Blueprint

bp = Blueprint('consultations', __name__, template_folder='templates', static_folder='static')

from . import routes, models