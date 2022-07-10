from pickle import TRUE
from application.models import User, Event, Question, validate_input
from application import application, db, bcrypt
from flask import request, jsonify, make_response
from flask_login import login_user, logout_user
import uuid
import jwt
import datetime
from functools import wraps
import random
random.seed(42)
db.create_all()


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
                              application.config['SECRET_KEY'],
                              algorithms="HS256")
            print('After data')
            current_user = User.query.filter_by(
                public_id=data['public_id']).first()
        except:
            return jsonify({'message': 'Token does not match'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@application.route("/", methods=['POST', 'GET'])
def home():
    return 'Home page'


@application.route("/database", methods=['POST', 'GET'])
def database():
    user = User.query.filter_by(email='user1@live.dk').first()
    # return f'{user.user_posts}'
    return f'{User.query.all()}'


@application.route("/register", methods=['POST'])
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
                request.form['password'],
                user.public_id
            ]
        )


@application.route("/login", methods=['GET', 'POST'])
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
            key=application.config['SECRET_KEY'],
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


@application.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == 'POST':
        logout_user()

@application.route("/create_event", methods = ['POST', 'GET'])
@token_required
def createEvent(current_user):
    if request.method == 'POST':
        user = User.query.filter_by(public_id = current_user.public_id).first()
        event = Event(
            app_id = random.randint(0, 9999),
            title = request.form['title'],
            description = request.form['description'],
            created_by_user = user.id
        )
        db.session.add(event)
        db.session.commit()

        return jsonify(
            [
                event.title,
                event.description,
                event.user_events.username,
                event.user_events.email
            ]
        )

@application.route("/question/<app_id>", methods=['POST', 'GET'])
@token_required
def ask_question(current_user, app_id):
# def ask_question():
    if request.method == 'POST':
        
        user = User.query.filter_by(public_id = current_user.public_id).first()
        event = Event.query.filter_by(app_id = app_id).first()

        question = Question(
            question = request.form['question'],
            asked_by_user = user.id,
            parent_event = event.id
        )

        db.session.add(question)
        db.session.commit()

        # return 'Question works'
        return question.user_questions.email, question.event_questions.title

    #     db.session.add(question_asked)
    #     db.session.commit()

    # return f'{Question.query.filter_by(question = question.question_asked).all()}'

    # return jsonify(
    # [
    #     request.form['title'],
    #     request.form['content']
    # ]
    # )


@application.route("/get_all_users", methods=['GET'])
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


@application.route("/get_one_user/<public_id>", methods=['GET'])
def get_one_users(public_id):
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['username'] = user.username
    user_data['email'] = user.email

    return jsonify({'user': user_data})
