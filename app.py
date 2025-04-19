from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hazard
from hazard import predict_hazard_score 

def send_approval_email(admin_email, username):
    sender_email = "parcivalpar@gmail.com"
    sender_password = "Parcival27P"

    subject = "New Authority Account Approval Needed"
    body = f"An authority account with username '{username}' requires approval. Please verify it."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = admin_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, admin_email, msg.as_string())
        server.quit()
        print("✅ Approval email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, 
                    user_type TEXT, 
                    username TEXT, 
                    password TEXT,
                    approved INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "password":
            return redirect(url_for("index"))  

    return render_template("login.html")

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        username = request.form.get('username')
        password = request.form.get('password')

        if not user_type or not username or not password:
            return "⚠️ Please fill in all fields!", 400

        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            if user_type == "authority":
                c.execute("INSERT INTO users (user_type, username, password, approved) VALUES (?, ?, ?, 0)", 
                          (user_type, username, password))
                message = "✅ Request sent for approval! Admin will review it."
            else:
                c.execute("INSERT INTO users (user_type, username, password, approved) VALUES (?, ?, ?, 1)", 
                          (user_type, username, password))
                message = "✅ Account created successfully! You can log in now."
            conn.commit()
        except Exception as e:
            return f"Database error: {e}", 500
        finally:
            conn.close()

        return render_template("create_account.html", message=message)
    
    return render_template("create_account.html")


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            if user[4] == 1:
                user_type = user[1]
                if user_type == "authority":
                    return redirect(url_for('otp_verification', user_type=user_type))
                return render_template('index.html', user_type=user_type)
            else:
                return "⚠️ Your account is awaiting approval!", 403
        else:
            return "⚠️ Invalid credentials!", 401

    return render_template("index.html")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    if request.method == 'POST':
        username = request.form.get('username')
        c.execute("UPDATE users SET approved = 1 WHERE username = ?", (username,))
        conn.commit()

    c.execute("SELECT * FROM users WHERE user_type = 'authority' AND approved = 0")
    pending_users = c.fetchall()
    conn.close()

    return render_template('admin.html', pending_users=pending_users)

@app.route('/approve_accounts')
def approve_accounts():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_type = 'authority' AND approved = 0")
    pending_users = c.fetchall()
    conn.close()
    return render_template("approve_accounts.html", pending_users=pending_users)

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET approved = 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return "✅ User Approved!"

@app.route('/otp_verification/<user_type>', methods=['GET', 'POST'])
def otp_verification(user_type):
    if request.method == 'POST':
        otp = request.form.get('otp')
        if otp == "123456":
            return "✅ OTP Verified! You can now access the system."
        else:
            return "⚠️ Invalid OTP!", 400

    return render_template('otp_verification.html', user_type=user_type)

@app.route('/predict_hazard', methods=['POST'])
def predict_hazard():
    """
    API endpoint to predict hazard score based on latitude & longitude.
    """
    data = request.get_json()
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    score = predict_hazard_score(latitude, longitude)
    return jsonify({"hazard_score": score})

@app.route('/get_hazard_data', methods=['GET', 'POST'])
def get_hazard_data():
    if request.method == 'POST':
        return jsonify({"message": "Received POST request"})
    else:
        return jsonify({"message": "Received GET request"})

@app.route('/hazard-data')
def hazard_data():
    hazard_points = hazard.generate_hazard_map()  
    return jsonify(hazard_points)

if __name__ == '__main__':
    app.run(debug=True)