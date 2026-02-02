from flask import Blueprint
from pywa import WhatsApp
import os

wa_bp = Blueprint('wa', __name__)

# wa = WhatsApp(
#     phone_id=os.environ.get("WA_PHONE_ID"),
#     token=os.environ.get("WA_TOKEN"),
#     app_id=os.environ.get("WA_APP_ID"),
#     app_secret=os.environ.get("WA_APP_SECRET"),    
#     verify_token=os.environ.get("WA_VERIFY_TOKEN"),
#     server=wa_bp, # Aquí le decimos a pywa que use el Blueprint como servidor
#     callback_url='/webhook', # La ruta final será /wa/webhook
#     webhook_challenge_delay=500, # Tiempo en ms para responder al desafío del webhook
    
    
    
# )





from . import routes