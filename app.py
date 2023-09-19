from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_session import Session
import csv
import hashlib
import os
import random
import string
import requests
import subprocess
import sys
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
submission_results = []

# Define the username and hashed password for login
USERNAME = 'admin'
HASHED_PASSWORD = 'ff4f0fce1161d864dc2602e532a51961c70524419da7fde6ff198259a689fc1b'

# Function to read CSV file and return its data as a list of dictionaries
def read_csv(file_path):
    data = []
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

# Function to write data to a CSV file
def write_csv(file_path, fieldnames, data):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

# Ensure CSV files exist at startup
COOKIE_CODES_CSV_PATH = 'config/CookieCodes.csv'
ADD_USER_CSV_PATH = 'config/addUser.csv'

if not os.path.exists(COOKIE_CODES_CSV_PATH):
    with open(COOKIE_CODES_CSV_PATH, 'w', newline='') as csvfile:
        fieldnames = []  # Add column headers if needed
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

# Configure logging to write to config/results.log
log_file = 'config/results.log'
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create results.log file if it does not exist
if not os.path.exists(log_file):
    open(log_file, 'w').close()

# Function to send a POST request to the webpage
def send_post_request(submitted_code, email=None):
    url = 'https://coupon.devplay.com/coupon/ck/en'
    data = {'code': submitted_code}

    # Include email in the POST data if provided
    if email:
        data['email'] = email

    response = requests.post(url, data=data)

    # Determine if the submission was successful or not
    if "successful" in response.text:
        return "Successful"
    else:
        return "Unsuccessful"

# Function to validate the code
def is_valid_code(code):
    return 13 <= len(code) <= 17 and code.isalnum() and code.isupper()

# Function to run script.py with email and code
def run_script(email, code):
    try:
        # Use 'python3' as the Python interpreter
        result = subprocess.run(["python3", "script.py", email, code], stdout=subprocess.PIPE, check=True, text=True)

        # Get the alert text from the script's output
        alert_text = result.stdout.strip()

        print("Alert Text:", alert_text)

        # Check if the alert message matches any of the specified messages
        if alert_text in [
            "Done! Log in to the game to claim your reward!",
            "Please check your DevPlay account!",
            "Please check the coupon code!",
            "This coupon code is invalid.",
            "This coupon code is currently not available. Please check the coupon code usage dates.",
            "This coupon code has already been used!",
            "You have exceeded the number of available coupons."
        ]:
            print("Closing the application...")
        else:
            print("Alert message does not match the specified messages.")

        # Log the result to the results.log file
        logging.info(f"Email: {email}, Code: {code}, Alert Text: {alert_text}, Result: {result.stdout.strip()}")

        return alert_text
    except subprocess.CalledProcessError as e:
        print("Error running script.py:", e)
        return "Error: " + str(e)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Read CookieCodes.csv
    cookie_data = read_csv(COOKIE_CODES_CSV_PATH)

    error_message = None  # Initialize the error message
    submission_results = []  # Initialize the submission_results list

    if request.method == 'POST':
        submitted_code = request.form.get('email')

        if is_valid_code(submitted_code):
            # Check if the code already exists in CookieCodes.csv
            if not any(item['code'] == submitted_code for item in cookie_data):
                # Save the code to CookieCodes.csv
                cookie_data.append({'code': submitted_code})
                write_csv(COOKIE_CODES_CSV_PATH, fieldnames=['code'], data=cookie_data)

                # Get the list of email addresses from addUser.csv
                user_data = read_csv(ADD_USER_CSV_PATH)
                email_addresses = [user['email'] for user in user_data]

                # Iterate through the email addresses and submit the code for each
                for email in email_addresses:
                    submission_result = send_post_request(submitted_code, email)
                    # Get the alert text from the script
                    alert_text = run_script(email, submitted_code)
                    submission_results.append({'email': email, 'code': submitted_code, 'alert_text': alert_text, 'result': submission_result})

                flash(f'Code {submitted_code} submitted successfully', 'success')
            else:
                error_message = 'This coupon code already exists.'
        else:
            error_message = 'This coupon code is invalid.'

    return render_template('index.html', cookie_data=cookie_data, error_message=error_message, submission_results=submission_results)

# Route for the "Add User" page
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    # Check if the user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        email = request.form.get('email')
        if email:
            # Read addUser.csv
            user_data = read_csv(ADD_USER_CSV_PATH)

            # Add the new email to the list
            user_data.append({'email': email})

            # Write back to addUser.csv
            write_csv(ADD_USER_CSV_PATH, fieldnames=['email'], data=user_data)

            flash('User added successfully', 'success')

    # Read addUser.csv
    user_data = read_csv(ADD_USER_CSV_PATH)

    return render_template('add_user.html', user_data=user_data)

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the provided username and password are correct
        if username == USERNAME and hashlib.sha256(password.encode()).hexdigest() == HASHED_PASSWORD:
            # Set a session variable to indicate that the user is logged in
            session['logged_in'] = True
            return redirect(url_for('add_user'))
        else:
            flash('Login failed. Please try again.', 'error')

    return render_template('login.html')

# Route for logout
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the user's session
    session.pop('logged_in', None)

    if not os.path.exists(ADD_USER_CSV_PATH):
        with open(ADD_USER_CSV_PATH, 'w', newline='') as csvfile:
            fieldnames = ['email']  # Specify column headers if needed
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7007)
