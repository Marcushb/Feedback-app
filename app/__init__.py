from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ngrok import run_with_ngrok
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
ngrok = False

if ngrok:
    run_with_ngrok(app)

app.config['SECRET_KEY'] = '6dce49d3b0ac1575f39720120005b5cc2ee0ed20cdba968cd2bbb345647bc9fa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

from app import routes
