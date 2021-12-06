Aplicación web para la OPI.
Renovación de Calamar.
JDMG 12/2021.

###################### Requisitos #########################
Python 3
- Aconsejable EV
###########################################################

############### Instalación de dependencias ###############
pip install -r requerimientos.txt
pip install gunicorn Flask
###########################################################

############### Pasos para iniciar ########################
* Creación de la BBDD
    flask db init
    flask db migrate
    flask db upgrade
* Creación de datos iniciales de la BBDD
    python altaAdmin.py user pass
* Lanzar servicio
    - Para pruebas
        export FLASK_ENV=development
        flask run
    - Producción con Gunicorn (seleccionar un worker menos que nucleos del procesador)
        gunicorn --workers=2 --bind=0.0.0.0:8000 app:app
###########################################################