from flask import Flask, render_template, jsonify, request, redirect, url_for

							#might need later, maybe not
							#from flask_cors import CORS
							#CORS(app, supports_credentials=True)
							#import json


from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

#flask --app app run   use this to run app

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
db = SQLAlchemy(app)
admin = Admin(app)

app.app_context().push() # without this, I recieve flask error

# http://127.0.0.1:5000/ # link to webaddress

# first database = "key, username, password"
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

    def __repr__(self): # how database User is printed out
    	return f"User('{self.email}', '{self.password}')"

# second database = "course name, teacher, time, students enrolled"



admin.add_view(ModelView(User, db.session))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run')
def run():
	return "<p>Is indeed running page</p>"


@app.route("/login", methods=["POST"])
def login():

    Email = request.form['email']
    Password = request.form['password']

    user = User.query.filter_by(email=Email).first()
 

    if user is not None:
    	if user.password == Password:
    		return redirect(url_for('success', name=user.email))

    	else:
    		return jsonify({"error": "Password is not correct"}), 404
    else:
    	return jsonify({"error": "Invalid request: Email not found.."}), 404


@app.route('/success/<name>')
def success(name):
    return 'Welcome %s' % name






if __name__ == '__main__':
    app.run(debug=True)



##  User('Admin@ucmerced.edu', 'AdminPassword10')
# login: Admin@ucmerced.edu
# password: AdminPassword10

# Notes 

#install//
# pip install Flask
# pip install flask-admin
# pip install -U Flask-SQLAlchemy
#


### how to add in to database using terminal.
#>>> from app import app      use this to avoid error
#>>> from app import db
#>>> from app import User
#>>> user1 = User(email='Admin@ucmerced.edu', password='AdminPassword10')
#>>> db.session.add(user1)
#>>> db.session.commit()