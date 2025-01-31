from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify, render_template_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# You would set this in your environment variables
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
AUTH_PASSCODE = os.getenv('AUTH_PASSCODE', 'your-secure-passcode')
AUTH_TOKEN = "your_secure_auth_token"

body = open('./templates/december.html','r').read()

# Store request data in memory (simple for demonstration purposes)
data_store = []

# HTML template to display the logged data
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Request Data Log</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 10px; border: 1px solid #ddd; }
    th { background-color: #f4f4f4; }
  </style>
</head>
<body>
  <h1>Logged Request Data</h1>
  {% if data %}
    <table>
      <tr>
        <th>#</th>
        <th>Data</th>
      </tr>
      {% for idx, item in enumerate(data) %}
      <tr>
        <td>{{ idx + 1 }}</td>
        <td>{{ item }}</td>
      </tr>
      {% endfor %}
    </table>
  {% else %}
    <p>No data received yet.</p>
  {% endif %}
</body>
</html>
"""

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
def bocah():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Authorization header is missing"}), 401

    if auth_header != f"Bearer {AUTH_TOKEN}":
        return jsonify({"error": "Invalid authorization token"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    data_store.append(data)

    result = {"message": "Request successful", "data_received": data}

    return jsonify(result), 200

@app.route('/logs', methods=['GET'])
def show_logs():
    # Render the data log page
    return render_template_string(html_template, data=data_store)

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

        
        try:
            # Create the email message
            message = Mail(
                from_email='me@housefish.dev',  # Must be verified with SendGrid
                to_emails=email,
                subject=f'Hello {name}',
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
    app.run()