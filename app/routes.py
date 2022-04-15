from app.models import User, Post, validate_input
from app import app, db, bcrypt
from flask import request, jsonify

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

    return f'Database: {User.query.all()}'

@app.route("/login", methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_data = request.form
        user = User.query.filter_by(email = login_data['email']).first()
        if user and bcrypt.check_password_hash(user.password, login_data['password']):
            return f'Database: {User.query.all()}'
        else:
            return 'Get smashed'