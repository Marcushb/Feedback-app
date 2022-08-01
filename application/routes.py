from application.models import User, Event, Question, Feedback, VerifyInput
from application import application, db, bcrypt
from flask import request, jsonify, make_response
import requests
import uuid
import jwt
import datetime
from functools import wraps
import random
# random.seed(42)
db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        jwt_token = None
        if 'x-access-token' in request.headers:
            jwt_token = request.headers['x-access-token']

        if not jwt_token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(jwt_token,
                              application.config['SECRET_KEY'],
                              algorithms="HS256")
            current_user = User.query.filter_by(
                email = data['email']
                ).first()
        except:
            return jsonify({'message': 'Token does not match'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@application.route("/", methods=['POST', 'GET'])
def home():
    return 'Home'


@application.route("/database", methods=['POST', 'GET'])
def database():
    user = User.query.filter_by(email='user1@live.dk').first()
    return f'{User.query.all()}'


# @application.route("/register", methods=['POST'])
# def register():

#     if request.method == 'POST':
#         user_valid = validate_input(request.form)
#         if user_valid:
#             return user_valid
#         unhashed_password = request.form['password']

#         user = User(
#             public_id=str(uuid.uuid4()),
#             name=request.form['name'],
#             email=request.form['email'],
#             unhashed_password=unhashed_password
#         )

#         db.session.add(user)
#         db.session.commit()

#         return jsonify(
#             [
#                 request.form['name'],
#                 request.form['email'],
#                 request.form['password'],
#                 user.public_id
#             ]
#         )

@application.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        access_token = request.form['access_token']

        if not access_token:
            return jsonify({'message': 'Access token not found'}), 401

        verify_url = "https://graph.microsoft.com/v1.0/me/"
        header = {"Authorization": f"Bearer {access_token}"}
        verified = requests.get(verify_url, headers = header)

        if 'error' in verified.json().keys():
            return verified.json()['error']['code'], verified.status_code
                # undersøg mulighed for at implementre forskellige messages alt efter error, 
                # f.eks specifik message hvis token er udløbet, en anden hvis den aldrig 
                # har virket etc
        else:
            verified = verified.json()
        user_email, user_name = verified['userPrincipalName'], verified['displayName']
        user = User.query.filter_by(email = user_email).first()
        if not user:
            jwt_token = jwt.encode(
                {
                    'email': user_email,
                    'name': user_name
                },
                key = application.config['SECRET_KEY'],
                algorithm = "HS256"
            )
            new_user = User(
                # public_id = str(uuid.uuid4()),
                name = user_name,
                email = user_email,
                jwt_token = jwt_token
                )
            db.session.add(new_user)
            db.session.commit()
            user = User.query.filter_by(email = user_email).first()

        # For at definere expiration time
        # 'exp': datetime.datetime.utcnow(
        # ) + datetime.timedelta(minutes=30)}

        return jsonify(
            {
                'jwt_token': user.jwt_token,
                'email': user.email,
                'name': user.name
            }
        ), 200

    return jsonify({'message': 'Request method must be POST'}), 401

    # if request.method == 'POST':
    #     user = User.query.filter_by(email=request.form['email']).first()
    #     if user and bcrypt.check_password_hash(user.password, request.form['password']):
    #         login_user(user, remember=True)
    #         return f'Login succesful\nUser information: {User.query.get(user.id)}'
    #     else:
    #         return 'Get smashed'


# @application.route("/logout", methods=["GET", "POST"])
# def logout():
#     if request.method == 'POST':
#         logout_user()

@application.route("/create_event", methods = ['POST', 'GET'])
@token_required
def createEvent(current_user):
    if request.method == 'POST':
        user = User.query.filter_by(email = current_user.email).first()
        event = Event(
            app_id = random.randint(0, 9999),
            title = request.form['title'],
            description = request.form['description'],
            created_by_user = user.id
        )
        db.session.add(event)
        db.session.commit()

        return jsonify(
            {
                'title': f'{event.title}',
                'description': f'{event.description}',
                'creator_name': f'{event.user_events.name}',
                'creator_email': f'{event.user_events.email}',
                'event_public_id': f'{event.app_id}'
            }
        )

@application.route("/question/<app_id>", methods=['POST', 'GET'])
@token_required
def ask_question(current_user, app_id):
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

        return question.question, 200

@application.route("/feedback/<question_id>", methods = ['POST'])
def give_feedback(question_id):
    if request.method == 'POST':
        parent_question = Question.query.filter_by(id = int(question_id)).first()
        parent_user = User.query.filter_by(id = parent_question.asked_by_user).first()

        feedback = Feedback(
            content = request.form['content'],
            answered_by_id = parent_user.id,
            parent_question = parent_question.id
        )
        db.session.add(feedback)
        db.session.commit()

        return feedback.content

@application.route("/get_all_users", methods=['GET'])
def get_all_users():
    users = User.query.all()
    output = []
    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
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
    user_data['name'] = user.name
    user_data['email'] = user.email

    return jsonify({'user': user_data})

@application.route("/get_event", methods = ['POST'])
def get_event():
    if request.method == 'POST':
        user = User.query.filter_by(id = request.form['id']).first()
        events_db = Event.query.filter_by(created_by_user = user.id).all()

        events = []
        for event in events_db:
            event_data = {}
            event_data['title'] = event.title
            event_data['date_posted'] = event.date_posted
            event_data['description'] = event.description
            event_data['isActive'] = event.isActive

            questions_db = Question.query.filter_by(parent_event = event.id).all()
            questions = []
            for question in questions_db:
                question_data = {}
                question_data['question'] = question.question
                question_data['date_posted'] = question.date_posted

                feedbacks_db = Feedback.query.filter_by(parent_question = question.id).all()
                feedbacks = []
                for feedback in feedbacks_db:
                    feedback_data = {}
                    feedback_data['content'] = feedback.content
                    feedback_data['date_posted'] = feedback.date_posted
                    feedbacks.append(feedback_data)

                question_data['feedbacks'] = feedbacks
                questions.append(question_data)

            event_data['questions'] = questions

            

            events.append(event_data)

        return jsonify(
                {
                'email': user.email, 
                'events': events
                }
            )
@application.route("/test", methods = ["POST"])
def test():
    return "blabla", 401