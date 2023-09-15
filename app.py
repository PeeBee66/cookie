from flask import Flask, render_template, request, redirect, url_for, flash, session, Response  # Add Response import
from flask_session import Session
import csv
import hashlib
import os
import random
import string
import requests
import subprocess  # Added for running script.py
import sys
import logging  # Added for logging
import time  # Add time import

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure value
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
submission_results = []

# Define the username and hashed password for login
USERNAME = 'admin'
HASHED_PASSWORD = '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'

# Function to read CSV file and return its data as a list of dictionaries
def read_csv(file_path):
    data = []
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

@app.route('/sse_log')
def sse_log():
    def generate_log_updates():
        while True:
            with open('config/results.log', 'r') as log_file:
                log_content = log_file.read()
            yield f"data: {log_content}\n\n"
            time.sleep(1)  # Adjust the refresh interval as needed

    return Response(generate_log_updates(), content_type='text/event-stream')

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

if not os.path.exists(ADD_USER_CSV_PATH):
    with open(ADD_USER_CSV_PATH, 'w', newline='') as csvfile:
        fieldnames = ['email']  # Specify column headers if needed
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

@app.route('/log_results')
def log_results():
    # You can add any logic here that you want to display in logresults.html
    return render_template('logresults.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'username' not in session:
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

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7007, debug=True)
