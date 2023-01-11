from unicodedata import numeric
from flask import jsonify, request
from sqlalchemy import null
from application import db, login_manager, bcrypt
from datetime import datetime
from dateutil.tz import tzutc
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    # __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key = True)
    # public_id = db.Column(db.String(50), unique = True)
    name = db.Column(db.String(20), unique = False, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    jwt_token = db.Column(db.String(200), unique = True, nullable = False)
    password = db.Column(db.String(200), unique = True, nullable = True)
    user_events = db.relationship(
        'Event',
        foreign_keys='Event.created_by_user',
        backref='user_events',
        lazy=True
    )
    user_questions = db.relationship(
        'Question',
        foreign_keys = 'Question.asked_by_user',
        backref = 'user_questions',
        lazy=True
    )

    @property
    def unhashed_password(self):
        # Nok ikke så smart selv at raise Error så API'en fejler - undersøg
        raise AttributeError('Cannot view unhashed password')

    @unhashed_password.setter
    def unhashed_password(self, unhashed_password):
        self.password = bcrypt.generate_password_hash(unhashed_password)

    def __repr__(self):
        return f"User('{self.name}\n','{self.email}"


class Event(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(50), unique = True)
    pin = db.Column(db.Integer, nullable = False)
    title = db.Column(db.String(100), nullable = False)
    date_posted = db.Column(db.String, default = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), nullable = False)
    date_start = db.Column(db.String, nullable = False)
    date_end = db.Column(db.String, nullable = False)
    description = db.Column(db.Text, nullable = True)
    isActive = db.Column(db.String, default = 'UPCOMING')
    event_questions = db.relationship(
        'Question',
        foreign_keys = 'Question.parent_event',
        backref = 'event_questions'
    )
    event_feedback = db.relationship(
        'Feedback',
        foreign_keys = 'Feedback.parent_event',
        backref = 'event_feedback'
    )
    created_by_user = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"Event('{self.title}, {self.description}, {self.date_posted}')"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    description = db.Column(db.Text, nullable = False)
    question_answers = db.relationship('Feedback', foreign_keys = 'Feedback.parent_question', backref = 'question_answers', lazy = True)
    asked_by_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = True)
    parent_event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable = True)
    index = db.Column(db.Integer, nullable = False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable = False)
    rating = db.Column(db.Integer, nullable = False)
    content = db.Column(db.Text, nullable = True)
    parent_question = db.Column(db.Integer, db.ForeignKey('question.id'), nullable = True)
    parent_event = db.Column(db.Integer, db.ForeignKey('event.id'), nullable = True)

    def __repr__(self):
        return f"Answer('{self.content}')"

class Pin(db.Model):
    pin = db.Column(db.Integer, primary_key = True)

class VerifyInput:
    def check_keys(check_type, keys_expected, data = None):
        match check_type:
            case "request":
                data = request.get_json
            # case "object":
            #     data = data
        key_object = {'result': 'success'}
        for key in keys_expected:
            try:
                key_in_data = data(f'{key}')
                key_object[f'{key}'] = key_in_data
            except:
                return {
                    'message': f'Expected key not found in body: {key}',
                    'statusCode': 403,
                    'result': 'error'
                }
        return key_object
    
    def check_overwrite_keys(keys_overwrite, keys_accepted):
        accepted = all(element in keys_accepted for element in keys_overwrite)
        if not accepted:
            return {
                'message': f'Keys not applicable to be overwritten: {keys_overwrite[accepted]}',
                'statusCode': 406
                }
    
# def clean_data(data):
#  return 'temp'

#  def pull_db_data(table, cols):
#     data_db = ''
#     return 'temp'