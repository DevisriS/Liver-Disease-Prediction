from flask import Flask, render_template, request, redirect, url_for, session, flash
import numpy as np
import pickle
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Load your machine learning model
model = pickle.load(open('Liver2.pkl', 'rb'))

# File to store user credentials
USER_FILE = 'users.json'

# Helper function to load user data from JSON file
def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r') as file:
            return json.load(file)
    return {}

# Helper function to save user data to JSON file
def save_users(users):
    with open(USER_FILE, 'w') as file:
        json.dump(users, file)

@app.route('/', methods=['GET'])
def Home():
    if 'username' not in session:  
        return redirect(url_for('login')) 
    return render_template('index.html')  

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Load existing users
        users = load_users()

        if username in users:
            flash('Username already exists! Please choose a different one.', 'danger')
        else:
            # Save new user to users.json
            users[username] = password
            save_users(users)
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Load existing users
        users = load_users()

        if username in users and users[username] == password:
            session['username'] = username  # Log the user in
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('Home'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route("/predict", methods=['POST'])
def predict():
    if 'username' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        Age = int(request.form['Age'])
        Gender = int(request.form['Gender'])
        Total_Bilirubin = float(request.form['Total_Bilirubin'])
        Alkaline_Phosphotase = int(request.form['Alkaline_Phosphotase'])
        Alamine_Aminotransferase = int(request.form['Alamine_Aminotransferase'])
        Aspartate_Aminotransferase = int(request.form['Aspartate_Aminotransferase'])
        Total_Protiens = float(request.form['Total_Protiens'])
        Albumin = float(request.form['Albumin'])
        Albumin_and_Globulin_Ratio = float(request.form['Albumin_and_Globulin_Ratio'])

        values = np.array([[Age, Gender, Total_Bilirubin, Alkaline_Phosphotase, 
                            Alamine_Aminotransferase, Aspartate_Aminotransferase, 
                            Total_Protiens, Albumin, Albumin_and_Globulin_Ratio]])
        prediction = model.predict(values)

        return render_template('result.html', prediction=prediction)

if __name__ == "__main__":
    app.run(debug=True)
