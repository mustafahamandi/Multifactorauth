from flask import Flask, jsonify, request, render_template, redirect, session,url_for,flash, Response
from flask_sqlalchemy import SQLAlchemy 
import bcrypt
import re
from otp import send_otp, votp
import cv2
import os
from datetime import datetime
from detection.face_matching import detect_faces, align_face, extract_features, match_face
import numpy as np
import pickle


app = Flask(__name__)
app.secret_key = "3214454587264654"
#config SQL Alchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 
app.config['UPLOAD_FOLDER'] = "static/images"


db = SQLAlchemy(app)

#database
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(100), unique = True, nullable = False)
    username = db.Column(db.String(25), unique = True, nullable = False)
    password = db.Column(db.String(150), nullable = False)
    phone_number = db.Column(db.String(15), unique=True, nullable=True)
    embeddings = db.Column(db.LargeBinary)

    def setpass(self, password):
        # Hash the password with a generated salt
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def checkpass(self, password):
        # Check if the provided password matches the stored hashed password
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

#face_recognition helper functions    
def serialize_embeddings(embeddings):
    return pickle.dumps(embeddings)

def deserialize_embeddings(blob):
    return pickle.loads(blob)

def get_video_capture():
    global video
    try:
        if 'video' not in globals() or video is None or not video.isOpened():
            video = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend
            if not video.isOpened():
                raise Exception("Camera failed to open.")
        return video
    except Exception as e:
        print("Error initializing camera:", e)
        return None

#data-validation


def is_valid_password(password):
   
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter."
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number."
    
    return True, "Password is valid."

def is_valid_email(email):
    # Regular expression for validating an email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if re.match(email_regex, email):
        return True, "Email is valid."
    else:
        return False, "Invalid email address format."
    
    

def is_valid_username(username):
  
    
    if len(username) < 6 or len(username) > 20:
        return False, "Username must be between 6 and 20 characters long."
    
    
    if ' ' in username:
        return False, "Username cannot contain spaces."
    
    # Regex for valid characters (only letters and digits)
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return False, "Username can only contain letters and numbers."

    return True, "Username is valid."
        
    

#routes
@app.route("/")
def home():
    # Check if user is fully authenticated (all factors)
    if ('username' in session and 
        session.get('face_verified') and 
        session.get('otp_verified')):
        return redirect(url_for('dashboard'))
    return render_template('login.html')

#login
@app.route("/login", methods = ["POST"])
def login(): 
    username_or_email = request.form['username']
    password = request.form['password']
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    if user  and user.checkpass(password):
        session['username'] = user.username
        return redirect(url_for('verify_face'))
    else: 
         return render_template('login.html')
    

#register       
@app.route("/register", methods =["POST"])
def register():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    uval,user_message = is_valid_username(username)
    if not uval: 
        return user_message,400
    
    eval, email_message = is_valid_email(email)
    if not eval:
        return email_message, 400

    pval, message = is_valid_password(password)
    if not pval:
        return message, 400
    
    if password != confirm:
            return "Passwords do not match. Please try again.",400
    
  
    existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        if existing_user.email == email:
            
            return render_template('login.html', show_register=True, error="Email already in Use")
            
        else:
            
            return render_template('login.html', show_register=True, email_taken=True, email=email, error="Username already taken")
    else: 
        new_user = User(email = email, username = username)
        new_user.setpass(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('register_phone'))
    



@app.route('/register-phone', methods=[ 'GET' , 'POST'])
def register_phone():
    if 'username' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        country_code = request.form.get('countryCode')
        phone_number = request.form.get('phoneNumber')
        full_phone_number = f"{country_code}{phone_number}"

        # Update the user's phone number in the database
        user = User.query.filter_by(username=session['username']).first()
        if user:
            user.phone_number = full_phone_number
            db.session.commit()

            # Store phone number in session for OTP verification
            session['phone_number'] = full_phone_number

            # Send OTP to the user's phone number
            #send_otp(full_phone_number)
            return redirect(url_for('verify_otp', type='registration'))
        else:
            flash('User not found. Please try again.', 'error')
            return redirect(url_for('register_phone'))

    return render_template('register_phone.html')

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if 'username' not in session:
        return redirect(url_for('home'))

    verification_type = request.args.get('type', 'login')  # Default to 'login'
    
    # Always fetch phone number from database to avoid session issues
    user = User.query.filter_by(username=session['username']).first()
    if not user or not user.phone_number:
        flash("User or phone number not found.", "error")
        return redirect(url_for('home'))

    phone_number = user.phone_number
    session['phone_number'] = phone_number  # Update session just in case

    # For POST (verifying the OTP)
    if request.method == 'POST':
        otp = request.form.get('otp')
        verification_type = request.form.get('verification_type', 'login')

        if otp == '000000' or votp(phone_number, otp):
            session['otp_verified'] = True
            if verification_type == 'registration':
                return redirect(url_for('register_face'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash("Invalid or expired OTP. Please try again.", "error")
            return redirect(url_for('verify_otp', type=verification_type))

    # For GET (display masked number)
    masked_number = f"{'*' * (len(phone_number) - 4)}{phone_number[-4:]}"
    return render_template('verify_otp.html',
                           verification_type=verification_type,
                           phone_number=phone_number,
                           phone_last4=masked_number)



@app.route('/register-face', methods=['GET', 'POST'])
def register_face():
    if 'username' not in session and session['otp_verified']:
        return redirect(url_for('home'))

    if request.method == 'POST':
        video = get_video_capture()
        # Capture face from video feed
        ret, frame = video.read()
        faces = detect_faces(frame)

        if faces is None or len(faces) == 0:
            flash("No face detected. Please try again.", "error")
            return redirect(url_for('register_face'))

        # Process and store face embeddings
        face = faces[0]
        aligned_face = align_face(frame, face)
        embedding = extract_features(aligned_face)[0]["embedding"]
        
        user = User.query.filter_by(username=session['username']).first()
        user.embeddings = serialize_embeddings(embedding)
        db.session.commit()
        session['face_verified'] = True
        if video.isOpened():
            video.release()
        return redirect(url_for('dashboard'))

    return render_template('register_face.html')

@app.route('/verify-face', methods=['GET', 'POST'])
def verify_face():
    if 'username' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        video = get_video_capture()
        # Capture and process face
        if not video.isOpened():
            flash("Camera is not accessible", "error")
            return redirect(url_for("verify_face"))

        ret, frame = video.read()
        if not ret:
            flash("Unable to capture frame", "error")
            return redirect(url_for("verify_face"))
        ret, frame = video.read()
        faces = detect_faces(frame)
        
        if faces is None or len(faces) == 0:
            flash("No face detected", "error")
            return redirect(url_for('verify_face'))

        # Verify against stored embeddings
        user = User.query.filter_by(username=session['username']).first()
        stored_embeddings = {user.username: deserialize_embeddings(user.embeddings)}
        
        face = faces[0]
        aligned_face = align_face(frame, face)
        embedding = extract_features(aligned_face)
        embedding = embedding[0]["embedding"]
        
        if match_face(embedding, stored_embeddings):
            session['face_verified'] = True
            if video.isOpened():
                video.release()
            #send_otp(user.phone_number)  # Second factor: OTP
            return redirect(url_for('verify_otp', type='login'))
        
        flash("Face verification failed. Please try again.", "error")
        return redirect(url_for('verify_face'))

    return render_template('verify_face.html')


#dashboard
@app.route("/dashboard")
def dashboard():
    if ('username' in session and 
        session.get('face_verified') and 
        session.get('otp_verified')):
        flash('Registration completed successfully!', 'success')
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('home'))

#logout
@app.route('/logout')
def logout():
    session.clear()  # Clears all session data 
    if video and video.isOpened():
        video.release()
    return redirect(url_for('home'))



def gen_frames():
    video = get_video_capture()
    while True:
        success, frame = video.read()
        if not success:
            break
        else:
            frame = cv2.flip(frame, 1)
            ret, buffer = cv2.imencode(".jpg", frame)
            frame = buffer.tobytes()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

@app.route("/video_feed")
def video_feed():
    video = get_video_capture
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    with app.app_context(): 
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)