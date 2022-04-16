from sys import settrace
from app import db, login_manager, bcrypt
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique = True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    user_posts = db.relationship(
        'Post',
        foreign_keys='Post.posted_by_id',
        backref='user_posts',
        lazy=True)
    user_answers = db.relationship(
        'Answer',
        foreign_keys='Answer.answered_by_id',
        backref='user_answers',
        lazy=True)

    @property
    def unhashed_password(self):
        raise AttributeError('Cannot view unhashed password')

    @unhashed_password.setter
    def unhashed_password(self, unhashed_password):
        self.password = bcrypt.generate_password_hash(unhashed_password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.password}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow())
    content = db.Column(db.Text)
    posted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_answers = db.relationship('Answer', backref='post_answers', lazy=True)

    def __repr__(self):
        return f"Post('{self.title}', '{self.content}')"


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow())
    content = db.Column(db.Text, nullable=False)
    answered_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    posted_by_id = db.Column(db.Integer, db.ForeignKey('post.id'))

    def __repr__(self):
        return f"Answer('{self.content}')"


def validate_input(input_data):
    username = User.query.filter_by(username=input_data['username']).first()
    email = User.query.filter_by(email=input_data['email']).first()
    if username:
        return('Username already exists.')
    elif email:
        return ('Email already used.')
