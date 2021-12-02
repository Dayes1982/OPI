# -*- coding: utf-8 -*-
import os
from flask import render_template, redirect, url_for, request, json, jsonify
from flask.helpers import send_file
from app import app, db, admin
from .forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from functools import wraps
from app.models import Usuarios, Software, Material, Archivo, Categoria, Subcategoria, Anio, Permisos #, Mes
from sqlalchemy import asc, desc
from werkzeug.urls import url_parse
from app.forms import RegistrationForm, SoftwareForm, ArchivosForm, SubcategoriaForm, PermisosForm, DescargaArchivosForm
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose
from werkzeug.utils import secure_filename
from flask_admin.menu import MenuLink


# Manejo de archivos
path = os.path.join(os.path.dirname(__file__), 'static/files')
SOFT_DIR = os.path.join(os.path.dirname(__file__), 'static/software')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'static/datos')

########## Personalización de la vista de administrador #################
class MyModelViewUsuarios(ModelView):
    can_export = True
    can_create = False
    column_searchable_list = ['nombre']
    column_exclude_list = ['password']
    def is_accessible(self):
        return current_user.administrador

class MyModelViewMaterial(ModelView):
    can_export = True
    can_create = True
    column_searchable_list = ['tip_Usuario','numero_Serie']
    def is_accessible(self):
        return current_user.administrador

class MyModelViewSoftware(ModelView):
    can_edit = False
    column_searchable_list = ['nombre']
    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = SoftwareForm()
        if form.validate_on_submit():
            soft = Software(nombre=form.nombre.data, descripcion=form.descripcion.data)
            file = request.files['programa']
            soft.programa = secure_filename(file.filename)
            programa = Software.query.filter_by(programa=soft.programa).first()
            if programa is not None:
                return self.render('admin/templates/create_software.html',form=form, mensaje="Ya existe un programa con el mismo archivo.")
            db.session.add(soft)
            db.session.commit()
            os.makedirs(SOFT_DIR, exist_ok=True)
            file_path = os.path.join(SOFT_DIR, soft.programa)
            file.save(file_path)
            form.nombre.data = ""
            form.descripcion.data = ""
            return self.render('admin/templates/create_software.html',form=form, mensaje="Software dado de alta correctamente.")
        return self.render('admin/templates/create_software.html',form=form)
    
    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            os.remove(os.path.join(SOFT_DIR, model.programa))
            self.session.flush()
            self.session.delete(model)
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')
            self.session.rollback()
            return False
        else:
            self.after_model_delete(model)
        return True

class AnioView(ModelView):
    can_edit = False
class CategoriaView(ModelView):
    page_size = 50

class SubcategoriaView(ModelView):
    page_size = 50
    column_list = ('categoria', 'nombre')
    can_edit = False
    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = SubcategoriaForm()
        form.categoria.choices = [(g.nombre) for g in Categoria.query.order_by(Categoria.nombre.asc())]
        if form.validate_on_submit():
            sub = Subcategoria(categoria=form.categoria.data, nombre=form.nombre.data)
            db.session.add(sub)
            db.session.commit()
            return self.render('admin/templates/subcategorias.html',form=form, mensaje="Subcategoria dada de alta correctamente.")
        return self.render('admin/templates/subcategorias.html',form=form)
        
class ArchivosView(ModelView):
    can_edit = False
    column_searchable_list = ['nombre']
    #column_list = ('categoria','subcategoria','anio','mes','nombre')
    column_list = ('categoria','subcategoria','anio','nombre')
    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = ArchivosForm()
        #form.mes.choices = [(g.numero, g.nombre) for g in Mes.query.order_by(Mes.numero.asc())]
        form.anio.choices = [(str(g.numero)) for g in Anio.query.order_by(Anio.numero.desc())]
        form.categoria.choices = [(g.nombre) for g in Categoria.query.order_by(Categoria.nombre.asc())]
        form.categoria.choices.insert(0,(""))
        form.subcategoria.choices = [(g.nombre) for g in Subcategoria.query.order_by(Subcategoria.nombre.asc())]
        form.subcategoria.choices.insert(0,(""))
        subcategorias = [(g.categoria , g.nombre) for g in Subcategoria.query.order_by(Subcategoria.nombre.asc())]
        if form.validate_on_submit():
            #soft = Archivo(categoria=form.categoria.data, subcategoria=form.subcategoria.data, mes=form.mes.data,anio=form.anio.data)
            soft = Archivo(categoria=form.categoria.data, subcategoria=form.subcategoria.data, anio=form.anio.data)
            file = request.files['nombre']
            soft.nombre = secure_filename(file.filename)
            programa = Archivo.query.filter_by(nombre=soft.nombre ).first()
            if programa is not None:
                return self.render('admin/templates/create_files.html',form=form, mensaje="Ya existe un archivo con el mismo nombre.")
            db.session.add(soft)
            db.session.commit()
            os.makedirs(DATA_DIR, exist_ok=True)
            file_path = os.path.join(DATA_DIR, soft.nombre)
            file.save(file_path)

            form.categoria.data = ""
            form.subcategoria.data = ""
            #form.mes.data = ""
            form.anio.data = ""
            return self.render('admin/templates/create_files.html',form=form, subcategorias=subcategorias,mensaje="Archivo dado de alta correctamente.")
        return self.render('admin/templates/create_files.html',subcategorias=subcategorias,form=form)
    
    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            os.remove(os.path.join(DATA_DIR, model.nombre))
            self.session.flush()
            self.session.delete(model)
            self.session.commit()
        except Exception:
            self.session.rollback()
            return False
        else:
            self.after_model_delete(model)
        return True

class PermisosView(ModelView):
    can_edit = False
    column_searchable_list = ['Usuario']
    column_list = ('Usuario', 'Categoria')
    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self):
        form = PermisosForm()
        form.nombreUser.choices = [(g.nombre) for g in Usuarios.query.order_by(Usuarios.nombre.asc())]
        form.nomCategoria.choices = [(g.nombre) for g in Categoria.query.order_by(Categoria.nombre.asc())]
        if form.validate_on_submit():
            per = Permisos(Usuario=form.nombreUser.data, Categoria=form.nomCategoria.data)
            db.session.add(per)
            db.session.commit()
            return self.render('admin/templates/permisos.html',form=form, mensaje="Permiso: " + form.nombreUser.data + " a " + form.nomCategoria.data + " concedido correctamente.")
        return self.render('admin/templates/permisos.html',form=form)

admin.add_view(MyModelViewUsuarios(Usuarios, db.session))
admin.add_view(MyModelViewSoftware(Software, db.session))
admin.add_view(MyModelViewMaterial(Material, db.session))
admin.add_view(AnioView(Anio, db.session))
admin.add_view(CategoriaView(Categoria, db.session))
admin.add_view(SubcategoriaView(Subcategoria, db.session))
admin.add_view(PermisosView(Permisos, db.session))
admin.add_view(ArchivosView(Archivo, db.session))
admin.add_link(MenuLink(name='Salir Administración', url='/'))


######## VISTAS ##############

@app.route('/') 
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('menu'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuarios.query.filter_by(nombre=form.nombre.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Usuarios(nombre=form.nombre.data, administrador=False, activo=False, accesoSoftware=False, accesoMaterial=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return render_template('confirme.html')
    return render_template('register.html', title='Register', form=form)

# Función para comprobar si tiene acceso a algunas páginas (Tiene que estar confirmado por un Admin)
def check_confirmed(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.activo == False:
            return redirect(url_for('confirme'))
        return func(*args, **kwargs)
    return decorated_function

# Muestra que falta estar confirmado
@app.route('/confirme')
@login_required
def confirme():
    if current_user.activo == True:
        return redirect('login')
    return render_template('confirme.html')
    
@app.route('/menu', methods=['POST', 'GET'])
@login_required
@check_confirmed
def menu():
    # Permisos para los archivos.
    if current_user.accesoMaterial == True:
        #material = Material.query.order_by(Material.tip_Usuario).all()
        material = Material.query.filter_by(tip_Usuario=current_user.nombre).all()
    else:
        material = ""
    if current_user.accesoSoftware == True:
        software = Software.query.order_by(Software.nombre).all()
    else:
        software=""
    permisoCat = Permisos.query.filter_by(Usuario=current_user.nombre).all()
    form = DescargaArchivosForm()
    #form.mes.choices = [(g.numero, g.nombre) for g in Mes.query.order_by(Mes.numero.asc())]
    form.anio.choices = [(str(g.numero)) for g in Anio.query.order_by(Anio.numero.desc())]
    form.categoria.choices = [(g.Categoria) for g in Permisos.query.filter_by(Usuario=current_user.nombre).order_by(Permisos.Categoria.asc())]
    if len(form.categoria.choices) > 0:
        form.subcategoria.choices = [(g.nombre) for g in Subcategoria.query.filter_by(categoria=form.categoria.choices[0]).order_by(Subcategoria.nombre.asc())]
    if form.validate_on_submit():
        # Servir archivo
        #archivo = Archivo.query.filter_by(mes=form.mes.data, anio=form.anio.data, categoria=form.categoria.data,subcategoria=form.subcategoria.data).first()
        archivo = Archivo.query.filter_by(anio=form.anio.data, categoria=form.categoria.data,subcategoria=form.subcategoria.data).first()
        print(archivo)
        if archivo is None:
            mensaje="El archivo no existe"
            return render_template("menu.html", title='Home Page', material=material, software=software,permisoCat=permisoCat, form=form, mensaje=mensaje)
        else:
            file_path = os.path.join(DATA_DIR, archivo.nombre)
            return send_file(file_path)
    return render_template("menu.html", title='Home Page', material=material, software=software,permisoCat=permisoCat, form=form)


@app.route('/updateSubcategoria', methods=['POST'])
def updateselect():
    cat = request.form.get('categoria')
    choices = [(g.nombre) for g in Subcategoria.query.filter_by(categoria=cat).order_by(Subcategoria.nombre.asc())]
    return jsonify(choices)
