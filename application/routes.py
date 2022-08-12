import json
from application.models import User, Event, Question, Feedback, VerifyInput
from application import application, db, constant, bcrypt
from flask import request, jsonify, make_response
import requests
import uuid
import jwt
import datetime
from functools import wraps
import random
from datetime import datetime
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
                'message': 'Token is missing',
                'statusCode': 401})

        try:
            data = jwt.decode(jwt_token,
                              application.config['SECRET_KEY'],
                              algorithms="HS256")
            current_user = User.query.filter_by(email = data['email']).first()
        except:
            return jsonify({
                'message': 'Token does not match',
                'statusCode': 401})

        return f(current_user, *args, **kwargs)

    return decorated

@application.route("/", methods=['POST'])
def home():
    if request.method == 'POST':
        input_check = VerifyInput.check_keys(keys_expected = ['title'], check_type = 'request')
        if input_check['result'] == 'error':
            return jsonify(input_check)
        else:
            return input_check
        # return VerifyInput.validate_input(method = 'POST', data_expected = ['title', "question"])

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

@application.route("/login_microsoft", methods=['POST'])
def login():
    if request.method == 'POST':
        input_check = VerifyInput.check_keys(
            keys_expected = ['accessToken'], 
            check_type = 'request'
            )
        if input_check['result'] == 'error':
            return jsonify(input_check)
        header = {"Authorization": f"Bearer {input_check['accessToken']}"}
        verified = requests.get(
            url = constant.urls['microsoft']['verify_identity'], 
            headers = header
            )

        if 'error' in verified.json().keys():
            return jsonify({
                'message': verified.json()['error']['code'],
                'statusCode': verified.status_code
            })
                # undersøg mulighed for at implementre forskellige messages alt efter error, 
                # f.eks specifik message hvis token er udløbet, en anden hvis den aldrig 
                # har virket etc
        else:
            verified = verified.json()
        data = VerifyInput.check_keys(
            check_type = 'object', 
            keys_expected = ['userPrincipalName', 'displayName'],
            data = verified
            )
        if data['result'] == 'error':
            return jsonify(data)
        user_email, user_name = data['userPrincipalName'], data['displayName']
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

        # For at definere expiration time
        # 'exp': datetime.datetime.utcnow(
        # ) + datetime.timedelta(minutes=30)}

        # Create function to convert one type of variable to another
        if user.name == "":
            user.name = None
        return jsonify({
                'jwtToken': user.jwt_token,
                'email': user.email,
                'name': user.name,
                'statusCode': 200    
        })

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



@application.route("/get_microsoft_events", methods = ["POST"])
@token_required
def get_outlook_events(current_user):
    if request.method == 'POST':
        # LAV GENEREL FUNKTION TIL AT VERIFICERE
        data = VerifyInput.check_keys(check_type = 'request', keys_expected = ['accessToken'])
        if data['result'] == 'error':
            return jsonify(data)
        header = {"Authorization": f"Bearer {data['access_token']}"}
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
            data = VerifyInput.check_keys(
                check_type = 'object',
                keys_expected = [
                    'microsoft_id',
                    'subject',
                    'bodyPreview',
                    'start_time',
                    'end_time',
                    'location'
                ],
                data = verified['value'][0]
                # Ikke glad for at value[0] er hardcoded - led efter alternativ løsning
            )
            if data['result'] == 'error':
                return jsonify(data)
        output = []
        for meeting in verified['value']:
            output_data = {}
            output_data['microsoft_id'] = meeting['id']
            output_data['subject'] = meeting['subject']
            output_data['bodyPreview'] = meeting['bodyPreview']
            output_data['start_time'] = meeting['start']['dateTime']
            output_data['end_time'] = meeting['end']['dateTime']
            output_data['location'] = meeting['location']['displayName']

            attendees_name, attendees_email = [], []
            for attendee in meeting['attendees']:
                email, name = attendee['emailAddress']['address'], attendee['emailAddress']['name']
                attendees_email.append(email), attendees_name.append(name)
            output_data['attendees_name'] = attendees_name
            output_data['attendees_email'] = attendees_email
            output.append(output_data)

        return jsonify({
            'microsoftEvents': output,
            'statusCode': 200
        })
    return jsonify({
        'message': 'Request method must be POST',
        'statusCode': 401
        })


@application.route("/create_event", methods = ['POST', 'PUT'])
@token_required
def createEvent(current_user):
    if request.method == 'POST':
        user = User.query.filter_by(email = current_user.email).first()
        data = VerifyInput.check_keys(
            check_type = 'request', 
            keys_expected = ['title', 'date_start', 'date_end', 'description']
            )
        if data['result'] == 'error':
            return jsonify(data)
        event = Event(
            app_id = random.randint(0, 9999),
            title = data['title'],
            # date_start = request.form['date_start'],
            # date_end = datetime request.form['date_end'],
            description = data['description'],
            created_by_user = user.id
        )
        db.session.add(event)

        questions = request.form['question']
        # FIND LØSNING PÅ LOOP OVER QUESTIONS 
        if isinstance(question, str):
            question_db = Question(
                question = question,
                asked_by_user = user.id,
                parent_event = event.id
            )
            db.session.add(question_db)

        elif isinstance(question, list):
            for question in questions:
                question_db = Question(
                    question = question,
                    asked_by_user = user.id,
                    parent_event = event.id
                )
                db.session.add(question_db)

        db.session.commit()

        return jsonify({
                'title': f'{event.title}',
                'description': f'{event.description}',
                'creatorName': f'{event.user_events.name}',
                'creatorEmail': f'{event.user_events.email}',
                'eventPublic_id': f'{event.app_id}',
                'statusCode': 200
                })

    if request.method == 'PUT':
        data = VerifyInput.check_keys(check_type = 'request', keys_expected = ['appId'])
        if data['result'] == 'error':
            return data
        event = Event.query.filter_by(app_id = data['appId']).first()
        """
        Lav funktion der verificerer at de sendte parametre er parametre der kan ændres.
        F.eks for Event skal den tjekke, at keys i de sendte parametre i request.form[]
        er i listen ['title', 'date_start', 'date_end', 'description'] 
        """
        keys_accepted = VerifyInput.check_overwrite_keys(
            keys_overwrite = [request.form['keys_overwrite']], 
            keys_accepted = constant.db_overwrite_params['Event']
            )
        if keys_accepted:
            return jsonify(keys_accepted)
        else:
            return 'keys overwrite accepted'



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
def get_one_user(public_id):
    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['email'] = user.email

    return jsonify({'user': user_data})

@application.route("/get_events", methods = ['POST'])
def get_events():
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

        return jsonify({'email': user.email, 'events': events})

@application.route("/get_event/<app_id>", methods = ['GET'])
def get_event(app_id):
    if request.method == 'GET':
        event = Event.query.filter_by(app_id = app_id).all()
        questions_db = Question.query.filter_by(parent_event = event.id).all()
        questions = []
        for question in questions_db:
            question_data = {}
            question_data['question'] = question.question
        
        event_object = {
            'event_title': event.title,
            'event_descrption': event.description,
            'questions': questions
        }
        return event_object


@application.route("/test", methods = ["POST"])
def test():
    return "blabla", 401

