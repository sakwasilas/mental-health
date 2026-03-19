from flask import Flask, render_template, request, redirect, session, url_for, flash
from connections import SessionLocal
from functools import wraps
from models import User

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
    
if __name__=="__main__":
    app.run(debug=True)