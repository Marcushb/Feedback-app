import json
from application.models import User, Event, Question, Feedback, Pin, VerifyInput
from application import application, db, constant, bcrypt
from flask import request, jsonify, make_response, json
import flask
from application.functions import change_event, setIsActive, force_isActive, db_query_filter, json_response, create_feedback_summary
import requests
import uuid
import jwt
from functools import wraps
import random
from datetime import datetime, timedelta
from dateutil import parser
import pytest
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
                'errorMessage': 'Microsoft login unsuccesful',
                'devInfo': verified.json()['error']['code'],
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

        if user.name == "":
            user.name = None
        return jsonify({
                'jwtToken': user.jwt_token,
                'email': user.email,
                'name': user.name
        }), 200

@application.route("/register_app", methods = ["POST"])
def register_app():
    ## IMPLEMENTÉR KRAV TIL EMAIL - HER ELLER FRONTEND?
    if request.method == 'POST':
        data = request.get_json(force = True)
        exists = User.query.filter_by(email = data['email']).first()
        if exists:
            return jsonify({
                'errorMessage': 'Email already exists.',
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
        user = db_query_filter("User", "email", new_user.email, "first", "user")
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
                'errorMessage': 'Could not load Microsoft events.',
                'devInfo': f"{verified.json()['error']['code']}",
                "route": f"{request.url}",
                'statusCode': f"{verified.status_code}"
            })
        else:
            verified = verified.json()
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


@application.route("/create_event", methods = ['POST'])
@token_required
def createEvent(current_user):
    if request.method == 'POST':
        user = User.query.filter_by(email = current_user.email).first()
        data_total = request.get_json(force = True)
        
        for data in data_total:
            public_id = str(uuid.uuid4())
            pin_event = random.randint(0, 9999)
            while Event.query.filter_by(pin = pin_event).first() is not None:
                pin_event = random.randint(0, 9999)
            # db.session.add(Pin(pin = pin_event))
            # db.session.commit()

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
        event = db_query_filter("Event", "id", data['ID'], "first", "event")
        if isinstance(event, tuple):
            return event
        event.title = data['title']
        event.date_start = data['startDate']
        event.date_end = data['endDate']
        event.description = data['description']
        db.session.commit()

        return {}, 200
    
    if request.method == 'DELETE':
        for id in data['ID']:
            event = db_query_filter("Event", "id", id, "first", "event")
            if isinstance(event, tuple):
                return event
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
        question = db_query_filter("Question", "id", data['ID'], "first", "question")
        if isinstance(question, tuple):
                return question
        question.description = data['description']
        db.session.commit()

        return {}, 200
    
    if request.method == 'DELETE':
        for id in data['ID']:
            question = db_query_filter("Question", "id", id, "first", "question")
            if isinstance(question, tuple):
                return question
            feedbacks = Feedback.query.filter_by(parent_question = id).delete()
            question = Question.query.filter_by(id = id).delete()
        db.session.commit()

        return {}, 200

# @application.route("/modify_feedback", methods = ['PUT', 'DELETE'])
# @token_required
# def modify_feedback(current_user):
#     data = request.get_json(force = True)

#     if request.method == 'PUT':
#         feedback = Feedback.query.filter_by(id = data['ID']).first()
#         feedback.rating = data['rating']
#         feedback.content = data['content']
#         db.session.commit()

#     if request.method == 'DELETE':
#         for id in data['ID']:
#             feedback = Feedback.query.filter_by(id = id).delete()
#         db.session.commit()

#         return {}, 200
    
#     if request.method == 'DELETE':
#         for id in data['ID']:
#             question = Question.query.filter_by(id = id).first()
#             feedbacks = Feedback.query.filter_by(parent_question = id).delete()
#             question = Question.query.filter_by(id = id).delete()
#         db.session.commit()

#         return {}, 200

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
            event_data['id'] = event.id
            event_data['title'] = event.title
            event_data['startDate'] = event.date_start
            event_data['endDate'] = event.date_end
            event_data['isActive'] = setIsActive(event, constant.expiration_min)
            event_data['feedbackSummary'] = create_feedback_summary(
                Feedback.query.filter_by(parent_event = event.id).all()
            )
            events.append(event_data)

        return jsonify({"response": events}), 200


@application.route("/events/<id>", methods = ['GET'])
@token_required
def get_events(current_user, id):
    if request.method == 'GET':
        
        # event = Event.query.filter_by(id = id).first()
        # if not event:
        #     return none_json("event")
        event = db_query_filter("Event", "id", id, "first", "event")
        if isinstance(event, tuple):
            return event

        event_data = {}
        event_data['title'] = event.title
        event_data['startDate'] = event.date_start
        event_data['endDate'] = event.date_end
        event_data['description'] = event.description
        event_data['isActive'] = setIsActive(event, constant.expiration_min)
        event_data['pin'] = event.pin

        questions_db = db_query_filter(
            "Question",
            "parent_event",
            event.id,
            "all",
            "questions_db"
        )
        # questions_db = Question.query.filter_by(parent_event = event.id).all()
        questions = []
        for question in questions_db:
            question_data = {}
            question_data['id'] = question.id
            question_data['question'] = question.description

            feedbacks_db = Feedback.query.filter_by(parent_question = question.id).all()
            if not feedbacks_db:
                feedbacks = None
            else: 
                feedbacks = []
                for feedback in feedbacks_db:
                    feedback_data = {}
                    feedback_data['rating'] = feedback.rating
                    if not feedback.content:
                        feedback_data['content'] = None
                    else:
                        feedback_data['content'] = feedback.content
                    feedbacks.append(feedback_data)

            question_data['feedbacks'] = feedbacks

            question_data['questionFeedbackSummary'] = create_feedback_summary(
                Feedback.query.filter_by(parent_question = question.id).all()
                )

            questions.append(question_data)
            
        event_data['questions'] = questions

        event_data['feedbackSummary'] = create_feedback_summary(
            Feedback.query.filter_by(parent_event = event.id).all()
            )

        return jsonify({'response': event_data}), 200


@application.route("/initialize_session/<pin>", methods = ["POST"])
def initialize_session(pin):
    if request.method == 'POST':
        event = Event.query.filter_by(pin = pin).first()
        if event:
            event_data = {}
            isActive = setIsActive(event, constant.expiration_min)
            if isActive == 'FINISHED':
                return jsonify({
                    'errorMessage': f'Pin {pin} is not valid',
                    'route': f'{request.url}',
                    'statusCode': 410
                    }), 410
            user = db_query_filter("User", "id", event.created_by_user, "first", "user")
            event_data['ownerName'] = user.name
            event_data['ownerEmail'] = user.email
            event_data['title'] = event.title
            event_data['datePosted'] = event.date_posted
            event_data['description'] = event.description

            questions_db = Question.query.filter_by(parent_event = event.id).all()
            questions = []
            for question in questions_db:
                question_data = {}
                question_data['description'] = question.description
                question_data['id'] = question.id
                questions.append(question_data)
            event_data['questions'] = questions

            return jsonify({'response': event_data}), 200
        else:
            # return jsonify({
            #     'errorMessage': f'Pin {pin} is not valid',
            #     'route': request.url,
            #     'statusCode': 404
            #     }), 404
            return json_response(
                f"Pin {pin} is not valid", 
                f"Event with Pin {pin} does not exist in database",
                request.url,
                404
            ), 404


@application.route("/submit_feedback", methods = ['POST'])
def give_feedback():
    if request.method == 'POST':
        data = request.get_json(force = True)

        for answer in data:
            parent_question = db_query_filter(
                "Question",
                "id", 
                answer['id'], 
                "first", 
                "parent_question"
                )
            if isinstance(parent_question, tuple):
                return parent_question
            # parent_question = Question.query.filter_by(id = answer['id']).first()
            feedback = Feedback(
                rating = answer['rating'],
                content = answer['content'],
                parent_question = parent_question.id,
                parent_event = parent_question.parent_event
            )
            db.session.add(feedback)
        db.session.commit()

        return {}, 200


@application.route("/test", methods = ["POST"])
def test() -> flask.Response:
    # event = Event.query.filter_by(created_by_user = 1).first()
    # test = setIsActive(
    #     event,
    #     constant.expiration_min
    #     )
    # data = jsonify({"bla": "bla"})
    data = json_response(1, 1, 1)
    return data

@application.route("/force_event_active", methods = ["POST"])
def force_event_active():
    data = request.get_json(force = True)
    event = Event.query.filter_by(id = data['ID']).first()
    force_isActive(event)

    return {}, 200

