
# Import modules
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash

# Create Flask web app
app = Flask(__name__)

# Configure sqlite database and set a secret key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
app.config["SECRET_KEY"] = "mysecret"

# Create the database instance
db = SQLAlchemy(app)

# Create an admin interface for the application
admin = Admin(app)

# Push app context to avoid flask error
app.app_context().push()


# First Database Model for User ("key, username, password")
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studentName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    
    # Define the 'role' column with constraints and default to 'student'
    role = db.Column(db.String(20), CheckConstraint("role IN ('student', 'teacher', 'admin')"), default='student')
    
    # Add a one-to-many relationship with Registration
    registrations = db.relationship('Registration', back_populates='user')


# Second Database Model for Registration
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    grade = db.Column(db.Integer)  # Add this if you want to store grades

    # Define the relationships with User and Course without backref
    user = db.relationship('User', back_populates='registrations')
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))



# Third Database Model for Courses ("course name, teacher, time, students enrolled")
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    courseName = db.Column(db.String(20), nullable=False)
    teacher = db.Column(db.String(30), nullable=False)  ## might have to delete teacher here
    time = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable = False)
    
    # Define a foreign key relationship with User for the teacher
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    teacherType = db.relationship("User", backref='course_taught', foreign_keys=[teacher_id])
    
    # Add a one-to-many relationship with Registration
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id'))

# Create a Flask Admin View to manage Users
class UserView(ModelView):
    form_columns = ["studentName", "password", "role"]
    column_list = ["studentName", "email", "role"]
    column_labels = {
        "studentName": "Student Name",
        "email": "Email",
        "role": "Role"
    }

# Create a Flask Admin View to manage Courses
class CourseView(ModelView):
    form_columns = ["courseName", "teacherType", "time", "capacity"]
    column_list = ["courseName", "teacher", "time", "capacity"]

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
        'teacherType': {
            'fields': ['studentName'],
            'page_size': 10
        }
    }

# Add the User, Course, and Model views to the admin interface
admin.add_view(UserView(User, db.session))
admin.add_view(CourseView(Course, db.session))
admin.add_view(ModelView(Registration, db.session))


# Routes for Application

# Login Route
@app.route('/')
def index():
    return render_template('index.html')


# Registration Route
@app.route('/register_Page')
def register_Page():
    return render_template('register.html')

# Test Route
@app.route('/run')
def run():
	return "<p>Is indeed running page</p>"


# Function to register a new user (Student or Teacher)
@app.route('/register', methods=['POST'])
def register():
    
    # Get the user's name, email, and password from the form
    name = request.form.get('new_name')
    email = request.form.get('new_email')
    password = request.form.get('new_password')

    # If the user exists with the same email
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        
        # Return an error message
        return jsonify({"error": "User with this email already exists"}), 400


    # Check if the email ends with "@eduteacher.com"
    if email.endswith("@EDUteacher.com"):
        
        # Assign the role as teacher 
        role = 'teacher' 
    else:
        
        # Otherwise assign the role as student
        role = 'student'
        
    # Hash the user's password
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Create the new user with their name, email, hashed password, and role
    new_user = User(studentName=name, email=email, password=hashed_password, role=role)
    
    # Add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    # Return the html page
    return render_template('registration_success.html')

# Function to Handle User Login
@app.route("/login", methods=["POST"])
def login():

    # Get the user's email, and password from the form
    Email = request.form['email']
    Password = request.form['password']

    # Find the user's name via their email
    user = User.query.filter_by(email=Email).first()
 
    # Check if the email ends with "@type" and assign role at login
    if user is not None:
        if check_password_hash(user.password, Password):
            
            # If the email ends with "@admin.com"
            if Email.endswith("@admin.com"):
                
                # Assign the role as admin
                user.role = 'admin'
                
                # Redirect them to the corresponding URL (change to admin view)
                return redirect(url_for('admin', name=user.studentName))
            
            # Otherwise if the email ends with "@EDUteacher.com"
            elif Email.endswith("@EDUteacher.com"):
                
                # Assign the role as "teacher"
                user.role = 'teacher'
                
                # Redirect the User to the corresponding URL (teacher view still WIP)
                return redirect(url_for('portal', name=user.studentName))
            
            # Otherwise
            else:
                
                # Assign the role as "student"
                user.role = 'student'
                
            # Commit the changes to the database
            db.session.commit()

            # Redirect the user to the student_view
            return redirect(url_for('student_view', name = user.studentName))
        
        # Otherwise
        else:
            # Output an error message saying that the password is incorrect
            return jsonify({"error": "Password is not correct"}), 404
        
    # Otherwise
    else:
        
        # Ouptut an error message saying that either one, or both is invalid
        return jsonify({"error": "Invalid request: Email not found or invalid login credentials"}), 404

# Check to see that the user inputted is indeed a student
@app.route('/success/<name>')
def success(name):
    return 'Welcome student %s' % name

# Student View Route
@app.route('/student_view/<name>')
def student_view(name):
    
    # Find the user with the student name passed through
    student = User.query.filter_by(studentName=name).first()
    
    # This SHOULD automatically get the associated courses for said student
    courses = student.registrations

    # Renders our student.html view
    return render_template('student.html', student=student, courses=courses)

# # POST Method for student to add course (WIP waiting for backend)
# @app.route('/student/add_course', methods=['POST'])  
# def student_add_course():
    
#   # Get course name from the form
#   course_name = request.form['course_name']
#   course = Course.query.get(course_name)

#   # If no seats are available
#   if course.remaining_seats <= 0:
      
#       # Ouput a flash message to show that there are no seats available
#       flash('No seats available for this course')
      
#       # And redirect to the student view
#       return redirect(url_for('student_view'))

#   # Create new registration by linking student's name (from session) with the course they select
#   registration = Registration(student_name=session['student_name'], course_name=course_name)
  
#   # Add registration to the database and Commit changes to the database
#   db.session.add(registration)
#   db.session.commit()
  
#   # Output a flash message to show success 
#   flash('Added course successfully')
  
#   # Redirect to the student view
#   return redirect(url_for('student_view'))

# # POST method for students to drop the course  (WIP waiting fro backend)
# @app.route('/student/drop', methods=['POST'])
# def student_drop():
    
#   # Get course name to drop the course 
#   course_name = request.form['course_name']

#   # Find the corresponding registration of the student and the course
#   registration = Registration.query.filter_by(student_name=session['student_name'], course_name=course_name).first()
  
#   # Delete the registration from the database and commit changes
#   db.session.delete(registration)
#   db.session.commit()
  
#   # Output a flash message to show succes
#   flash('Dropped course successfully')
  
#   # Redirect to the student_view 
#   return redirect(url_for('student_view'))

# Check to see that the user inputted is indeed a teacher
@app.route('/portal/<name>')
def portal(name):
    return 'Welcome teacher %s' % name

# Check to see that the user inputted is indeed an admin
@app.route('/admin/<name>')
def admin(name):
    return 'Welcome admin %s' % name


# Run app with debugger on
if __name__ == '__main__':
    app.run(debug=True)


# NOTES:

# Link to web Address:
# http://127.0.0.1:5000/

#Imports:
#might need later, maybe not
#from flask_cors import CORS
#CORS(app, supports_credentials=True)
#import json

# Running:
#flask --app app run   use this to run app

# Password + User:
#  User('Admin@ucmerced.edu', 'AdminPassword10')
# login: Admin@ucmerced.edu
# password: AdminPassword10


# Venv Install:
#install//
# pip install Flask
# pip install flask-admin
# pip install -U Flask-SQLAlchemy
# pip install Flask-Admin[sqla]
# pip install Werkzeug   

# Database Creation:
# create_db.py
#from app import db
#db.create_all()

# how to add in to database using terminal: 
#>>> from app import app      use this to avoid error
#>>> from app import db
#>>> from app import User
#>>> user1 = User(email='Admin@ucmerced.edu', password='AdminPassword10')
#>>> db.session.add(user1)
#>>> db.session.commit()