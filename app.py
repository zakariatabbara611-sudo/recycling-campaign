import os
import sqlite3
import smtplib
import random
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "super_secret_gpa_key"

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "checker.db")

def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Helper function to calculate GPA
def calculate_gpa(courses):
    total_credits = sum(c['credits'] for c in courses)
    if total_credits == 0:
        return 0.0
    total_points = sum(c['credits'] * c['grade_points'] for c in courses)
    return total_points / total_credits

# --- AUTH ROUTES ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM logen WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result and result['password'] == password:
        session['user'] = username  # Save user login session
        flash(f"Welcome back, {username}!", "success")
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password.", "error")
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

# --- SIGN UP ROUTE ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for('signup'))

        conn = get_db()
        cursor = conn.cursor()

        # Check if username or email already exists
        cursor.execute("SELECT * FROM logen WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            flash("Username or email already taken.", "error")
            return redirect(url_for('signup'))

        # Insert new user
        cursor.execute("INSERT INTO logen (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        conn.close()

        flash("Account created! Please log in.", "success")
        return redirect(url_for('index'))

    return render_template('signup.html')

# --- FORGOT & RESET PASSWORD ROUTES ---

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM logen WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            # Store email in session to verify during reset
            session['reset_email'] = email
            flash("Email verified! Please enter your new password.", "success")
            return redirect(url_for('reset'))
        else:
            flash("No account found with that email address.", "error")
            return redirect(url_for('forgot'))

    return render_template('forgot.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if 'reset_email' not in session:
        flash("Please initiate password reset first.", "error")
        return redirect(url_for('forgot'))

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        email = session.pop('reset_email', None)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE logen SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()
        conn.close()

        flash("Password updated successfully! You can now log in.", "success")
        return redirect(url_for('index'))

    return render_template('reset.html')

# --- DASHBOARD & GRADES ROUTES ---

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("Please log in first.", "error")
        return redirect(url_for('index'))

    username = session['user']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_grades WHERE username = ?", (username,))
    courses = cursor.fetchall()
    conn.close()

    gpa = calculate_gpa(courses)
    return render_template('dashboard.html', username=username, courses=courses, gpa=gpa)

@app.route('/add_course', methods=['POST'])
def add_course():
    if 'user' not in session:
        return redirect(url_for('index'))

    course_name = request.form.get('course_name').strip()
    credits = int(request.form.get('credits'))
    grade_points = float(request.form.get('grade'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_grades (username, course_name, credits, grade_points) VALUES (?, ?, ?, ?)",
        (session['user'], course_name, credits, grade_points)
    )
    conn.commit()
    conn.close()

    flash("Course added!", "success")
    return redirect(url_for('dashboard'))

@app.route('/delete_course/<int:course_id>')
def delete_course(course_id):
    if 'user' not in session:
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_grades WHERE id = ? AND username = ?", (course_id, session['user']))
    conn.commit()
    conn.close()

    flash("Course removed.", "success")
    return redirect(url_for('dashboard'))

# Initialize scheduling models and register schedule blueprint (if available)
try:
    import models
    models.create_tables()
    models.init_sample_data()
except Exception as _e:
    print('Models init skipped or failed:', _e)

try:
    from schedule_routes import schedule_bp
    app.register_blueprint(schedule_bp)
except Exception as _e:
    print('Schedule blueprint not registered:', _e)

# Start background scheduler for daily reminders (requires APScheduler)
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from email_utils import send_shift_reminders_job

    scheduler = BackgroundScheduler()
    # Run reminder job every day at 08:00
    scheduler.add_job(send_shift_reminders_job, 'cron', hour=8, minute=0)
    scheduler.start()
except Exception as _e:
    print('Scheduler not started:', _e)

if __name__ == '__main__':
    app.run(debug=True)


SENDER_EMAIL = "zakariatabbara611@gmail.com"
SENDER_PASSWORD = "phen thfj ibga uhns"  # App Password, not regular password!

def send_verification_email(receiver_email, code):
    msg = EmailMessage()
    msg['Subject'] = 'Your Password Reset Verification Code'
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg.set_content(f'Your 6-digit verification code for GPA Calculator is: {code}')

    # Connect to Gmail SMTP server
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM logen WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            # 1. Generate a random 6-digit verification code
            verification_code = str(random.randint(100000, 999999))
            
            # 2. Store the code and email in session temporarily
            session['reset_email'] = email
            session['reset_code'] = verification_code

            # 3. Send email with the code
            try:
                send_verification_email(email, verification_code)
                flash("A 6-digit verification code has been sent to your email!", "success")
                return redirect(url_for('reset'))
            except Exception as e:
                print("Email Error:", e)
                flash("Failed to send verification email. Check server configuration.", "error")
                return redirect(url_for('forgot'))
        else:
            flash("No account found with that email address.", "error")
            return redirect(url_for('forgot'))

    return render_template('forgot.html')

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if 'reset_email' not in session or 'reset_code' not in session:
        flash("Please request a password reset code first.", "error")
        return redirect(url_for('forgot'))

    if request.method == 'POST':
        user_code = request.form.get('code', '').strip()
        new_password = request.form.get('password', '').strip()

        # Check if entered code matches generated code
        if user_code != session.get('reset_code'):
            flash("Invalid verification code. Please try again.", "error")
            return redirect(url_for('reset'))

        email = session.pop('reset_email', None)
        session.pop('reset_code', None)  # Clear the code after successful use

        # Update database with new password
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE logen SET password = ? WHERE email = ?", (new_password, email))
        conn.commit()
        conn.close()

        flash("Password updated successfully! You can now log in.", "success")
        return redirect(url_for('index'))

    return render_template('reset.html')