import os
import logging
from flask import Flask, flash, redirect, url_for
from flask_login import LoginManager, current_user



def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Configurar logging

        # Asegúrate de que la carpeta donde se guardará app.log sea escribible
    log_path = os.path.join(app.root_path, 'app.log')
    
    file_handler = logging.FileHandler(log_path)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - %(name)s - (' + app.name + ') - (' + app.logger.name + ') - [%(pathname)s:%(lineno)d]')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

    # Registrar errores no capturados
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f'Unhandled exception: {str(e)}', exc_info=True)
        return f'{"Error Interno del Servidor:"} {str(e)}, 500'

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
    
    from .WA import wa_bp
    app.register_blueprint(wa_bp, url_prefix = '/wa' )
    

    return app