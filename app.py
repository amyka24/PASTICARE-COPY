import os
import random
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask import jsonify
import pdfkit
from flask import make_response, render_template
import re
from sqlalchemy import func


app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/pasti'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db) 
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=True)  # Add this
    profile_picture = db.Column(db.String(200), nullable=True) 
    role = db.Column(db.String(10), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'

def generate_student_code():
    prefix = "ST"
    random_numbers = random.randint(10000, 99999)
    return f"{prefix}{random_numbers}"

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)
    student_code = db.Column(db.String(8), unique=True, nullable=False, default=lambda: generate_student_code())

     # New fields
    address = db.Column(db.String(200), nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    ambition = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Student {self.name}>'
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    subcategories = db.relationship('SubCategory', backref='category', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.name}>"


class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    milestones = db.relationship('Milestone', backref='subcategory', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SubCategory {self.name} under {self.category.name}>"


class Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=False)
    target_period = db.Column(db.String(20))
    added_by_teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    is_default = db.Column(db.Boolean, default=True)
    
    progress = db.relationship('StudentProgress', backref='milestone', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Milestone {self.description[:30]}...>"


class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    milestone_id = db.Column(db.Integer, db.ForeignKey('milestone.id'), nullable=False)
    status = db.Column(db.String(20), default="Not Started")  # Could be: Not Started, In Progress, Achieved
    date_updated = db.Column(db.Date, default=db.func.current_date())
    note = db.Column(db.Text, nullable=True)

    student = db.relationship("Student", backref="progress_records")

    def __repr__(self):
        return f"<Progress Student={self.student_id} Milestone={self.milestone_id} Status={self.status}>"
    
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Event {self.title} on {self.date}>"
    
class ClassWallPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Post {self.title}>"
    
    # in ClassWallPost model
    user = db.relationship('User')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    post_id = db.Column(db.Integer, db.ForeignKey('class_wall_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    mentions = db.Column(db.String(255))

    user = db.relationship("User", backref="comments")
    post = db.relationship("ClassWallPost", backref="comments")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_phone = request.form.get("username_or_phone")
        password = request.form.get("password")
        user = User.query.filter_by(username=username_or_phone, role='teacher').first()

        if not user:
            # If the user is not a teacher, check if it's a parent
            user = User.query.filter_by(username=username_or_phone, role='parent').first()

        if not user:
            student = Student.query.filter(
                (Student.phone_number == username_or_phone) | (Student.student_code == username_or_phone)
            ).first()

            if student:
                user = User.query.filter_by(student_id=student.id, role='parent').first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            # Redirect based on role
            if user.role == 'teacher':
                return redirect(url_for("teacher_dashboard"))
            elif user.role == 'parent':
                return redirect(url_for("parent_dashboard"))
        return "Login failed. Please check your credentials."
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/register_acc", methods=["GET"])
def register_acc():
    message = request.args.get("message")
    return render_template("registeracc.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")
    student_code = request.form.get("student_code", None)  # For parent, we need the student code
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

 # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return render_template("registeracc.html", message="❌ Username is already taken. Please choose another.")

    # If the role is 'parent', we check if the student code exists
    student_id = None
    if role == 'parent' and student_code:
        student = Student.query.filter_by(student_code=student_code).first()
        if student:
            student_id = student.id
        else:
            return "Invalid student code. Please check the student code and try again."

    # Create a new user
    new_user = User(username=username, password=hashed_password, role=role, student_id=student_id)
    db.session.add(new_user)
    db.session.commit()

    return redirect("/login")


@app.route("/")
@login_required
def home():
    # Redirect to the appropriate dashboard based on role
    if current_user.role == 'teacher':
        return redirect(url_for("teacher_dashboard"))
    elif current_user.role == 'parent':
        return redirect(url_for("parent_dashboard"))
    return "Access Denied."

@app.route("/teacher_dashboard")
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        return "Access Denied."
    students = Student.query.all()
    return render_template("teacher_dashboard.html", user=current_user, students=students)
    
from datetime import date

@app.route("/parent_dashboard")
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        return "Access Denied."
    
    student = Student.query.get(current_user.student_id)

    if not student:
        return "Your child is no longer listed in the system, and you no longer have access to this platform. If you believe this is an error, please contact the administrator for assistance."

    # Directly use Event since it's already defined in this file
    today = date.today()
    upcoming_event = Event.query.filter(Event.date >= today).order_by(Event.date.asc()).first()

    # Get milestone progress
    progress = (
        db.session.query(StudentProgress, Milestone, SubCategory, Category)
        .join(Milestone, StudentProgress.milestone_id == Milestone.id)
        .join(SubCategory, Milestone.subcategory_id == SubCategory.id)
        .join(Category, SubCategory.category_id == Category.id)
        .filter(StudentProgress.student_id == student.id)
        .all()
    )

    progress_data = []
    for sp, milestone, subcat, cat in progress:
        progress_data.append({
            "category": cat.name,
            "subcategory": subcat.name,
            "milestone": milestone.description,
            "status": sp.status
        })

    # 🎉 New: pick a random Good or Excellent milestone for highlight
    highlight = None
    highlight_items = [p['milestone'] for p in progress_data if p['status'] in ['Good', 'Excellent']]
    if highlight_items:
        highlight = random.choice(highlight_items)

    return render_template(
        "parent_dashboard.html",
        user=current_user,
        student=student,
        highlight=highlight,
        upcoming_event=upcoming_event
    )



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/register_student", methods=["GET"])
def show_register_student_form():
    return render_template("registerstudent.html", user=current_user)

@app.route("/register_student", methods=["POST"])
def register_student():
    name = request.form.get("name")
    nickname = request.form.get("nickname")
    date_of_birth = request.form.get("date_of_birth")
    parent_name = request.form.get("parent_name")
    phone_number = request.form.get("phone_number")
    email = request.form.get("email")
    profile_picture = None
    
    # Handle file upload
    if "profile_picture" in request.files:
        file = request.files["profile_picture"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_picture = filename

    if name and date_of_birth and parent_name and phone_number and email:
        new_student = Student(
            name=name,
            nickname=nickname,
            date_of_birth=date_of_birth,
            parent_name=parent_name,
            phone_number=phone_number,
            email=email,
            profile_picture=profile_picture
        )
        db.session.add(new_student)
        db.session.commit()
        return redirect("/")

    return "Failed to register student. All fields must be filled out."

@app.route("/delete_student", methods=["POST"])
def delete_student():
    data = request.get_json()
    student_ids = data.get("student_ids", [])
    
    if student_ids:
        try:
            # Unlink parent accounts associated with the students
            for student_id in student_ids:
                parent_user = User.query.filter_by(student_id=student_id, role="parent").first()
                if parent_user:
                    parent_user.student_id = None
            
            # Delete the students
            Student.query.filter(Student.id.in_(student_ids)).delete(synchronize_session=False)
            db.session.commit()
            return {"success": True}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    return {"success": False, "error": "No student IDs provided"}, 400

@app.route('/student/<int:student_id>')
@login_required
def student_profile(student_id):
    student = Student.query.get_or_404(student_id)

    # Count progress by status
    status_counts = (
        db.session.query(StudentProgress.status, db.func.count(StudentProgress.id))
        .filter_by(student_id=student_id)
        .group_by(StudentProgress.status)
        .all()
    )

    progress_data = {'Weak': 0, 'Good': 0, 'Excellent': 0}
    for status, count in status_counts:
        progress_data[status] = count

    return render_template('student_profile.html',
                           student=student,
                           progress_data=progress_data,
                           user=current_user)

@app.route('/student/<int:student_id>/progress_summary_data')
@login_required
def student_progress_summary_data(student_id):
    student = Student.query.get_or_404(student_id)

    subcategories = db.session.query(SubCategory).all()
    result = []

    for subcat in subcategories:
        total_milestones = Milestone.query.filter_by(subcategory_id=subcat.id).count()

        if total_milestones == 0:
            continue

        completed = StudentProgress.query.filter_by(
            student_id=student.id
        ).join(Milestone).filter(
            Milestone.subcategory_id == subcat.id
        ).count()

        percent = round((completed / total_milestones) * 100)

        result.append({
            'category': subcat.category.name,
            'subcategory': subcat.name,
            'percentage': percent
        })

    return jsonify(result)


@app.route('/edit_student/<int:student_id>', methods=['GET'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('editstuprofile.html', student=student, user=current_user)

@app.route('/update_student/<int:student_id>', methods=['POST'])
def update_student(student_id):
    student = Student.query.get_or_404(student_id)

    student.name = request.form['name']
    student.nickname = request.form.get('nickname')
    student.date_of_birth = request.form['date_of_birth']
    student.parent_name = request.form['parent_name']
    student.phone_number = request.form['phone_number']
    student.email = request.form['email']
    student.address = request.form.get('address')
    student.allergies = request.form.get('allergies')
    student.ambition = request.form.get('ambition')

    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            student.profile_picture = filename

    db.session.commit()
    return redirect(url_for('student_profile', student_id=student.id))
    return render_template('editstuprofile.html', student=student, user=current_user)

@app.route('/edit_student_parent/<int:student_id>', methods=['GET'])
@login_required
def edit_student_parent(student_id):
    if current_user.role != 'parent':
        return "Access Denied."

    student = Student.query.get_or_404(student_id)

    return render_template('editstuprofile_parent.html', student=student, user=current_user)


@app.route('/update_student_parent/<int:student_id>', methods=['POST'])
@login_required
def update_student_parent(student_id):
    if current_user.role != 'parent':
        return "Access Denied."

    student = Student.query.get_or_404(student_id)

    student.name = request.form['name']
    student.nickname = request.form.get('nickname')
    student.date_of_birth = request.form['date_of_birth']
    student.parent_name = request.form['parent_name']
    student.phone_number = request.form['phone_number']
    student.email = request.form['email']
    student.address = request.form.get('address')
    student.allergies = request.form.get('allergies')
    student.ambition = request.form.get('ambition')

    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            student.profile_picture = filename

    db.session.commit()
    return redirect(url_for('parent_dashboard'))

#Edit Profile Route 
@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if current_user.role not in ['parent', 'teacher']:
        return "Access Denied."

    if request.method == "POST":
        name = request.form.get("name")
        file = request.files.get("profile_picture")

        if name:
            current_user.name = name

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            current_user.profile_picture = filename

        db.session.commit()

        # Redirect based on role
        if current_user.role == 'parent':
            return redirect(url_for("parent_dashboard"))
        elif current_user.role == 'teacher':
            return redirect(url_for("teacher_dashboard"))

    return render_template("accountprofile.html", user=current_user)


#Track Progress Route

@app.route('/track_progress')
@login_required
def track_progress():
    categories = Category.query.all()
    subcategories = SubCategory.query.all()
    students = Student.query.all()  # ← Add this line
    return render_template('trackprogress_tchr.html',
                           categories=categories,
                           subcategories=subcategories,
                           students=students,  # ← Pass this to template
                           user=current_user)

# ---------------------------
# Track Progress - Main Page
# ---------------------------

# ---------------------------
# Fetch Milestones via AJAX
# ---------------------------
@app.route('/get_milestones/<int:subcategory_id>')
@login_required
def get_milestones(subcategory_id):
    milestones = Milestone.query.filter_by(subcategory_id=subcategory_id).all()
    return jsonify([{"id": m.id, "description": m.description} for m in milestones])

# ---------------------------
# Assign Progress (Old Inline Method)
# ---------------------------
@app.route('/assign_progress', methods=['POST'])
@login_required
def assign_progress():
    student_id = request.form.get('student_id')
    milestone_ids = request.form.getlist('milestone_ids')
    statuses = request.form.getlist('statuses')

    for milestone_id, status in zip(milestone_ids, statuses):
        if not status:
            continue
        existing = StudentProgress.query.filter_by(student_id=student_id, milestone_id=milestone_id).first()
        if existing:
            existing.status = status
            existing.date_updated = db.func.current_date()
        else:
            new_progress = StudentProgress(
                student_id=student_id,
                milestone_id=milestone_id,
                status=status
            )
            db.session.add(new_progress)

    db.session.commit()
    return redirect(url_for('track_progress', success=1))


# ---------------------------
# Track Individual Milestone (New UX)
# ---------------------------
@app.route('/track_progress/milestone/<int:milestone_id>')
@login_required
def track_milestone(milestone_id):
    milestone = Milestone.query.get_or_404(milestone_id)
    students = Student.query.all()
    
    progress_map = {
        p.student_id: p.status
        for p in StudentProgress.query.filter_by(milestone_id=milestone_id).all()
    }

    return render_template('track_milestone.html',
                           milestone=milestone,
                           students=students,
                           progress_map=progress_map, 
                           user=current_user)


# ---------------------------
# Save Progress for Milestone
# ---------------------------
@app.route('/track_progress/milestone/<int:milestone_id>', methods=['POST'])
@login_required
def save_milestone_progress(milestone_id):
    students = Student.query.all()

    for student in students:
        status = request.form.get(f"status_{student.id}")
        if not status:
            continue

        existing = StudentProgress.query.filter_by(student_id=student.id, milestone_id=milestone_id).first()
        if existing:
            existing.status = status
            existing.date_updated = db.func.current_date()
        else:
            db.session.add(StudentProgress(student_id=student.id, milestone_id=milestone_id, status=status))

    db.session.commit()
    return redirect(url_for('track_milestone', milestone_id=milestone_id, success=1))


@app.route('/parent_progress')
@login_required
def parent_progress():
    if not current_user.student_id:
        return "Unauthorized", 403

    student_id = current_user.student_id

    progress = (
        db.session.query(StudentProgress, Milestone, SubCategory, Category)
        .join(Milestone, StudentProgress.milestone_id == Milestone.id)
        .join(SubCategory, Milestone.subcategory_id == SubCategory.id)
        .join(Category, SubCategory.category_id == Category.id)
        .filter(StudentProgress.student_id == student_id)
        .all()
    )

    progress_data = []
    for sp, milestone, subcat, cat in progress:
        progress_data.append({
            "category": cat.name,
            "subcategory": subcat.name,
            "milestone": milestone.description,
            "status": sp.status
        })

    # ✅ Safe counts & percentages
    total = len(progress_data)
    excellent = len([p for p in progress_data if p['status'] == 'Excellent'])
    good = len([p for p in progress_data if p['status'] == 'Good'])
    weak = len([p for p in progress_data if p['status'] == 'Weak'])

    excellent_pct = round((excellent / total) * 100) if total > 0 else 0
    good_pct = round((good / total) * 100) if total > 0 else 0
    weak_pct = round((weak / total) * 100) if total > 0 else 0

    return render_template(
        'student_progress_parent.html',
        progress=progress_data,
        user=current_user,
        excellent=excellent,
        good=good,
        weak=weak,
        excellent_pct=excellent_pct,
        good_pct=good_pct,
        weak_pct=weak_pct
    )


#Calendar Route

@app.route("/calendar")
@login_required
def calendar():
    if current_user.role != 'teacher':
        return "Access Denied."

    filter_option = request.args.get('filter', 'month')
    today = datetime.today()

    if filter_option == 'year':
        events = Event.query.filter(
            db.extract('year', Event.date) == today.year
        ).order_by(Event.date.asc()).all()
    else:  # default to 'month'
        events = Event.query.filter(
            db.extract('year', Event.date) == today.year,
            db.extract('month', Event.date) == today.month
        ).order_by(Event.date.asc()).all()

    return render_template("calendar_tchr.html",user=current_user, events=events, filter=filter_option)



from datetime import datetime

@app.route("/add_event_form")
@login_required
def add_event_form():
    if current_user.role != 'teacher':
        return "Access Denied."
    return render_template("addcalendar_tchr.html",user=current_user)


@app.route("/add_event", methods=["POST"])
@login_required
def add_event():
    if current_user.role != 'teacher':
        return "Access Denied."

    title = request.form.get("title")
    date = request.form.get("date")
    description = request.form.get("description")

    event = Event(title=title, date=datetime.strptime(date, "%Y-%m-%d"), description=description, created_by=current_user.id)
    db.session.add(event)
    db.session.commit()
    return redirect(url_for("calendar"))

@app.route("/delete_event/<int:event_id>", methods=["POST"])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.created_by != current_user.id:
        return "Unauthorized"
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("calendar"))

@app.route("/parent_calendar")
@login_required
def calendar_parent():
    if current_user.role != 'parent':
        return "Access Denied."

    filter_option = request.args.get('filter', 'month')
    today = datetime.today()

    if filter_option == 'year':
        events = Event.query.filter(
            db.extract('year', Event.date) == today.year
        ).order_by(Event.date.asc()).all()
    else:
        events = Event.query.filter(
            db.extract('year', Event.date) == today.year,
            db.extract('month', Event.date) == today.month
        ).order_by(Event.date.asc()).all()

    return render_template("calendar_parent.html", user=current_user, events=events, filter=filter_option)


# Class Wall route

@app.route("/class_wall", methods=['GET', 'POST'])
@login_required
def class_wall():
    if current_user.role != 'teacher':
        return "Access Denied."

    if request.method == 'POST':
        content = request.form.get('content')
        image = None

        # Handle image upload (if any)
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image = filename

        new_post = ClassWallPost(title='Class Update', content=content, image=image, created_by=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('class_wall'))

    posts = ClassWallPost.query.order_by(ClassWallPost.timestamp.desc()).all()
    parents = User.query.filter_by(role='parent').all()
    return render_template("classwall_tchr.html", user=current_user, posts=posts, users=parents)
  

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = ClassWallPost.query.get_or_404(post_id)

    if current_user.id != post.created_by:
        return "Unauthorized", 403

    # Delete associated comments first
    Comment.query.filter_by(post_id=post_id).delete()

    # Delete post image if exists
    if post.image:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('class_wall'))

@app.route("/comment/<int:post_id>", methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form.get('comment_content')
    if content:
        # Parse @mentions using regex
        mentions = []
        if '@' in content:
            usernames = re.findall(r'@(\w+)', content)
            if usernames:
                parents = User.query.filter(User.username.in_(usernames), User.role == 'parent').all()
                mentions = [str(p.id) for p in parents]

        # Create the comment object
        new_comment = Comment(
            content=content,
            post_id=post_id,
            user_id=current_user.id,
            mentions=','.join(mentions) if mentions else None
        )

        db.session.add(new_comment)
        db.session.commit()

    # Redirect according to role
    if current_user.role == 'teacher':
        return redirect(url_for('class_wall'))
    elif current_user.role == 'parent':
        return redirect(url_for('class_wall_parent'))
    return "Access Denied."


@app.route('/get_parents')
@login_required
def get_parents():
    term = request.args.get('term', '')
    post_id = request.args.get('post_id')
    
    # Get parents who are either:
    # 1. Parents of students in this class (if post is class-specific)
    # 2. Or all parents if it's a general post
    parents = User.query.filter(
        User.role == 'parent',
        User.username.ilike(f'%{term}%')
    ).limit(5).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'username': p.username
    } for p in parents])

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # Allow only the comment's owner or a teacher to delete
    if current_user.id != comment.user_id and current_user.role != 'teacher':
        return "Unauthorized", 403

    db.session.delete(comment)
    db.session.commit()

    # Redirect based on role
    if current_user.role == 'teacher':
        return redirect(url_for('class_wall'))
    elif current_user.role == 'parent':
        return redirect(url_for('class_wall_parent'))
    else:
        return "Access Denied."


@app.route("/parent_wall")
@login_required
def class_wall_parent():
    if current_user.role != 'parent':
        return "Access Denied."

    posts = ClassWallPost.query.order_by(ClassWallPost.timestamp.desc()).all()
    parents = User.query.filter_by(role='parent').all()
    return render_template("classwall_parent.html", user=current_user, posts=posts, users=parents)



#Generate Report Route 

@app.route('/generate_report')
@login_required
def generate_report():
    students = Student.query.all()
    return render_template('generate_report.html', students=students, user=current_user)

@app.route('/generate_report/individual/<int:student_id>')
@login_required
def generate_individual_report(student_id):
    student = Student.query.get_or_404(student_id)
    # Join progress data
    progress = (
        db.session.query(StudentProgress, Milestone, SubCategory, Category)
        .join(Milestone, StudentProgress.milestone_id == Milestone.id)
        .join(SubCategory, Milestone.subcategory_id == SubCategory.id)
        .join(Category, SubCategory.category_id == Category.id)
        .filter(StudentProgress.student_id == student_id)
        .all()
    )
    return render_template('report_preview_individual.html',
                           student=student,
                           progress=progress,
                           user=current_user)

from datetime import datetime

@app.route('/generate_report/individual/<int:student_id>/download')
@login_required
def download_individual_pdf(student_id):
    student = Student.query.get_or_404(student_id)

    progress = (
        db.session.query(StudentProgress, Milestone, SubCategory, Category)
        .join(Milestone, StudentProgress.milestone_id == Milestone.id)
        .join(SubCategory, Milestone.subcategory_id == SubCategory.id)
        .join(Category, SubCategory.category_id == Category.id)
        .filter(StudentProgress.student_id == student_id)
        .all()
    )

    # ✅ 1. Render HTML as a string
    html = render_template('report_pdf_template.html',
                           student=student,
                           progress=progress,
                           user=current_user,
                           now=datetime.now)

    # ✅ 2. Write HTML to a temporary file
    temp_file_path = 'temp_report.html'
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # ✅ 3. Generate PDF from that file (with local file access enabled)
    options = {
        'enable-local-file-access': None,
        'encoding': 'UTF-8'
    }

    pdf = pdfkit.from_file(temp_file_path, False, options=options)

    # ✅ 4. Return the generated PDF as a download
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={student.name}_report.pdf'
    return response

@app.route('/test_pdf_template')
def test_pdf_template():
    student = Student.query.first()
    progress = (
        db.session.query(StudentProgress, Milestone, SubCategory, Category)
        .join(Milestone, StudentProgress.milestone_id == Milestone.id)
        .join(SubCategory, Milestone.subcategory_id == SubCategory.id)
        .join(Category, SubCategory.category_id == Category.id)
        .filter(StudentProgress.student_id == student.id)
        .all()
    )
    return render_template('report_pdf_template.html',
                           student=student,
                           progress=progress,
                           user=current_user,
                           now=datetime.now)

@app.route('/generate_report/class')
@login_required
def generate_class_report():
    students = Student.query.all()

    all_progress = {}

    for student in students:
        progress = (
            db.session.query(StudentProgress, Milestone, SubCategory, Category)
            .join(Milestone, StudentProgress.milestone_id == Milestone.id)
            .join(SubCategory, Milestone.subcategory_id == SubCategory.id)
            .join(Category, SubCategory.category_id == Category.id)
            .filter(StudentProgress.student_id == student.id)
            .all()
        )
        all_progress[student] = progress

    return render_template('report_preview_class.html',
                           all_progress=all_progress,
                           user=current_user,
                           now=datetime.now)

@app.route('/generate_report/class/download')
@login_required
def download_class_pdf():
    students = Student.query.all()

    all_progress = {}
    for student in students:
        progress = (
            db.session.query(StudentProgress, Milestone, SubCategory, Category)
            .join(Milestone, StudentProgress.milestone_id == Milestone.id)
            .join(SubCategory, Milestone.subcategory_id == SubCategory.id)
            .join(Category, SubCategory.category_id == Category.id)
            .filter(StudentProgress.student_id == student.id)
            .all()
        )
        all_progress[student] = progress

    html = render_template('report_pdf_template_class.html',
                           all_progress=all_progress,
                           user=current_user,
                           now=datetime.now)

    options = {
        'enable-local-file-access': None,
        'encoding': 'UTF-8'
    }

    pdf = pdfkit.from_string(html, False, options=options)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=class_progress_report.pdf'
    return response

#delulu visualisation
@app.route('/generate_report/summary')
@login_required
def generate_summary_report():
    categories = Category.query.all()
    return render_template('report_summary.html', categories=categories, user=current_user)

from collections import defaultdict

@app.route('/generate_report/summary/data/<int:category_id>')
@login_required
def get_summary_data(category_id):
    subcategories = SubCategory.query.filter_by(category_id=category_id).all()
    summary_data = []

    for subcat in subcategories:
        milestones = Milestone.query.filter_by(subcategory_id=subcat.id).all()
        milestone_summary = []
        assessed_count = 0  # For progress bar

        for milestone in milestones:
            progress_counts = db.session.query(
                StudentProgress.status,
                db.func.count(StudentProgress.id)
            ).filter_by(milestone_id=milestone.id).group_by(StudentProgress.status).all()

            counts = {'Weak': 0, 'Good': 0, 'Excellent': 0}
            has_any_progress = False

            for status, count in progress_counts:
                counts[status] = count
                if count > 0:
                    has_any_progress = True

            if has_any_progress:
                assessed_count += 1  # This milestone has at least one entry

            milestone_summary.append({
                'milestone': milestone.description,
                'counts': counts
            })

        summary_data.append({
            'subcategory': subcat.name,
            'milestones': milestone_summary,
            'assessed_count': assessed_count,
            'total_milestones': len(milestones)
        })

    return jsonify(summary_data)


@app.route('/generate_report/summary/data/all')
@login_required
def get_all_summary_data():
    categories = Category.query.all()
    all_data = []

    for cat in categories:
        cat_block = {'category': cat.name, 'subcategories': []}
        subcategories = SubCategory.query.filter_by(category_id=cat.id).all()

        for subcat in subcategories:
            milestones = Milestone.query.filter_by(subcategory_id=subcat.id).all()
            milestone_summary = []
            assessed_count = 0

            for milestone in milestones:
                progress_counts = db.session.query(
                    StudentProgress.status,
                    db.func.count(StudentProgress.id)
                ).filter_by(milestone_id=milestone.id).group_by(StudentProgress.status).all()

                counts = {'Weak': 0, 'Good': 0, 'Excellent': 0}
                has_progress = False

                for status, count in progress_counts:
                    counts[status] = count
                    if count > 0:
                        has_progress = True

                if has_progress:
                    assessed_count += 1

                milestone_summary.append({
                    'milestone': milestone.description,
                    'counts': counts
                })

            cat_block['subcategories'].append({
                'subcategory': subcat.name,
                'milestones': milestone_summary,
                'assessed_count': assessed_count,
                'total_milestones': len(milestones)
            })

        all_data.append(cat_block)

    return jsonify(all_data)

from datetime import datetime, date

from datetime import datetime, date

@app.route('/generate_report/milestone_progress')
@login_required
def milestone_progress_report():
    today = date.today()

    period_map = {
        "January - March": date(today.year, 3, 31),
        "April - July": date(today.year, 7, 31),
        "August - November": date(today.year, 11, 30)
    }

    milestone_data = []

    categories = Category.query.all()
    for cat in categories:
        subcats = SubCategory.query.filter_by(category_id=cat.id).all()
        subcat_data = []

        for subcat in subcats:
            milestones = Milestone.query.filter_by(subcategory_id=subcat.id).all()
            milestone_list = []

            for milestone in milestones:
                target_label = milestone.target_period
                estimated_end_date = period_map.get(target_label)

                if StudentProgress.query.filter_by(milestone_id=milestone.id).first():
                    status = "Assessed"
                elif estimated_end_date and estimated_end_date < today:
                    status = "Overdue"
                else:
                    status = "Upcoming"

                milestone_list.append({
                    "description": milestone.description,
                    "target_period": target_label or "-",
                    "status": status
                })

            subcat_data.append({
                "name": subcat.name,
                "milestones": milestone_list
            })

        milestone_data.append({
            "name": cat.name,
            "subcategories": subcat_data
        })

    return render_template("report_milestone_progress.html", milestone_data=milestone_data, user=current_user)



#PERFORMANCE ANALYTICS
@app.route('/generate_report/student_insights')
@login_required
def student_insights():
    students = Student.query.all()
    insights = []

    for student in students:
        progress = StudentProgress.query.filter_by(student_id=student.id).all()

        total = len(progress)
        weak = sum(1 for p in progress if p.status == 'Weak')
        good = sum(1 for p in progress if p.status == 'Good')
        excellent = sum(1 for p in progress if p.status == 'Excellent')

        if total == 0:
            label = 'Not Assessed'
        else:
            weak_pct = (weak / total) * 100
            good_pct = (good / total) * 100
            excellent_pct = (excellent / total) * 100

            if weak_pct > 30:
                label = 'Needs Attention'
            elif good_pct + excellent_pct >= 70:
                label = 'Doing Well'
            else:
                label = 'Moderate'

        insights.append({
            "student": student,
            "total": total,
            "excellent": excellent,
            "good": good,
            "weak": weak,
            "label": label
        })

    return render_template('report_student_insights.html', insights=insights, user=current_user)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)