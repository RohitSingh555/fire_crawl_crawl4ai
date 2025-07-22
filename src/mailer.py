import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import json
from pathlib import Path
from datetime import datetime

def find_latest_verification_files():
    """Find the most recent verification results files"""
    verified_dir = Path('verified_results')
    if not verified_dir.exists():
        print("❌ No verified_results directory found")
        return None, None
    
    # Find all verified_fire_incidents_*.csv files
    csv_files = list(verified_dir.glob('verified_fire_incidents_*.csv'))
    json_files = list(verified_dir.glob('verified_fire_incidents_*.json'))
    
    if not csv_files or not json_files:
        print("❌ No verification results files found")
        return None, None
    
    # Return the most recent files
    latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
    latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
    
    print(f"📁 Found latest verification files:")
    print(f"   CSV: {latest_csv}")
    print(f"   JSON: {latest_json}")
    
    return str(latest_csv), str(latest_json)

def generate_html_email_body(csv_file, json_file):
    """Generate a beautiful HTML email body with verification results"""
    try:
        # Read JSON file for detailed summary
        with open(json_file, 'r', encoding='utf-8') as f:
            verified_articles = json.load(f)
        
        # Get file stats
        csv_size = os.path.getsize(csv_file) / 1024  # KB
        
        # Generate HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .company-header {{
            background: linear-gradient(135deg, #4CAF50, #2E7D32);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            text-align: center;
            margin-bottom: 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .company-logo {{
            font-size: 2.2em;
            font-weight: bold;
            margin-bottom: 5px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .company-tagline {{
            font-size: 1em;
            opacity: 0.9;
            font-style: italic;
        }}
        .header {{
            background: linear-gradient(135deg, #66BB6A, #4CAF50);
            color: white;
            padding: 30px;
            border-radius: 0 0 10px 10px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .stats-container {{
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 10px;
            min-width: 150px;
            flex: 1;
            border-top: 4px solid #4CAF50;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #4CAF50;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .incidents-section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin: 30px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .incidents-section h2 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
            margin-bottom: 25px;
        }}
        .incident-item {{
            border-left: 4px solid #4CAF50;
            padding: 20px;
            margin: 15px 0;
            background: #f8f9fa;
            border-radius: 0 5px 5px 0;
        }}
        .incident-title {{
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .incident-details {{
            color: #666;
            font-size: 0.9em;
        }}
        .incident-details span {{
            margin-right: 20px;
        }}
        .fire-score {{
            background: #4CAF50;
            color: white;
            padding: 3px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .footer {{
            background: #2E7D32;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-top: 30px;
        }}
        .footer a {{
            color: #A5D6A7;
            text-decoration: none;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        .attachment-info {{
            background: #E8F5E8;
            border: 1px solid #4CAF50;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .attachment-info strong {{
            color: #2E7D32;
        }}
        .agilemorph-branding {{
            background: #f1f8e9;
            border: 1px solid #C8E6C9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
        }}
        .agilemorph-branding strong {{
            color: #2E7D32;
        }}
    </style>
</head>
<body>
    <div class="company-header">
        <div class="company-logo">AgileMorph</div>
        <div class="company-tagline">Empowering Your Digital Transformation</div>
    </div>

    <div class="header">
        <h1>🔥 Fire Incident Report</h1>
        <p>Daily Verification Summary • {datetime.now().strftime('%B %d, %Y')}</p>
    </div>

    <div class="agilemorph-branding">
        <strong>🚀 Powered by AgileMorph Solutions</strong><br>
        Innovative Software Solutions for Data Analytics & AI-Powered Insights
    </div>

    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-number">{len(verified_articles)}</div>
            <div class="stat-label">Verified Incidents</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{csv_size:.1f} KB</div>
            <div class="stat-label">File Size</div>
        </div>
        <div class="stat-box">
            <div class="stat-number">{datetime.now().strftime('%H:%M')}</div>
            <div class="stat-label">Generated At</div>
        </div>
    </div>

    <div class="attachment-info">
        <strong>📎 Attachment:</strong> {os.path.basename(csv_file)} - Complete fire incident data in CSV format for analysis
    </div>

    <div class="incidents-section">
        <h2>🔥 Top Fire Incidents Today</h2>
"""

        # Add top incidents
        for i, article in enumerate(verified_articles[:5], 1):
            title = article.get('title', 'No title')[:100]
            source = article.get('source', 'Unknown source')
            date = article.get('published_date', 'No date')
            fire_score = article.get('fire_related_score', 0.0)
            
            html_content += f"""
        <div class="incident-item">
            <div class="incident-title">{i}. {title}...</div>
            <div class="incident-details">
                <span><strong>Source:</strong> {source}</span>
                <span><strong>Date:</strong> {date}</span>
                <span class="fire-score">Fire Score: {fire_score:.2f}</span>
            </div>
        </div>
"""
        
        if len(verified_articles) > 5:
            html_content += f"""
        <div class="incident-item" style="text-align: center; color: #666; font-style: italic;">
            ... and {len(verified_articles) - 5} more verified fire incidents
        </div>
"""
        
        html_content += """
    </div>

    <div class="footer">
        <p>This report contains AI-verified fire incidents that have been processed and confirmed for accuracy.</p>
        <p>Generated automatically by AgileMorph's Fire Incident Verification System</p>
        <p><a href="https://theagilemorph.com/">Visit AgileMorph Solutions</a> | <a href="https://theagilemorph.com/contact">Contact Us</a></p>
    </div>
</body>
</html>
"""
        
        return html_content
        
    except Exception as e:
        print(f"❌ Error generating HTML summary: {e}")
        return f"""
        <html>
        <body>
            <h2>Fire Incident Verification Report</h2>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>CSV file attached with verification results.</p>
            <p>Powered by AgileMorph Solutions</p>
        </body>
        </html>
        """

def send_email_with_csv_attachment(smtp_server, port, sender_email, sender_password, recipient_email, subject, html_body, csv_file):
    try:
        # Create the email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Add HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)

        # Add CSV attachment
        if csv_file and os.path.exists(csv_file):
            with open(csv_file, 'rb') as f:
                attachment = MIMEBase('text', 'csv')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                
                file_name = os.path.basename(csv_file)
                attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
                msg.attach(attachment)
                print(f"✅ Added CSV attachment: {file_name}")

        # Connect to the SMTP server and send the email
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            print("🔗 Connecting to the server...")
            server.login(sender_email, sender_password)
            print("✅ Logged in successfully!")
            server.send_message(msg)
            print("📧 Email sent successfully!")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def main():
    """Main function to send verification results"""
    print("📧 AgileMorph Fire Incident Verification Email Sender")
    print("=" * 50)
    
    # Find latest verification files
    csv_file, json_file = find_latest_verification_files()
    
    if not csv_file or not json_file:
        print("❌ No verification results found. Please run verification.py first:")
        print("python src/verification.py")
        return
    
    # Configuration
    smtp_server = 'smtp.gmail.com'  # For Gmail SMTP server
    port = 465  # SSL port
    sender_email = "agilemorphsolutions@gmail.com"  # Replace with your email
    sender_password = "vktnzpaaurneigpg"  
    recipient_email = 'tejassdesh07@gmail.com, unipaney@dhaninfo.biz, u@agilemorph.biz, rchakraborty@dhaninfo.biz, npalliwal@dhaninfo.biz, lalit.shukla@dhaninfo.biz, rnagmote@dhaninfo.biz, apandey@dhaninfo.biz'
    
    # Generate email content
    subject = f'🔥 AgileMorph Daily Fire Incident Report - {datetime.now().strftime("%B %d, %Y")}'
    html_body = generate_html_email_body(csv_file, json_file)
    
    print(f"📊 Sending AgileMorph daily fire incident report...")
    print(f"   CSV file: {csv_file}")
    
    # Send the email
    send_email_with_csv_attachment(smtp_server, port, sender_email, sender_password, recipient_email, subject, html_body, csv_file)

if __name__ == "__main__":
    main()
