from flask import Blueprint

bp = Blueprint('consultations', __name__, template_folder='templates')

from . import routes, models