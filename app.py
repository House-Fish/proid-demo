from flask import Flask, render_template, render_template_string, request, flash, redirect, url_for, session, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from functools import wraps
from dotenv import load_dotenv
from flask_socketio import SocketIO
import os
import random

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Required for flash messages

socketio = SocketIO(app, cors_allowed_origins=["https://proid.housefish.dev"])

# You would set this in your environment variables
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
AUTH_PASSCODE = os.getenv('AUTH_PASSCODE')
AUTH_TOKEN = os.getenv("AUTH_TOKEN")


# State storage for Transportation and Air-Conditioner
current_state = {
    "Transportation": "Unknown",
    "Air-Conditioner": "Unknown"
}

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        passcode = request.form.get('passcode')
        if passcode == AUTH_PASSCODE:
            session['authenticated'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('send_email'))
        else:
            flash('Invalid passcode!', 'error')
    return render_template('login.html')

@app.route('/api/bocah', methods=['POST'])
def handle_post_request():

    # Check for the correct authentication header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Authorization header is missing"}), 401

    if auth_header != f"Bearer {AUTH_TOKEN}":
        return jsonify({"error": "Invalid authorization token"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    # Update state based on key-value pairs
    if data["key"] == "Environment":
        current_state["Air-Conditioner"] = data["value"]
    elif data["key"] == "Motion State":
        current_state["Transportation"] = data["value"]

    socketio.emit('state_update', current_state)

    return jsonify({"message": "State updated successfully", "current_state": current_state}), 200


@app.route('/state', methods=['GET'])
@require_auth
def show_logs():
    # Render the log dashboard
    return render_template('state.html', 
                           transportation=current_state['Transportation'], 
                           air_conditioner=current_state['Air-Conditioner'])

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@require_auth
def send_email():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')

        # List of available report files
        reports = ['./templates/january.html', './templates/january1.html', './templates/january2.html', 
                   './templates/january3.html', './templates/january4.html']
        
        # Randomly select a report
        selected_report = random.choice(reports)

        # Read the selected report
        body = open(selected_report, 'r').read()

        # Use Jinja to update the name in the report
        body = render_template_string(body, name=name)
        
        try:
            # Create the email message
            message = Mail(
                from_email='me@housefish.dev',  # Must be verified with SendGrid
                to_emails=email,
                subject=f'Hello {name}, your monthly carbon report is in 🌱',
                html_content=body
            )

            # Send the email
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            
            # Check if the email was sent successfully
            if response.status_code == 202:
                flash('Email sent successfully!', 'success')
            else:
                flash('Failed to send email.', 'error')
                
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            
        return redirect(url_for('send_email'))
        
    return render_template('email_form.html')

if __name__ == '__main__':
    app.run(threaded=True)