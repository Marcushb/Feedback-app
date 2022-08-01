from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ngrok import run_with_ngrok
# from flask_cors import CORS

application = Flask(__name__)
# CORS(app)
ngrok = False

if ngrok:
    run_with_ngrok(application)

application.config['SECRET_KEY'] = '6dce49d3b0ac1575f39720120005b5cc2ee0ed20cdba968cd2bbb345647bc9fa'
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(application)
bcrypt = Bcrypt(application)
login_manager = LoginManager(application)

from application import routes

from msal import PublicClientApplication
app_microsoft = PublicClientApplication(
    "94ced860-137f-439b-b5d1-c1ecd802ddc2",
    authority = "https://login.microsoftonline.com/f8cdef31-a31e-4b4a-93e4-5f571e91255a"
    )


