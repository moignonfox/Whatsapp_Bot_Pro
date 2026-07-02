from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Import des routes pour les enregistrer sur le blueprint
from . import auth
from . import orders
from . import chat
from . import stats
from . import catalog
from . import devices
