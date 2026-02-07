from logging.handlers import RotatingFileHandler
import os
import logging
import traceback
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user
# from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import HTTPException
from app.extensions import csrf


def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    csrf.init_app(app)
    app.config.from_object('config.Config')

    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login.login'  # Set the login view for Flask-Login
    login_manager.session_protection = 'strong'  # Optional: Set session protection level
    
    @login_manager.unauthorized_handler
    def unauthorized():
        if current_user.is_authenticated:
            flash('Tu sesión ha expirado por inactividad.', 'warning')
        else:
            flash('Por favor inicia sesión para acceder a esa página.','danger')
        return redirect(url_for('login.login'))
    
    @login_manager.user_loader
    def load_user(id):
        from .empleados.models import empleadosModel as User
        return User.query.get(int(id))

    from dotenv import load_dotenv
    load_dotenv()

    # Initialize extensions, blueprints, etc.
    from .extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
  
    
    #CONFIGURACIÓN DEL LOGGER (SOLO EN PRODUCCIÓN/MODO NO-DEBUG)
    if not app.debug:
        # Definir la ruta del archivo app.log en la raíz de la carpeta 'app'
        log_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs')
        
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        
        # RotatingFileHandler: 5MB por archivo, mantiene hasta 5 copias de seguridad
        file_handler = RotatingFileHandler(os.path.join(log_path, 'app.log'), maxBytes=5242880, backupCount=5, encoding='utf-8')
        
        # Formato: Fecha Hora | Nivel | Mensaje
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('=== SAG System Startup ===')
    
    from .login import login_bp
    app.register_blueprint(login_bp, url_prefix='/login')
    
    from .empleados import empleados_bp
    app.register_blueprint(empleados_bp, url_prefix='/empleados')
    
    from .clientes import clientes_bp
    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    
    from .auxiliares import ciudades_bp
    app.register_blueprint(ciudades_bp, url_prefix='/ciudades')
    
    from .auxiliares import vehiculos_bp
    app.register_blueprint(vehiculos_bp, url_prefix='/vehiculos')

    from .programacion import programacion_bp
    app.register_blueprint(programacion_bp, url_prefix='/programacion')
    
    from .facturacion import facturacion_bp
    app.register_blueprint(facturacion_bp, url_prefix='/facturacion')
    
    from .auxiliares import tasa_bp
    app.register_blueprint(tasa_bp, url_prefix='/tasa')
    
     
    from .wa import wa_bp, init_wa
    
    app.register_blueprint(wa_bp, url_prefix = '/wa' )
    init_wa(app)

    # Exime el endpoint real del webhook (registrado por pywa) del CSRF.
    webhook_exempted = False
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith('/wa/webhook'):
            csrf.exempt(app.view_functions[rule.endpoint])
            app.logger.info('CSRF exempted for webhook endpoint: %s -> %s', rule.rule, rule.endpoint)
            webhook_exempted = True

    if not webhook_exempted:
        app.logger.warning('No webhook endpoint found to exempt from CSRF.')
    
    
    
    #MANEJADORES DE ERRORES (ERROR HANDLERS)
    
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 Not Found: {request.url} | IP: {request.remote_addr}")
        return render_template('errors/404.html'), 404

    @app.errorhandler(Exception)
    def internal_error(error):
        # Captura el error y la traza completa (stack trace)
        error_details = traceback.format_exc()
        usuario_actual = current_user.usuario if current_user.is_authenticated else "Anonimo"
        
        # Registra el error detallado en el log
        app.logger.error(
            f"EXCEPCION DETECTADA!\n"
            f"Usuario: {usuario_actual}\n"
            f"URL: {request.url}\n"
            f"Metodo: {request.method}\n"
            f"Detalles:\n{error_details}"
        )
        
        # Opcional: Si es una base de datos, hacer rollback para evitar datos corruptos
        # db.session.rollback()
        
        return render_template('errors/500.html'), 500
    
    # with app.app_context():
    #     for rule in app.url_map.iter_rules():
    #         print(f"Endpoint: {rule.endpoint} | Ruta: {rule}")

    return app