from flask import Flask, render_template, request, flash, redirect, url_for
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# You would set this in your environment variables
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

body = open('./templates/december.html','r').read()

@app.route('/', methods=['GET', 'POST'])
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
    app.run(debug=True)