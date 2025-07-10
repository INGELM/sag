from flask import render_template,redirect, url_for, flash
from . import login_bp
from .form import *
from datetime import datetime
from flask_login import login_user, current_user, logout_user
from app.empleados.models import empleadosModel
from flask import session
from flask import current_app




@login_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return render_template('./base/dashboard_base.html', year=datetime.now().year, User=current_user)
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        empleado = empleadosModel.query.filter_by(usuario=username).first()
        
        if empleado and empleado.rol == 'Operador':
            flash('Usuario no autorizado. Por favor, contacte al administrador.', 'warning')
            return render_template('login.html', form=form, year=datetime.now().year)

        if empleado and empleado.contrasena and empleado.check_password(password):
            current_app.logger.debug(f'Empleado encontrado: {empleado.usuario}')
            login_user(empleado, remember=form.remember.data)
            
            if hasattr(empleado, 'rol') and empleado.rol == 'admin':
                session['admin'] = True
            else:
                session['admin'] = False
            
            return redirect(url_for('login.inicio'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            if not form.username.data:
                form.username.errors.append('Por favor, complete el campo de usuario')
            if not form.password.data:
                form.password.errors.append('Por favor, complete el campo de contraseña')
    else:
        if form.username.errors:
            form.username.errors.append('Por favor, complete el campo de usuario')
        if form.password.errors:
            form.password.errors.append('Por favor, complete el campo de contraseña')

    return render_template('login.html', form=form, year=datetime.now().year)

@login_bp.route('/logout')
def logout():
    logout_user()
    session.pop('admin', None)
    return redirect(url_for('login.login'))

@login_bp.route('/inicio', methods=['GET', 'POST'])
def inicio():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    return render_template('index.html', year=datetime.now().year, User = current_user)
