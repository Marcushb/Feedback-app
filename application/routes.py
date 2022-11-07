import json
from queue import Empty
from application.models import User, Event, Question, Feedback, Pin, VerifyInput
from application import application, db, constant, bcrypt
from flask import request, jsonify, make_response, json
from application.functions import change_event, check_isActive_expired
import requests
import uuid
import jwt
from functools import wraps
import random
from datetime import datetime, timedelta
from dateutil import parser
# random.seed(42)
db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        jwt_token = None
        if 'x-access-token' in request.headers:
            jwt_token = request.headers['x-access-token']

        if not jwt_token:
            return jsonify({
                'errorMessage': 'Token is missing',
                'route': f'{request.url}',
                'statusCode': 401
                }), 401

        try:
            data = jwt.decode(jwt_token,
                              application.config['SECRET_KEY'],
                              algorithms="HS256")
            current_user = User.query.filter_by(email = data['email']).first()
        except:
            return jsonify({
                'errorMessage': 'Token does not match',
                'route': f'{request.url}',
                'statusCode': 401})

        return f(current_user, *args, **kwargs)

    return decorated

@application.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return 'App is alive'

    if request.method == 'POST':
        return 'App is alive'
    
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

@application.route("/login_microsoft", methods = ['POST'])
def login_microsoft():
    if request.method == 'POST':
        # input_check = VerifyInput.check_keys(
        #     keys_expected = ['accessToken'], 
        #     check_type = 'request'
        #     )
        # if input_check['result'] == 'error':
        #     return jsonify(input_check)
        input_check = request.get_json(force = True)
        header = {"Authorization": f"Bearer {input_check['accessToken']}"}
        verified = requests.get(
            url = constant.urls['microsoft']['verify_identity'], 
            headers = header
            )

        if 'error' in verified.json().keys():
            return jsonify({
                'errorMessage': verified.json()['error']['code'],
                'route': f'{request.url}',
                'statusCode': verified.status_code
            }), verified.status_code
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
                name = user_name,
                email = user_email,
                jwt_token = jwt_token
                )
            db.session.add(new_user)
            db.session.commit()
            user = User.query.filter_by(email = user_email).first()
        else:
            user.email = user_email
            user.name = user_name
            db.session.commit()

        # For at definere expiration time
        # 'exp': datetime.datetime.utcnow(
        # ) + datetime.timedelta(minutes=30)}

        # Create function to convert one type of variable to another
        if user.name == "":
            user.name = None
        return jsonify({
                'jwtToken': user.jwt_token,
                'email': user.email,
                'name': user.name
        }), 200

    # if request.method == 'POST':
    #     user = User.query.filter_by(email=request.form['email']).first()
    #     if user and bcrypt.check_password_hash(user.password, request.form['password']):
    #         login_user(user, remember=True)
    #         return f'Login succesful\nUser information: {User.query.get(user.id)}'
    #     else:
    #         return 'Get smashed'

@application.route("/register_app", methods = ["POST"])
def register_app():
    ## IMPLEMENTÉR KRAV TIL EMAIL - HER ELLER FRONTEND?
    if request.method == 'POST':
        data = request.get_json(force = True)
        exists = User.query.filter_by(email = data['email']).first()
        if exists:
            return jsonify({
                'errorMessage': 'Email already exists',
                'route': f'{request.url}',
                'statusCode': 400
            }), 400
        
        jwt_token = jwt.encode(
            {
                'email': data['email'],
                'name': data['name']
            },
                key = application.config['SECRET_KEY'],
                algorithm = "HS256"
        )
        new_user = User(
            name = data['name'],
            email = data['email'],
            jwt_token = jwt_token,
            unhashed_password = data['password']
            )
        db.session.add(new_user)
        db.session.commit()
        user = User.query.filter_by(email = new_user.email).first()
        if user.name == "":
            user.name = None
        return jsonify({
                'jwtToken': user.jwt_token,
                'email': user.email,
                'name': user.name
                }), 200



# @application.route("/logout", methods=["GET", "POST"])
# def logout():
#     if request.method == 'POST':
#         logout_user()

@application.route("/login_app", methods = ["POST"])
def login_app():
     if request.method == 'POST':
        data = request.get_json(force = True)
        user = User.query.filter_by(email = data['email']).first()
        if user and bcrypt.check_password_hash(user.password, data['password']):
            return jsonify({
                'jwtToken': user.jwt_token,
                'email': user.email,
                'name': user.name
                }), 200
        else:
            return jsonify({
                'errorMessage': 'Incorrect email or password',
                'route': f'{request.url}',
                'statusCode': 401
                }), 401
                
                
@application.route("/get_microsoft_events", methods = ["POST"])
@token_required
def get_outlook_events(current_user):
    if request.method == 'POST':
        # LAV GENEREL FUNKTION TIL AT VERIFICERE
        # data = VerifyInput.check_keys(check_type = 'request', keys_expected = ['accessToken'])
        # if data['result'] == 'error':
        #     return jsonify(data)
        data = request.get_json(force = True)
        header = {"Authorization": f"Bearer {data['accessToken']}"}
        params = {
            'select': 'id, subject, bodyPreview, start, end, attendees, location'
            }
        verified = requests.get(
            url = constant.urls['microsoft']['get_user_events'], 
            headers = header, 
            params = params
            )

        if 'error' in verified.json().keys():
            return jsonify({
                'message': f"{verified.json()['error']['code']}",
                'statusCode': f"{verified.status_code}"
            })
        else:
            verified = verified.json()
            """data = VerifyInput.check_keys(
                check_type = 'object',
                keys_expected = [
                    'id',
                    'subject',
                    'bodyPreview',
                    'start',
                    'end',
                    'location',
                    'attendees'
                ],
                data = verified['value'][0]
                # Ikke glad for at value[0] er hardcoded - led efter alternativ løsning
            )
            if data['result'] == 'error':
                return jsonify(data)"""
        output = []
        for meeting in verified['value']:
            output_data = {}
            output_data['id'] = meeting['id']
            output_data['subject'] = meeting['subject']
            output_data['bodyPreview'] = meeting['bodyPreview']
            output_data['startTime'] = parser.isoparse(meeting['start']['dateTime']).isoformat() + "Z"
            output_data['endTime'] = parser.isoparse(meeting['end']['dateTime']).isoformat() + "Z"
            output_data['location'] = meeting['location']['displayName']

            attendees = []
            for attendee in meeting['attendees']:
                data = {
                    'email': attendee['emailAddress']['address'], 
                    'name': attendee['emailAddress']['name']
                    }
                attendees.append(data)
            output_data['attendees'] = attendees
            output.append(output_data)

        return jsonify({'response': output}), 200
    return jsonify({
        'message': 'Request method must be POST',
        'statusCode': 401
        }), 401


@application.route("/create_event", methods = ['POST'])
@token_required
def createEvent(current_user):
    if request.method == 'POST':
        user = User.query.filter_by(email = current_user.email).first()
        data = request.get_json(force = True)

        public_id = str(uuid.uuid4())
        pin_event = random.randint(0, 9999)
        while Pin.query.filter_by(pin = pin_event).first() is not None:
            pin_event = random.randint(0, 9999)
        db.session.add(Pin(pin = pin_event))
        db.session.commit()

        event = Event(
            public_id = public_id,
            pin = pin_event,
            title = data['title'],
            date_start = data['startDate'],
            date_end = data['endDate'],
            description = data['description'],
            created_by_user = user.id
        )
        db.session.add(event)

        questions = data['questions']
        event = Event.query.filter_by(public_id = public_id).first()

        for question in questions:
            question_db = Question(
                description = question,
                asked_by_user = user.id,
                parent_event = event.id
            )
            db.session.add(question_db)

        db.session.commit()

        return {}, 200


@application.route("/modify_event", methods = ['PUT', 'DELETE'])
@token_required
def modify_event(current_user):
    data = request.get_json(force = True)

    if request.method == 'PUT':
        event = Event.query.filter_by(id = data['ID']).first()
        event.title = data['title']
        event.date_start = data['startDate']
        event.date_end = data['endDate']
        event.description = data['description']
        db.session.commit()

        return {}, 200
    
    if request.method == 'DELETE':
        for id in data['ID']:
            event = Event.query.filter_by(id = id).first()
            questions = Question.query.filter_by(parent_event = id).delete()
            feedbacks = Feedback.query.filter_by(parent_event = id).delete()
            event = Event.query.filter_by(id = id).delete()
        db.session.commit()

        return {}, 200

@application.route("/modify_question", methods = ['PUT', 'DELETE'])
@token_required
def modify_question(current_user):
    data = request.get_json(force = True)

    if request.method == 'PUT':
        question = Question.query.filter_by(id = data['ID']).first()
        question.description = data['description']
        db.session.commit()

        return {}, 200
    
    if request.method == 'DELETE':
        for id in data['ID']:
            question = Question.query.filter_by(id = id).first()
            feedbacks = Feedback.query.filter_by(parent_question = id).delete()
            question = Question.query.filter_by(id = id).delete()
        db.session.commit()

        return {}, 200

@application.route("/modify_feedback", methods = ['PUT', 'DELETE'])
@token_required
def modify_feedback(current_user):
    data = request.get_json(force = True)

    if request.method == 'PUT':
        feedback = Feedback.query.filter_by(id = data['ID']).first()
        feedback.rating = data['rating']
        feedback.content = data['content']
        db.session.commit()

    if request.method == 'DELETE':
        for id in data['ID']:
            feedback = Feedback.query.filter_by(id = id).delete()
        db.session.commit()

        return {}, 200
    
    if request.method == 'DELETE':
        for id in data['ID']:
            question = Question.query.filter_by(id = id).first()
            feedbacks = Feedback.query.filter_by(parent_question = id).delete()
            question = Question.query.filter_by(id = id).delete()
        db.session.commit()

        return {}, 200

# @application.route("/question/<app_id>", methods=['POST', 'GET'])
# @token_required
# def ask_question(current_user, app_id):
#     if request.method == 'POST':
        
#         user = User.query.filter_by(public_id = current_user.public_id).first()
#         event = Event.query.filter_by(app_id = app_id).first()

#         question = Question(
#             question = request.get_json('question'),
#             asked_by_user = user.id,
#             parent_event = event.id
#         )
#         db.session.add(question)
#         db.session.commit()

#         return question.question, 200

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

    return jsonify({'users': output}), 200

@application.route("/get_one_user/<public_id>", methods=['GET'])
def get_one_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['email'] = user.email

    return jsonify({'user': user_data}), 200


@application.route("/events", methods = ['GET'])
@token_required
def get_events_new(current_user):
    if request.method == 'GET':
        user = User.query.filter_by(email = current_user.email).first()
        events_db = Event.query.filter_by(created_by_user = user.id).all()
        if len(events_db) == 0:
            return jsonify({"response": []}), 200
        events = []
        for event in events_db:
            event_data = {}
            feedback_data = Feedback.query.filter_by(parent_event = event.id).all()
            feedback_rating = []
            for feedback in feedback_data:
                feedback_rating.append(feedback.rating)
            event_data['id'] = event.id
            event_data['title'] = event.title
            event_data['startDate'] = event.date_start
            event_data['endDate'] = event.date_end
            event_data['feedbackCount'] = len(feedback_rating)
            event_data['rating1'] = feedback_rating.count(1)
            event_data['rating2'] = feedback_rating.count(2)
            event_data['rating3'] = feedback_rating.count(3)
            event_data['rating4'] = feedback_rating.count(4)
            event_data['isActive'] = check_isActive_expired(
                event,
                constant.expiration_min
                )

            events.append(event_data)

        return jsonify({"response": events}), 200


@application.route("/events/<id>", methods = ['GET'])
@token_required
def get_events(current_user, id):
    if request.method == 'GET':
        
        event = Event.query.filter_by(id = id).first()
        event_data = {}
        event_data['title'] = event.title
        event_data['startDate'] = event.date_start
        event_data['endDate'] = event.date_end
        event_data['description'] = event.description
        event_data['isActive'] = check_isActive_expired(
            event,
            constant.expiration_min
        )

        questions_db = Question.query.filter_by(parent_event = event.id).all()
        questions = []
        for question in questions_db:
            question_data = {}
            question_data['question'] = question.description

            feedbacks_db = Feedback.query.filter_by(parent_question = question.id).all()
            feedbacks = []
            for feedback in feedbacks_db:
                feedback_data = {}
                feedback_data['rating'] = feedback.rating
                feedback_data['content'] = feedback.content
                feedbacks.append(feedback_data)

            question_data['feedbacks'] = feedbacks
            questions.append(question_data)
            
        event_data['questions'] = questions

        return jsonify({'response': event_data}), 200


@application.route("/initialize_session/<pin>", methods = ["POST"])
def initialize_session(pin):
    if request.method == 'POST':
        event = Event.query.filter_by(pin = pin).first()
        if event:
            event_data = {}
            event_data['isActive'] = check_isActive_expired(
                event.isActive,
                event.date_end,
                constant.expiration_min
                )
            if not event_data['isActive']:
                return jsonify({
                    'errorMessage': f'Pin {pin} is not valid',
                    'route': f'{request.url}',
                    'statusCode': 410
                    }), 410
            event_data['title'] = event.title
            event_data['date_posted'] = event.date_posted
            event_data['description'] = event.description

            questions_db = Question.query.filter_by(parent_event = event.id).all()
            questions = []
            for question in questions_db:
                question_data = {}
                question_data['question'] = question.description
                questions.append(question_data)
            event_data['questions'] = questions

            return jsonify({'response': event_data}), 200
        else:
            return jsonify({
                'errorMessage': f'Pin {pin} is not valid',
                'route': f'{request.url}',
                'statusCode': 404
                }), 404


@application.route("/submit_feedback", methods = ['POST'])
def give_feedback():
    if request.method == 'POST':
        data = request.get_json(force = True)
        parent_question = Question.query.filter_by(id = data['questionID']).first()
        parent_user_id = parent_question.asked_by_user

        feedback = Feedback(
            rating = data['rating'],
            content = data['content'],
            answered_by_id = parent_user_id,
            parent_question = parent_question.id,
            parent_event = parent_question.parent_event
        )
        db.session.add(feedback)
        db.session.commit()

        return {}, 200


@application.route("/test", methods = ["POST"])
def test():
    event = Event.query.filter_by(created_by_user = 1).first()
    test = check_isActive_expired(
        event,
        constant.expiration_min
        )
    return f"{test}", 200

