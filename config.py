import os
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()  # Carga las variables del archivo .env

# Obtén las partes separadas de la conexión
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')

# Codifica la contraseña
# encoded_password = quote(db_password)
encoded_password = db_password

# Construye la cadena de conexión


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}/{db_name}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    DEBUG = False
    TESTING = False
    PROPAGATE_EXCEPTIONS = True
    PYTHONIOENCODING = 'utf-8'
    CONECTADO_A = os.environ.get('CONECTADO_A', 'produccion')
    #CONFIGURACION WHATSAPP
    
    WTF_CSRF_TIME_LIMIT = 3600 * 24   # Deshabilitar el tiempo de expiración del token CSRF
    
    PHONE_ID = os.environ.get('PHONE_ID')
    TOKEN = os.environ.get('TOKEN')