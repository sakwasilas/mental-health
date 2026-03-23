from flask import Flask, render_template, request, redirect, session, url_for, flash
from connections import SessionLocal
from functools import wraps
from models import User,Issue,ChatMessage,Appointment
from datetime import datetime


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
@admin_required
def admin_dashboard():  
    return render_template("admin/admin_dashboard.html")

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

        db = SessionLocal()
        try:
            new_issue = Issue(
                user_id=session["user_id"],
                title=title,
                category=category,
                description=description,
                status="pending",
                date_posted=datetime.utcnow()
            )
            db.add(new_issue)
            db.commit()

            flash("Issue submitted successfully!")
            return redirect(url_for("my_issues"))
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
    db = SessionLocal()
    try:
        appointments = db.query(Appointment).filter_by(
            user_id=session["user_id"]
        ).all()
        return render_template("user/appointments.html", appointments=appointments)
    finally:
        db.close()

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

    try:
        if request.method == "POST":
            user_message = request.form["message"]

            db.add(ChatMessage(user_id=user_id, sender="user", text=user_message))

            response_text = ai_response(user_message)

            db.add(ChatMessage(user_id=user_id, sender="ai", text=response_text))

            db.commit()
            return redirect(url_for("ai_chat"))

        chat_history = db.query(ChatMessage)\
            .filter_by(user_id=user_id)\
            .order_by(ChatMessage.timestamp).all()

        return render_template("user/ai_chat.html", chat_history=chat_history)

    finally:
        db.close()

#------------------------------------------------------------------------------------
#--------------Make appoint----------------------------------------------------------
#------------------------------------------------------------------------------------
@app.route("/make_appointment", methods=["GET", "POST"])
@user_required
def make_appointment():
    db = SessionLocal()
    try:
        if request.method == "POST":
            counselor_id = request.form["counselor_id"]
            date = request.form["date"]
            time = request.form["time"]
            payment_method = request.form["payment_method"]

            new_appointment = Appointment(
                user_id=session["user_id"],
                counselor_id=counselor_id,
                date=date,
                time=time,
                payment_method=payment_method,
                status="Pending",
                meet_link=None
            )

            db.add(new_appointment)
            db.commit()

            flash("Appointment request sent. Wait for counselor approval.")
            return redirect(url_for("my_appointments"))

        counselors = db.query(User).filter_by(role="counselor").all()
        return render_template("user/make_appointment.html", counselors=counselors)

    finally:
        db.close()
#-----------------councelor--------------------------
@app.route("/counselor_dashboard")
@counselor_required
def counselor_dashboard():
    return render_template("counselor/dashboard.html")

#-------------------------------------------------------
# view appointment------------------------------------
#----------------------------------------------------

@app.route("/counselor_appointments")
@counselor_required
def counselor_appointments():
    db = SessionLocal()
    try:
        appointments = db.query(Appointment).filter_by(
            counselor_id=session["user_id"]
        ).all()

        users = db.query(User).all()
        user_map = {u.id: u.full_name for u in users}

        return render_template(
            "counselor/appointments.html",
            appointments=appointments,
            user_map=user_map
        )
    finally:
        db.close()

#----------------------accept appointments----------------
#------------------                    ---------------------
@app.route("/accept_appointment/<int:id>")
@counselor_required
def accept_appointment(id):
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter_by(
            id=id,
            counselor_id=session["user_id"]
        ).first()

        if not appointment:
            flash("Appointment not found")
            return redirect(url_for("counselor_appointments"))

        appointment.status = "Confirmed"
        appointment.meet_link = f"https://meet.google.com/session-{appointment.id}"

        db.commit()

        flash("Appointment accepted and meet link sent to user")
        return redirect(url_for("counselor_appointments"))

    finally:
        db.close()

#----------------------------------------------------------
#------------------------see response---------------------
#----------------------------------------------------------
@app.route("/responded_issues")
@counselor_required
def responded_issues():
    db = SessionLocal()
    try:
        issues = db.query(Issue).filter_by(status="responded").order_by(Issue.date_posted.desc()).all()
        return render_template("counselor/responded_issues.html", issues=issues)
    finally:
        db.close()

#------------------------------------------------------------
# response to issues
#------------------------------------------------------------
@app.route("/respond_issue/<int:id>", methods=["GET", "POST"])
@counselor_required
def respond_issue(id):
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter_by(id=id).first()

        if not issue:
            flash("Issue not found")
            return redirect(url_for("view_issues"))

        if request.method == "POST":
            issue.response = request.form["response"]
            issue.status = "responded"
            db.commit()

            flash("Response sent successfully")
            return redirect(url_for("view_issues"))

        return render_template("counselor/respond_issue.html", issue=issue)
    finally:
        db.close()

#---------------------------------------------------------------
#------------------------view issues-----------------------------
#----------------------------------------------------------------
@app.route("/view_issues")
@counselor_required
def view_issues():
    db = SessionLocal()
    try:
        issues = db.query(Issue).filter_by(status="pending").order_by(Issue.date_posted.desc()).all()
        return render_template("counselor/view_issues.html", issues=issues)
    finally:
        db.close()

#---------------------rehject appointment-----------------
@app.route("/reject_appointment/<int:id>")
@counselor_required
def reject_appointment(id):
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter_by(
            id=id,
            counselor_id=session["user_id"]
        ).first()

        if not appointment:
            flash("Appointment not found")
            return redirect(url_for("counselor_appointments"))

        appointment.status = "Rejected"
        appointment.meet_link = None
        db.commit()

        flash("Appointment rejected successfully")
        return redirect(url_for("counselor_appointments"))

    finally:
        db.close()

    
if __name__=="__main__":
    app.run(debug=True)