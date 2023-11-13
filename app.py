from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.ajax import QueryAjaxModelLoader
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user, login_required
from datetime import datetime

#flask --app app run   use this to run app
# http://127.0.0.1:5000/ # link to webaddress

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
app.config["SECRET_KEY"] = "mysecret"
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' #routes to this when unauthenticated


@login_manager.user_loader
def load_user(user_id):
    check = session.get('admin', None)
    check2 = session.get('teacher', None)
    if check == True:
        return AdminLogin.query.get(int(user_id))
    elif check2 == True:
        return Teacher.query.get(int(user_id))
    else:
        return User.query.get(int(user_id))


app.app_context().push() # without this, I recieve flask error


#  ------------------------------------------------------------------------------------------  #

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    studentName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    role = db.Column(db.String(20), default='student')

    def __repr__(self): # how database relationship User is printed out
       return f"s: '{self.studentName}'"

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        # Replace with your authentication logic
        return True

    @property
    def is_active(self):
        # Replace with your activation logic
        return True


class Teacher(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    teacherName = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    role = db.Column(db.String(20), default='teacher')
    courses = db.relationship("Course", back_populates="teacher")

    def __repr__(self):
        return f"T: {self.teacherName} "

    @property
    def is_active(self):
        # For simplicity, always consider the teacher account as active
        return True

    def get_id(self):
        return str(self.id)

class AdminLogin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='admin')
    login_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):
        # For simplicity, always consider the teacher account as active
        return True

    def get_id(self):
        return str(self.id)


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
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
    #pass
    form_columns = ["studentName", "email", "password", "role"]  
    column_list = ["studentName","email" , "role"]      #should not display passwords
    #####column_list = ["studentName", "email", "password" "role"]#### this is onlyincase to show hashing
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
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
    #pass
    form_columns = ["teacherName", "email", "password", "role"]  
    column_list = ["teacherName", "email", "role"]  #should not display passwords
    form_args = {
        'teacherName': {
            'label': 'Teachers Name',
            'description': 'Enter teachers full name.'
        },
        'email': {
            'label': 'Teacher Email',
            'description': 'Enter teachers email. (fomat "@EDUteacher" )'
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
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
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
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'
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

class AdminLoginView(ModelView):
    # def is_accessible(self):
        # return current_user.is_authenticated and current_user.role == 'admin'
    pass

from flask import current_app

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):   #changing index to another name breaks admin permission access
        role = session.get('role', None)

        if current_user.is_authenticated:
            print(f"----email-----{current_user.email}")
            print(f"----role-----{current_user.role}")
            print(f"----session.role-----{role}")

            if current_user.role == 'admin' and role == 'admin':
                # Print the session role before redirecting
                return super(MyAdminIndexView, self).index()
            else:
                flash('You do not have permission to access this page.')
                return redirect(url_for('login'))

        else:
            flash('You have to login.')
            return redirect(url_for('login'))


admin = Admin(app, index_view=MyAdminIndexView())


admin.add_view(UserView(User, db.session))
admin.add_view(TeacherView(Teacher, db.session))
admin.add_view(CourseView(Course, db.session))
admin.add_view(EnrollmentView(Enrollment, db.session))
admin.add_view(AdminLoginView(AdminLogin, db.session))

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
            # return jsonify({"error": "Incorrect teacher email handle"}), 400
            flash('Incorrect teacher email handle')
            return redirect(url_for("register"))

    elif account_type == "student":
        existing_user = Teacher.query.filter_by(email=email).first()
        existing_user2 = AdminLogin.query.filter_by(email=email).first()
        if existing_user or existing_user2:
            flash('Email is already registered.', 'login')
            return redirect(url_for("register"))

        if email.endswith("@EDUteacher.org"):
            flash('invalid student email domain.')
            return redirect(url_for("register"))   

    else:
        existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        flash('Email address already exists:', 'login')
        return redirect(url_for("register"))
        #return jsonify({"error": "User with this email already exists"}), 400


    # Check if the email ends with "@eduteacher.org"
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

    return render_template('registration_success.html')


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
        if not user.password.startswith('$pbkdf2'):

            if (user.password == Password):
                print("passed commited!")
                hashed_password = generate_password_hash(Password, method='pbkdf2:sha256')
                user.password = hashed_password
                db.session.commit()

        if check_password_hash(user.password, Password):

            # login_user(user, remember=True)  # Use Flask-Login's login_user function here
            # print(f"----login_user--print-----{current_user}")


            if Email.endswith("@admin"):
                login_user(user, remember=True)
                session['role'] = 'admin'
                session['email'] = Email
                session['admin'] = True
                session['teacher'] = False

                print(f"----login_user--print-----{current_user}")

                # session_role = session.get('role')
                # print(f"---F---Session Role: {session_role}")
                # print(f"---admin-Email---: {user.email}")

                return redirect(url_for('admin.index')) #this is how the admin redirect is set up

            elif Email.endswith("@EDUteacher.org"):
                login_user(user, remember=True)
                session['role'] = 'teacher'
                session['email'] = Email
                session['teacher'] = True
                session['admin'] = False
                session['id'] = user.id

                print(f"----login_user--print-----{current_user}")
                return redirect(url_for('teacher_view', teacher_id=user.id))

            else:
                login_user(user, remember=True)
                session['role'] = 'student'
                session['email'] = Email
                session['admin'] = False
                session['teacher'] = False

                #return f"Logged in as {user.username} with role {user.role}"
                return redirect(url_for('student_view', name=user.studentName))

        else:
            flash('Password is incorrect: try again')
            return redirect(url_for("login"))
            #return jsonify({"error": "Password is not correct"}), 404
    else:
        flash('Email not found or invalid login credentials')
        return redirect(url_for("login"))
        #return jsonify({"error": "Invalid request: Email not found or invalid login credentials"}), 404


# --------------------------------------------------------------------------------------------------------------- #


# Function to load a student's name
def loadstudent(name):

    student = User.query.filter_by(studentName=name).first()
    return student


# Student: View
@app.route('/student_view/<name>')
@login_required
def student_view(name):
    check = session.get('email', None)

    # Filter student by name
    student = User.query.filter_by(studentName=name).first()

    if student.email != check:
        flash('You do not have access to this page.')
        return abort(403) # Abort the request with a 403 Forbidden error
    
    # Find what classes they are enrolled into
    enrollments = Enrollment.query.filter_by(student=student).all()
    
    # Extract courses and grades from the student's enrollment
    courses_with_grades = [(enrollment.course, enrollment.grade) for enrollment in enrollments]

    # Render it into student html
    return render_template('student.html', student=student, courses_with_grades=courses_with_grades, current_user=student)


# Student: Display all courses
@app.route('/all_courses/<name>')
@login_required
def all_courses(name):

    check = session.get('email', None)
    
    # Filter student by name
    student = User.query.filter_by(studentName=name).first()

    if student.email != check:
        flash('You do not have access to this page.')
        return abort(403) # Abort the request with a 403 Forbidden error
    
    # Retrieve all available courses
    all_courses = Course.query.all()
    
    # Return into student all html
    return render_template('studentall.html', student=student, courses=all_courses, current_user = student)


# Student: Add a Course
@app.route('/add_course/<int:course_id>', methods=['POST'])
def add_course(course_id):
    
    # Get course by ID
    course = Course.query.get(course_id)
    
    # Get student name from request form
    name = request.form['name']
    
    # Load student by name
    student = loadstudent(name)
    
    # Check if an existing student is enrolled
    existing_student = Enrollment.query.filter_by(student=student, course=course).first()
    if existing_student:
        flash("Already enrolled in this course!")
        return redirect(url_for('all_courses', name=name))
    
    # Check if course has capacity
    if course.capacity > len(course.enrollments):
        enrollment = Enrollment(student=student, course=course)
        db.session.add(enrollment)  
        db.session.commit()
        return redirect(url_for('all_courses', name = name))
    else:
        flash('The course is currently full.')
        return redirect(url_for('all_courses', name = name))


# Student: Drop Course
@app.route('/drop_course/<int:course_id>', methods=['POST'])
def drop_course(course_id):
    
    # Get course by ID
    course = Course.query.get(course_id)
    
    # Get student name from request form
    name = request.form['name']
    
    # Load student by name
    student = loadstudent(name)
    
    # Check if the student is enrolled in the course
    enrolled = Enrollment.query.filter_by(student=student, course=course).first()
    if enrolled:
        db.session.delete(enrolled)
        db.session.commit()
        return redirect(url_for('student_view', name=name))
    else:
        flash('You are not enrolled in this course.')
        return redirect(url_for('student_view', name=name))


# ----------------------------------------------------------------------------- #
# Teacher: View
@app.route('/teacher/<int:teacher_id>')
@login_required
def teacher_view(teacher_id):
    check = session.get('teacher', None)
    idCheck = session.get('id', None)

    if check != True or idCheck != teacher_id:
        flash('You do not have access to this page.')
        return abort(403) # Abort the request with a 403 Forbidden error

    # Get teacher by ID
    teacher = Teacher.query.get(teacher_id)  
    
    # Retrieve courses they teach
    courses = teacher.courses
    
    # Render info in teacher html
    return render_template('teacher.html', teacher=teacher, courses=courses)

# Teacher: Display all Enrollments
@app.route('/teacher/course/<int:course_id>')
@login_required
def teacher_all(course_id):
    check = session.get('teacher', None)

    if check != True:
        flash('You do not have access to this page.')
        return abort(403) # Abort the request with a 403 Forbidden error
    
    # Get course by ID
    course = Course.query.get(course_id)
    
    # Retrieve all students enrolled in the course
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()  
    
    # Retrieve teacher associated with the course
    teacher = course.teacher
    
    # Render information on teacherall html
    return render_template('teacherall.html', course=course, enrollments=enrollments, teacher=teacher)

# Teacher: Edit Grades
@app.route('/edit_grades', methods=['POST'])
def edit_grades():
    
    # Get course ID via form
    course_id = request.form.get('course_id')
    
    # Get course by ID
    course = Course.query.get(course_id)

    # Edit grades   based on form data
    for enrollment in course.enrollments:
        student_id = enrollment.student.id
        new_grade = request.form.get(f'grade_{student_id}')
        
        if new_grade is not None:  # Check if a grade is provided
            enrollment.grade = new_grade

    # Commit changes to database
    db.session.commit()

    # Redirect to teacher_all
    return redirect(url_for('teacher_all', course_id=course_id))


@app.route('/teacher/create_course', methods=['GET', 'POST'])
@login_required
def create_course():
    # Check if the logged-in user is a teacher
    if current_user.role != 'teacher':
        flash('You do not have permission to access this page.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        course_name = request.form['courseName']
        time = request.form['time']
        capacity = int(request.form['capacity'])

        # Create a new course and associate it with the logged-in teacher
        new_course = Course(courseName=course_name, time=time, capacity=capacity, teacher=current_user)
        db.session.add(new_course)
        db.session.commit()

        flash('New course created successfully!')
        return redirect(url_for('teacher_view', teacher_id=current_user.id))

    return render_template('teachercourse.html', teacher=current_user)

import pytz

@app.route('/logout')
@login_required
def logout():

    role = session.get('role', None)
    if role == 'admin':
        current_user.login_timestamp = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
        # current_user.login_timestamp = current_user.login_timestamp.remove('GMT')
        db.session.commit()

    logout_user()
    print(f"---LOGOUT---Session Role: {role}")
    print("-----Loged--out-------")

    session['role'] = None
    session['email'] = None
    session['teacher'] = None
    session['admin'] = None
    session['id'] = None

    flash('You have been successfully logged out.')
    return redirect(url_for("login"))



# Route to get the count of students
@app.route('/get_student_count', methods=['GET'])
def get_student_count():
    student_count = User.query.filter_by(role='student').count()
    return jsonify(student_count=student_count)

# Route to get the count of students
@app.route('/get_teacher_count', methods=['GET'])
def get_teacher_count():
    teacher_count = Teacher.query.filter_by(role='teacher').count()
    return jsonify(teacher_count=teacher_count)

@app.route('/admin_timestamp', methods=['GET'])
def admin_timestamp():
    admin_user = AdminLogin.query.get(current_user.id)
    login_timestamp = admin_user.login_timestamp
    
    # Convert to 'US/Pacific' time zone and format without GMT offset
    pacific_time = login_timestamp.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Pacific'))
    formatted_timestamp = pacific_time.strftime('%a, %d %b %Y %H:%M:%S')

    return jsonify(login_timestamp=formatted_timestamp)


@app.route('/courses_offered', methods=['GET'])
def courses_offered():
    courses = Course.query.count()
    return jsonify(courses=courses)

@app.route('/enrollments', methods=['GET'])
def enrollments():
    enrolled = Enrollment.query.count()
    return jsonify(enrolled=enrolled)

if __name__ == '__main__':
    app.run(debug=True)




# Notes 

#install//
# pip install Flask
# pip install flask-admin
# pip install -U Flask-SQLAlchemy
# pip install Flask-Admin[sqla]
# pip install Werkzeug            #do not pip install individually! copy and paste line 334 right below

# pip install blinker==1.6.2 click==8.1.6 Flask==2.3.2 Flask-Admin==1.6.1 Flask-SQLAlchemy==3.0.5 greenlet==2.0.2 itsdangerous==2.1.2 Jinja2==3.1.2 MarkupSafe==2.1.3 SQLAlchemy==2.0.19 typing_extensions==4.7.1 Werkzeug==2.3.6 WTForms==3.0.1 flask_login==23.2.1
# pip install flask-bcrypt
# pip install pytz
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