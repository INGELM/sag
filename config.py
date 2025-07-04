import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '$2a$12$EuLRBS0CW4zeJjGKK6zEPeC/cwuCG71/qWfV42fnlZSNMyzs/YD5u'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://globalstweb:globalst062022@localhost/globalstweb_sag'  
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    DEBUG = False
    PROPAGATE_EXCEPTIONS = True
    PYTHONIOENCODING = 'utf-8'