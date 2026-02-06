# app/wa/__init__.py

from flask import Blueprint
from pywa import WhatsApp
import httpx


wa_bp = Blueprint('wa', __name__)

wa = None


def init_wa(app):
    global wa
    wa = WhatsApp(
        phone_id='878549852019408',
        token='EAAUpKttiF0cBQpHhRS0o8I7Hp0qmYw4AIxqlZBaWZBxMouQWxvYkSp0SjKZBmgwu7UzjeMjci2V58VGTYuJVZB9D4ZBpZAWf2mrIXo5jZBOn0j52NsIGn4eGBEPjEGle8XKkH1jgbZBR5HYqwTOSJZCtLwnRSV08dNj6oBFeviPwffZAfgZAFipybRMqOzXzlWsP5bSIzACEOamy4ZALGvXUlXhhoZAOZB6Ri4WljGwwllRFoG',
        # server='https://graph.facebook.com/v24.0',
        server=app,
        webhook_endpoint='/wa/webhook',
        # callback_url='https://sagglobal.share.zrok.io',
        verify_token='7R6j.fZAMZCVjVe2ZA5',
        app_id='1452638929557319',
        app_secret="482da5a0ef3f2a92c1e96dfe8efdc21d",
        webhook_challenge_delay=500
        
    )
    from .routes import register_wa_handlers
    register_wa_handlers(wa)
    return wa


from . import routes