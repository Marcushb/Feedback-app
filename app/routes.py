import email
from app.models import User, Post, validate_input
from app import app, db, bcrypt
from flask import request, jsonify
from flask_login import login_user, logout_user
import uuid

## db.create_all()

@app.route("/", methods=['POST', 'GET'])
def home():
    return 'Home page'


@app.route("/database", methods=['POST', 'GET'])
def database():
    return f'{User.query.all()}'


@app.route("/register", methods=['POST'])
def register():

    if request.method == 'POST':
        user_valid = validate_input(request.form)
        if user_valid:
            return user_valid
        unhashed_password = request.form['password']

        user = User(public_id=str(uuid.uuid4()),
                    username=request.form['username'],
                    email=request.form['email'],
                    unhashed_password=unhashed_password)

        db.session.add(user)
        db.session.commit()

        return jsonify([request.form['username'],
                        request.form['email'],
                        request.form['password']]
                       )


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user, remember=True)
            return f'Login succesful\nUser information: {User.query.get(user.id)}'
        else:
            return 'Get smashed'


@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == 'POST':
        logout_user()


@app.route("/ask", methods=['POST', 'GET'])
def ask_question():
    return 'bla'


@app.route("/get_all_users", methods=['GET'])
def get_all_users():
    users = User.query.all()
    output = []
    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['username'] = user.username
        user_data['email'] = user.email
        output.append(user_data)

    return jsonify({'users': output})

@app.route("/get_one_user/<public_id>", methods=['GET'])
def get_one_users(public_id):
    user = User.query.filter_by(public_id = public_id).first()

    if not user:
        return jsonify({'message' : 'No user found'})
        
    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['username'] = user.username
    user_data['email'] = user.email

    return jsonify({'user': user_data})