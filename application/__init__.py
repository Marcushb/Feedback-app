from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ngrok import run_with_ngrok
from application.config import secret_key, sqlalchemy_database_uri

# from flask_cors import CORS

application = Flask(__name__)
application.config['SECRET_KEY'] = secret_key
application.config['SQLALCHEMY_DATABASE_URI'] = sqlalchemy_database_uri

db = SQLAlchemy(application)
bcrypt = Bcrypt(application)
login_manager = LoginManager(application)
from application import routes
from application import error_handlers



ngrok = False
if ngrok:
    run_with_ngrok(application)