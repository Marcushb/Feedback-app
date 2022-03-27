from app.models import User, Post
from app import app, db, bcrypt
from flask import request, jsonify

@app.route("/home")
def home():
    return 'Home'

@app.route("/register", methods = ['POST'])
def register():
    if request.method == 'POST':
        request_data = request.form
        hashed_pw = bcrypt.generate_password_hash(request_data['password'])
        user = User(username = request_data['username'], 
                    email = request_data['email'], 
                    password = hashed_pw)
        db.session.add(user)
        db.session.commit()

    return f'Database: {User.query.all()}'