from flask import Flask, redirect, url_for
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_admin import Admin, AdminIndexView, expose

# export FLASK_ENV=development

# pip3 install gunicorn Flask
# gunicorn --workers=2 --bind=0.0.0.0:8000 app:app 
app = Flask(__name__)
app.config.update(dict(
    DEBUG = True,
))

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

class MyView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_admin:
            return redirect(url_for('login'))
        else:
            return self.render('admin/index.html')

admin = Admin(app,name='OPI RRHH',index_view=MyView())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)

from app import views, models, errors
