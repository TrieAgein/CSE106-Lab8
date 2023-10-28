from flask import Flask, render_template, jsonify, request, redirect, url_for

							#might need later, maybe not
							#from flask_cors import CORS
							#CORS(app, supports_credentials=True)
							#import json


from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash

#flask --app app run   use this to run app

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
app.config["SECRET_KEY"] = "mysecret"
db = SQLAlchemy(app)
admin = Admin(app)

app.app_context().push() # without this, I recieve flask error

# http://127.0.0.1:5000/ # link to webaddress

# first database = "key, username, password"
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studentName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    role = db.Column(db.String(20), CheckConstraint("role IN ('student', 'teacher', 'admin')"), default='student')

    #def __repr__(self): # how database User is printed out
    	# return f"User('{self.email}', '{self.password}')"
    #    return f"User('{self.studentName}')"


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    grade = db.Column(db.Integer)  # Add this if you want to store grades



# second database = "course name, teacher, time, students enrolled"
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    courseName = db.Column(db.String(20), nullable=False)
    teacher = db.Column(db.String(30), nullable=False)  ## might have to delete teacher here
    time = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable = False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    teacherType = db.relationship("User", backref='course_taught', foreign_keys=[teacher_id])


class UserView(ModelView):
    #pass
    form_columns = ["studentName", "password", "role"]  #should not display passwords
    column_list = ["studentName", "password", "role"]
    column_labels = {
        "studentName": "Student Name",
        "email": "Email",
        "role": "Role"
    }


class CourseView(ModelView):
    form_columns = ["courseName", "teacherType", "time", "capacity"]
    column_list = ["courseName", "teacherType", "time", "capacity"]

    form_args = {
        'courseName': {
            'label': 'Course Name',
            'description': 'Enter the course name in the format [AAA 100].'
        },
        'time': {
            'label': 'Time',
            'description': 'Enter the time in the format [MTWTF #:##-#:## AM].'
        },
        'capacity': {
            'label': 'Capacity',
            'description': 'Enter the maximum number of registrations allowed.'
        },
        'teacherType': {
            'label': 'Teacher',
            'description': 'Select the teacher teaching the course.'
        }
    }

    form_ajax_refs = {
        'students': QueryAjaxModelLoader('students', db.session, User, fields=['studentName'])
    }


admin.add_view(UserView(User, db.session))
admin.add_view(CourseView(Course, db.session))
admin.add_view(ModelView(Registration, db.session))



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_Page')
def register_Page():
    return render_template('register.html')

@app.route('/run')
def run():
	return "<p>Is indeed running page</p>"


# Function to register a new user // can only register new students or teachers
@app.route('/register', methods=['POST'])
def register():

    name = request.form.get('new_name')
    email = request.form.get('new_email')
    password = request.form.get('new_password')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 400


    # Check if the email ends with "@eduteacher"
    if email.endswith("@EDUteacher"):
        role = 'teacher'
    else:
        role = 'student'

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    new_user = User(studentName=name, email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return render_template('registration_success.html')


@app.route("/login", methods=["POST"])
def login():

    Email = request.form['email']
    Password = request.form['password']

    user = User.query.filter_by(email=Email).first()
 
    # Check if the email ends with "@type" and assign role at login
    if user is not None:
        if check_password_hash(user.password, Password):
            if Email.endswith("@admin"):
                user.role = 'admin'
                return redirect(url_for('admin'))

            elif Email.endswith("@EDUteacher"):
                user.role = 'teacher'
                return redirect(url_for('portal', name=user.studentName))

            else:
                user.role = 'student'

            db.session.commit()

            #return f"Logged in as {user.username} with role {user.role}"
            return redirect(url_for('success', name=user.studentName))

        else:
            return jsonify({"error": "Password is not correct"}), 404
    else:
        return jsonify({"error": "Invalid request: Email not found or invalid login credentials"}), 404


@app.route('/success/<name>')
def success(name):
    return 'Welcome student %s' % name


@app.route('/portal/<name>')
def portal(name):
    return 'Welcome teacher %s' % name


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
# pip install Flask-Admin[sqla]
# pip install Werkzeug   


### create_db.py
#from app import db
#db.create_all()

### how to add in to database using terminal.
#>>> from app import app      use this to avoid error
#>>> from app import db
#>>> from app import User
#>>> user1 = User(email='Admin@ucmerced.edu', password='AdminPassword10')
#>>> db.session.add(user1)
#>>> db.session.commit()