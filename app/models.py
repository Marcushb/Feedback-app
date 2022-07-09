from sys import settrace
from app import db, login_manager, bcrypt
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.String(50), unique = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)
    user_events = db.relationship(
        'Event',
        foreign_keys='Event.created_by_id',
        backref='user_events',
        lazy=True
    )
    user_answers = db.relationship(
        'Answer',
        foreign_keys = 'Answer.answered_by_id',
        backref = 'user_answers',
        lazy=True
    )

    @property
    def unhashed_password(self):
        raise AttributeError('Cannot view unhashed password')

    @unhashed_password.setter
    def unhashed_password(self, unhashed_password):
        self.password = bcrypt.generate_password_hash(unhashed_password)

    def __repr__(self):
        return f"User('{self.username}', '{self.public_id}, '{self.password}')"


class Event(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(100), nullable = False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable = False)
    description = db.Column(db.Text)
    isActive = db.Column(db.Integer)
    event_questions = db.relationship(
        'Question',
        foreign_keys = 'Question.parent_event',
        backref = 'event_questions'
    )
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"Post('{self.title}, {self.content}, {self.date_posted}')"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    question = db.Column(db.Text, nullable = False)
    asked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_answers = db.relationship('Answer', foreign_keys='Answer.parent_question', backref = 'question_answers', lazy = True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow(), nullable = False)
    parent_event = db.Column(db.Integer, db.ForeignKey('event.id'))

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow(), nullable = False)
    content = db.Column(db.Text, nullable=False)
    answered_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    parent_question = db.Column(db.Integer, db.ForeignKey('question.id'))

    def __repr__(self):
        return f"Answer('{self.content}')"


def validate_input(input_data):
    username = User.query.filter_by(username=input_data['username']).first()
    email = User.query.filter_by(email=input_data['email']).first()
    if username:
        return('Username already exists.')
    elif email:
        return ('Email already used.')
