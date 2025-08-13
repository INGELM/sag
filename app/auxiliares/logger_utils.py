import logging

# Crear un logger independiente
logger = logging.getLogger('wa_app')
logger.setLevel(logging.DEBUG)

# Configurar formato
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configurar handler para consola
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

def get_logger():
    """Devuelve el logger configurado"""
    return logger