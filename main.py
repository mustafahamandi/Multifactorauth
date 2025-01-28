from flask import Flask, jsonify, request, render_template, redirect, session,url_for,flash
from flask_sqlalchemy import SQLAlchemy 
import bcrypt
import re


app = Flask(__name__)
app.secret_key = "3214454587264654"
#config SQL Alchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 
db = SQLAlchemy(app)

#database
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(100), unique = True, nullable = False)
    username = db.Column(db.String(25), unique = True, nullable = False)
    password = db.Column(db.String(150), nullable = False)

    def setpass(self, password):
        # Hash the password with a generated salt
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def checkpass(self, password):
        # Check if the provided password matches the stored hashed password
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

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
    if "username" in session: 
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
        return redirect(url_for('dashboard'))
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
        return redirect(url_for('dashboard'))

#dashboard
@app.route('/dashboard')
def dashboard():
    if "username" in session:
        return render_template('dashboard.html', username = session['username'])
    return redirect(url_for('home'))

#logout
@app.route('/logout')
def logout(): 
    session.pop("username",None)
    return redirect(url_for('home'))

 

if __name__ == '__main__':
    with app.app_context(): 
        db.create_all()
    app.run(debug=True)