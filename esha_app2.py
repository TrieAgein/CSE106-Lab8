from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
app.config["SECRET_KEY"] = "mysecret"
db = SQLAlchemy(app)
admin = Admin(app)

app.app_context().push() # without this, I recieve flask error


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    studentName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    role = db.Column(db.String(20), default='student')

    def __repr__(self): # how database relationship User is printed out
       return f"s: '{self.studentName}'"

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacherName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    role = db.Column(db.String(20), default='teacher')
    courses = db.relationship("Course", back_populates="teacher")

    def __repr__(self):
        return f"T: {self.teacherName} "

class AdminLogin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='admin')


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student = db.relationship('User', backref=db.backref('enrollments', lazy=True))
    
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    course = db.relationship('Course', backref=db.backref('enrollments', lazy=True))
    
    grade = db.Column(db.Float, nullable=False, default=100.0)
    __table_args__ = (
        CheckConstraint('grade >= 0.0 AND grade <= 100.0', name='grade_range_check'),
    )


# second database = "course name, teacher, time, students enrolled"
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    courseName = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable = False)

    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    teacher = db.relationship("Teacher", back_populates="courses" )

    def __repr__(self): # how database User is printed out
        return f"Course: '{self.courseName}'"

#  ------------------------------------------------------------------------------------------  #

class UserView(ModelView):
    #pass
    form_columns = ["studentName", "email", "password", "role"]  #should not display passwords
    column_list = ["studentName","email" ,"password", "role"]
    form_args = {
        'studentName': {
            'label': 'Student Name',
            'description': 'Enter students full name.'
        },
        'email': {
            'label': 'Student Email',
            'description': 'Enter students email.'
        },
        'password': {
            'label': 'Password',
            'description': 'Enter password.'
        },
        'role': {
            'label': 'Role',
            'description': 'Students default role is "student".',
        },

    }

class TeacherView(ModelView):
    #pass
    form_columns = ["teacherName", "email", "password", "role"]  #should not display passwords
    column_list = ["teacherName", "email", "password", "role"]
    form_args = {
        'teacherName': {
            'label': 'Teachers Name',
            'description': 'Enter teachers full name.'
        },
        'email': {
            'label': 'Teacher Email',
            'description': 'Enter teachers email. (fomat "@EDUteacher.org" )'
        },
        'password': {
            'label': 'Password',
            'description': 'Enter password.'
        },
        'role': {
            'label': 'Role',
            'description': 'Teachers default role is "teacher".',
        },

    }

class CourseView(ModelView):
    #pass
    form_columns = ["courseName", "teacher", "time", "capacity"]
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
        'teacher': {
            'label': 'Teacher',
            'description': 'Select the teacher for this course.',
        },

    }
    column_formatters = { #changes how 'teacher' it displays in flask_admin /Course tab
        'teacher': lambda v, c, m, p: f'{m.teacher.teacherName} ({m.teacher.email})' if m.teacher else None
    }



class EnrollmentView(ModelView):
    #pass
    form_columns = ["student", "course", "grade" ]  
    column_list = ["student", "course", "grade" ]
    form_args = {
        'student': {
            'label': 'Student',
            'description': 'Select the student joining a course.'
        },
        'course': {
            'label': 'Course',
            'description': 'Select the course student is joining'
        },
        'grade': {
            'label': 'Grade',
            'description': 'Input a grade (deafult = "100" since student is new).'
        },
    }


admin.add_view(UserView(User, db.session))
admin.add_view(TeacherView(Teacher, db.session))
admin.add_view(CourseView(Course, db.session))
admin.add_view(EnrollmentView(Enrollment, db.session))
admin.add_view(ModelView(AdminLogin, db.session))

@app.route('/')
def launch():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('index.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/run')
def run():
	return "<p>Is indeed running page</p>"


# Function to register a new user // can only register new students or teachers
@app.route('/register_backend', methods=['POST'])
def register_backend():

    name = request.form.get('new_name')
    email = request.form.get('new_email')
    password = request.form.get('new_password')

    account_type = request.form.get('account_type') #teacher or student input

    if account_type == "teacher":
        existing_user = Teacher.query.filter_by(email=email).first()
        if not email.endswith("@EDUteacher.org"):
            return jsonify({"error": "Incorrect teacher email handle"}), 400

    else:
        existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 400


    # Check if the email ends with "@eduteacher"
    if email.endswith("@EDUteacher.org"):
        role = 'teacher'
    else:
        role = 'student'

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    if account_type == "teacher":
        new_user = Teacher(teacherName=name, email=email, password=hashed_password, role=role)
    else:
        new_user = User(studentName=name, email=email, password=hashed_password, role=role)

    db.session.add(new_user)
    db.session.commit()

    return render_template('index.html')


@app.route("/login_backend", methods=["POST"])
def login_backend():

    Email = request.form['email']
    Password = request.form['password']

    if Email.endswith("@EDUteacher.org"):
        user = Teacher.query.filter_by(email=Email).first()

    elif Email.endswith("@admin"):
        user = AdminLogin.query.filter_by(email=Email).first()

    else:
        user = User.query.filter_by(email=Email).first()
 
    # Check if the email ends with "@type" and assign role at login
    if user is not None:
        if check_password_hash(user.password, Password):
            if Email.endswith("@admin"):
                # role is 'admin'                   #this line is where token verification would go
                return redirect(url_for('admin'))

            elif Email.endswith("@EDUteacher.org"):
                # role is 'teacher'                 #this line is where token verification would go
                return redirect(url_for('portal', name=user.teacherName))

            else:
                pass
                # role is 'student'                 #this line is where token verification would go


            #return f"Logged in as {user.username} with role {user.role}"
            return redirect(url_for('student_view', name=user.studentName))

        else:
            return jsonify({"error": "Password is not correct"}), 404
    else:
        return jsonify({"error": "Invalid request: Email not found or invalid login credentials"}), 404


def loadstudent(name):
    student = User.query.filter_by(studentName=name).first()
    return student

@app.route('/student_view/<name>')
def student_view(name):
    
    student = User.query.filter_by(studentName=name).first()
    
    enrollments = Enrollment.query.filter_by(student=student).all()

    courses = [enrollment.course for enrollment in enrollments]

    # You need to pass the 'courses' and 'current_user' to the template
    return render_template('student.html', student=student, courses=courses, current_user=student)


@app.route('/all_courses/<name>')
def all_courses(name):
    
    student = User.query.filter_by(studentName=name).first()
    
    # Retrieve all available courses
    all_courses = Course.query.all()
    
    return render_template('studentall.html', student=student, courses=all_courses, current_user = student)

@app.route('/add_course/<int:course_id>', methods=['POST'])
def add_course(course_id):

  course = Course.query.get(course_id)
  name = request.form['name']
  student = loadstudent(name)
  
  existing = Enrollment.query.filter_by(student=student, course=course).first()
  if existing:
      flash("Already enrolled in this course!")
      return redirect(url_for('all_courses', name=name))
  
  if course.capacity > len(course.enrollments):
    
    enrollment = Enrollment(student=student, course=course)
    db.session.add(enrollment)  
    db.session.commit()

  else:
    flash('The course is currently full.')

  return redirect(url_for('all_courses', name = name))


@app.route('/drop_course/<int:course_id>', methods=['POST'])
def drop_course(course_id):
    course = Course.query.get(course_id)
    name = request.form['name']
    student = loadstudent(name)

    enrollment = Enrollment.query.filter_by(student=student, course=course).first()

    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()
        return redirect(url_for('all_courses', name=name))
    else:
        flash('You are not enrolled in this course.')
        return redirect(url_for('all_courses', name=name))



@app.route('/portal/<name>')
def portal(name):
    return 'Welcome teacher %s' % name



# @app.route('/register_course/<int:course_id>', methods=['POST'])
# def register_course(course_id):
#     course = Course.query.get(course_id)

#     if course.capacity > 0:
#         # Decrease the capacity
#         course.capacity -= 1

#         # Get the currently logged in user (you need to implement user authentication)
#         user = User.query.get(current_user.id)

#         # Create enrollment
#         enrollment = Enrollment(student=user, course=course)

#         # Add to the database
#         db.session.add(enrollment)
#         db.session.commit()

#         return redirect(url_for('home'))
#     else:
#         return "Course is full!"


if __name__ == '__main__':
    db.create_all()
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

# Notes 

#install//
# pip install Flask
# pip install flask-admin
# pip install -U Flask-SQLAlchemy
# pip install Flask-Admin[sqla]
# pip install Werkzeug

# pip install blinker==1.6.2 click==8.1.6 Flask==2.3.2 Flask-Admin==1.6.1 Flask-SQLAlchemy==3.0.5 greenlet==2.0.2 itsdangerous==2.1.2 Jinja2==3.1.2 MarkupSafe==2.1.3 SQLAlchemy==2.0.19 typing_extensions==4.7.1 Werkzeug==2.3.6 WTForms==3.0.1
# run this^ will install all thee right packages for this program


### how to delete or create db. type into terminal
#  flask shell
# >>>
# >>> from app import db
# >>> db.drop_all()
# >>> db.create_all()
# >>> exit()

# flask --app app run   use this to run app


### how to add in to database using terminal.
#>>> from app import app      use this to avoid error
#>>> from app import db
#>>> from app import User
#>>> user1 = User(studentName="student1",email="somethin@gmail" ,password="something",role="student")
#>>> db.session.add(user1)
#>>> db.session.commit()


# when in the database, if you have a student in enrollment db, or a teacher in Course db.
# you have to delete first from where studen is in enrollement, then you can delete student,
# you have to delete the course the teacher is teaching first before you delete teacher.
