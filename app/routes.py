import email
from app.models import User, Post, validate_input
from app import app, db, bcrypt
from flask import request, jsonify
from flask_login import login_user, logout_user

@app.route("/", methods = ['POST', 'GET'])
def home():
    return 'Home page'

@app.route("/database", methods = ['POST', 'GET'])
def database():
    return f'Database: {User.query.all()}, {User.query.filter_by(email = "bla@live.dk").first().password}'

@app.route("/register", methods = ['POST'])
def register():
        
    if request.method == 'POST':
        request_data = request.form
        user_valid = validate_input(request_data)
        if user_valid:
            return user_valid

        hashed_pw = bcrypt.generate_password_hash(request_data['password'])
        user = User(username = request_data['username'], 
                    email = request_data['email'], 
                    password = hashed_pw)
        db.session.add(user)
        db.session.commit()

        return jsonify([request_data['username'],
                        request_data['email'],
                        request_data['password']])

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_data = request.form
        user = User.query.filter_by(email = login_data['email']).first()
        if user and bcrypt.check_password_hash(user.password, login_data['password']):
            login_user(user, remember = True)
            return f'Login succesful\nUser information: {User.query.get(user.id)}'
        else:
            return 'Get smashed'


@app.route("logout", methods = ["GET", "POST"])
def logout():
    if request.method == 'POST':
        logout_user()