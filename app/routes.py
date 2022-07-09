from app.models import User, Question, validate_input
from app import app, db, bcrypt
from flask import request, jsonify, make_response
from flask_login import login_user, logout_user
import uuid
import jwt
import datetime
from functools import wraps
# db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # print(request.headers['x-access-token'])
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            print('This is try')
            data = jwt.decode(token,
                              app.config['SECRET_KEY'],
                              algorithms="HS256")
            print('After data')
            current_user = User.query.filter_by(
                public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token does not match'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.route("/", methods=['POST', 'GET'])
def home():
    return 'Home page'


@app.route("/database", methods=['POST', 'GET'])
def database():
    user = User.query.filter_by(email='user1@live.dk').first()
    # return f'{user.user_posts}'
    return f'{User.query.all()}'


@app.route("/register", methods=['POST'])
def register():

    if request.method == 'POST':
        user_valid = validate_input(request.form)
        if user_valid:
            return user_valid
        unhashed_password = request.form['password']

        user = User(
            public_id=str(uuid.uuid4()),
            username=request.form['username'],
            email=request.form['email'],
            unhashed_password=unhashed_password
        )

        db.session.add(user)
        db.session.commit()

        return jsonify(
            [
                request.form['username'],
                request.form['email'],
                request.form['password']
            ]
        )


@app.route("/login", methods=['GET', 'POST'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required"'})

    user = User.query.filter_by(username=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required"'})

    if bcrypt.check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)},
            key=app.config['SECRET_KEY'],
            algorithm="HS256"
        )

        return jsonify({'token': token})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm = "Login required"'})

    # if request.method == 'POST':
    #     user = User.query.filter_by(email=request.form['email']).first()
    #     if user and bcrypt.check_password_hash(user.password, request.form['password']):
    #         login_user(user, remember=True)
    #         return f'Login succesful\nUser information: {User.query.get(user.id)}'
    #     else:
    #         return 'Get smashed'


@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == 'POST':
        logout_user()


@app.route("/ask", methods=['POST', 'GET'])
@token_required
def ask_question(current_user):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        post = Question(
            title=title,
            content=content
        )

        db.session.add(post)
        db.session.commit()

    return f'{Question.query.filter_by(title = post.title).all()}'

    # return jsonify(
    # [
    #     request.form['title'],
    #     request.form['content']
    # ]
    # )


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
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['username'] = user.username
    user_data['email'] = user.email

    return jsonify({'user': user_data})
