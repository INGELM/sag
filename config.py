import os
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env

# Obtén las partes separadas de la conexión
db_host = os.getenv('DB_HOST', 'globalst.com.ve')
db_user = os.getenv('DB_USER', 'globalstweb')
db_password = os.getenv('DB_PASSWORD', 'ib2;rQ55Dp:P0S')
db_name = os.getenv('DB_NAME', 'globalstweb_sag')

# Codifica la contraseña
# encoded_password = quote(db_password)
encoded_password = db_password

# Construye la cadena de conexión


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', '$2a$12$jtoF3Txp11ljagYvW1oorO5U9mPUhW/rl7R6j.fS4jkAg.So.TCpG')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://globalstweb:ib2;rQ55Dp:P0S@globalst.com.ve/globalstweb_sag')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    DEBUG = True
    PROPAGATE_EXCEPTIONS = True
    PYTHONIOENCODING = 'utf-8'
    CONECTADO_A = os.environ.get('CONECTADO_A', 'produccion')
    #CONFIGURACION WHATSAPP
    
    WTF_CSRF_TIME_LIMIT = 3600 * 24   # Deshabilitar el tiempo de expiración del token CSRF
    
    PHONE_ID = os.environ.get('PHONE_ID')
    TOKEN = os.environ.get('TOKEN')