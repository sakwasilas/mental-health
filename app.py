from flask import Flask, render_template, request, redirect, session, url_for, flash
from connections import SessionLocal
from functools import wraps
from models import User,Issue,ChatMessage

app = Flask(__name__)
app.secret_key = "mental_health_secret_key"


# ---------------------------------------------------
# Role Protection Wrappers
# ---------------------------------------------------

def user_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        if "role" not in session or session["role"] != "user":
            flash("Access denied")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return wrapper


def counselor_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        if "role" not in session or session["role"] != "counselor":
            flash("Access denied")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        if "role" not in session or session["role"] != "admin":
            flash("Access denied")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return wrapper


# ---------------------------------------------------
# Home Route
# ---------------------------------------------------

@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------------------------------------------------
# Login
# ---------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form["email"]   # ✅ use email
        password = request.form["password"]

        db = SessionLocal()
        try:
            user = db.query(User).filter_by(email=email).first()

            if not user:
                flash("Email does not exist")
                return redirect(url_for("login"))

            # Check password
            if user.password != password:
                flash("Incorrect password")
                return redirect(url_for("login"))

            # Make sure role exists
            if not user.role:
                flash("User has no role assigned!")
                return redirect(url_for("login"))

            # Store info in session
            session["user_id"] = user.id
            session["email"] = user.email
            session["role"] = user.role

            # Redirect based on role
            if user.role.lower() == "admin":
                return redirect(url_for("admin_dashboard"))
            elif user.role.lower() == "counselor":
                return redirect(url_for("counselor_dashboard"))
            else:
                return redirect(url_for("user_dashboard"))

        finally:
            db.close()

    return render_template("login.html")

# ---------------------------------------------------
# Logout
# ---------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()
    flash("Logged out successfully")

    return redirect(url_for("login"))

#------------------------------------------------------------
#REGISTER
#----------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']

        db = SessionLocal()

        try:
            # Check if email exists
            existing_user = db.query(User).filter_by(email=email).first()
            if existing_user:
                flash("Email already registered")
                return redirect(url_for('register'))

            # Create user
            new_user = User(
                full_name=full_name,
                email=email,
                password=password,
                role="user"
            )

            db.add(new_user)
            db.commit()

            flash("Registration successful. Please login.")
            return redirect(url_for('login'))

        finally:
            db.close()

    return render_template('register.html')

#-----------------------------------------------
#---------------admin dashboard-----------------
@app.route('/admin')
def admin_dashboard():  
    return "Welcome Admin"

#------------------------------------------------
#user dashboard
#------------------------------------------------
@app.route("/user_dashboard")
@user_required
def user_dashboard():
    return render_template("user/user_dashboard.html")

#-----------------------------------------------------------
#------------------user issues------------
#-----------------------------------------------------------

@app.route("/post_issue", methods=["GET", "POST"])
@user_required
def post_issue():
    if request.method == "POST":
        title = request.form["title"]
        category = request.form["category"]
        description = request.form["description"]
        user_id = session["user_id"]

        db = SessionLocal()
        try:
            new_issue = Issue(
                user_id=user_id,
                title=title,
                category=category,
                description=description
            )
            db.add(new_issue)
            db.commit()
            flash("Issue submitted successfully!")
            return redirect(url_for("user_dashboard"))
        finally:
            db.close()

    return render_template("user/post_issue.html")

#-----------------------------------------------------------
#------------------my issue--------------------------------
#---------------------------------------------------------
@app.route("/my_issues")
@user_required
def my_issues():
    db = SessionLocal()
    try:
        user_id = session["user_id"]
        issues = db.query(Issue).filter_by(user_id=user_id).order_by(Issue.date_posted.desc()).all()
        return render_template("user/my_issues.html", issues=issues)
    finally:
        db.close()

#-----------------------------------------------------------------------
#-------------------my appointment-------------------------------------
#----------------------------------------------------------------------
@app.route("/my_appointments")
@user_required
def my_appointments():
    # Replace with your actual logic for fetching appointments
    return render_template("user/appointments.html")

#-------------------------------------------------------------------------
#---------------------------ai chartbot-----------------------------------
#------------------------------------------------------------------------
# AI Chat Logic (Simple)
def ai_response(message):
    message = message.lower()
    if "stress" in message or "anxiety" in message:
        return "Take a deep breath and try to relax. Would you like some coping tips?"
    elif "sleep" in message:
        return "Maintaining a sleep schedule can help. Avoid screens before bed."
    elif "help" in message:
        return "I am here to guide you. Can you tell me more about your concern?"
    else:
        return "I understand. Can you elaborate more so I can help?"

# AI Chat Page
@app.route("/ai_chat", methods=["GET", "POST"])
@user_required
def ai_chat():
    db = SessionLocal()
    user_id = session.get("user_id")

    if request.method == "POST":
        user_message = request.form["message"]

        # Save user message
        new_msg = ChatMessage(user_id=user_id, sender="user", text=user_message)
        db.add(new_msg)
        db.commit()

        # Generate AI response
        response_text = ai_response(user_message)

        # Save AI response
        ai_msg = ChatMessage(user_id=user_id, sender="ai", text=response_text)
        db.add(ai_msg)
        db.commit()

        return redirect(url_for("ai_chat"))

    # GET: fetch chat history
    chat_history = db.query(ChatMessage).filter_by(user_id=user_id).order_by(ChatMessage.timestamp).all()
    db.close()
    return render_template("user/ai_chat.html", chat_history=chat_history)

#------------------------------------------------------------------------------------
#--------------Make appoint----------------------------------------------------------
#------------------------------------------------------------------------------------
@app.route("/make_appointment", methods=["GET", "POST"])
@user_required
def make_appointment():
    db = SessionLocal()
    try:
        if request.method == "POST":
            counselor_name = request.form["counselor_name"]
            date = request.form["date"]
            time = request.form["time"]

            # Create appointment object
            new_appointment = Appointment(
                user_id=session["user_id"],
                counselor_name=counselor_name,
                date=date,
                time=time,
                status="Pending"
            )
            db.add(new_appointment)
            db.commit()
            flash("Appointment request submitted successfully.")
            return redirect(url_for("my_appointments"))

        # For GET request, show the form
        counselors = db.query(User).filter_by(role="counselor").all()
        return render_template("user/make_appointment.html", counselors=counselors)
    finally:
        db.close()
    
if __name__=="__main__":
    app.run(debug=True)