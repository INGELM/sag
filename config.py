import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', '$2a$12$jtoF3Txp11ljagYvW1oorO5U9mPUhW/rl7R6j.fS4jkAg.So.TCpG')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://globalstweb:ib2;rQ55Dp:P0S@globalst.com.ve/globalstweb_sag')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    DEBUG = True
    PROPAGATE_EXCEPTIONS = True
    PYTHONIOENCODING = 'utf-8'
    
    #CONFIGURACION WHATSAPP
    
    PHONE_ID = os.environ.get('PHONE_ID')
    TOKEN = os.environ.get('TOKEN')