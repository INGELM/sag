# passenger_wsgi.py

import sys
import codecs
import os

# Aseguramos que stdout y stderr usen UTF-8
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Agregamos el directorio actual al path
sys.path.append(os.getcwd())

# Importamos la app Flask desde tu archivo principal
from run import app as application