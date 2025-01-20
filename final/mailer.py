import smtplib
from email.message import EmailMessage
import os

def send_email_with_attachment(smtp_server, port, sender_email, sender_password, recipient_email, subject, body, file_path):
    try:
        # Create the email message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg.set_content(body)

        # Add the Excel attachment
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(file_path)

            # Add attachment to the email
            msg.add_attachment(file_data, maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=file_name)

        # Connect to the SMTP server and send the email
       # Connect to the SMTP server and send the email
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            print("Connecting to the server...")
            server.login(sender_email, sender_password)
            print("Logged in successfully!")
            server.send_message(msg)
            print("Email sent!")

        print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {e}")

# Configuration
smtp_server = 'smtp.gmail.com'  # For Gmail SMTP server
port = 465  # SSL port
sender_email = 'tejasdesh01@gmail.com'
sender_password = "" 
recipient_email = 'tejassdesh07@gmail.com'
subject = 'Excel File Attachment'
body = 'Please find the attached Excel file.'
file_path = 'filtered_fire_incidents2.xlsx'

# Send the email
send_email_with_attachment(smtp_server, port, sender_email, sender_password, recipient_email, subject, body, file_path)
