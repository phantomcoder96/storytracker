import os
import sys
from dotenv import load_dotenv
import brevo_python
from datetime import datetime

load_dotenv()
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
# Only send error alerts to the first email in the list (the admin)
TO_EMAIL = os.getenv("TO_EMAIL").split(',')[0].strip()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

if len(sys.argv) < 3:
    print("Usage: python send_error.py <Source> <Error Message>")
    sys.exit(1)

source = sys.argv[1]
error_message = sys.argv[2]

configuration = brevo_python.Configuration()
configuration.api_key['api-key'] = BREVO_API_KEY
api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))

html_content = f"""
<html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #f44336; border-radius: 8px;">
            <h2 style="color: #f44336;">⚠️ Story Tracker Error Alert</h2>
            <p><strong>Source:</strong> {source}</p>
            <p><strong>Error Details:</strong></p>
            <pre style="background: #f8f8f8; padding: 10px; border-left: 4px solid #f44336; white-space: pre-wrap;">{error_message}</pre>
        </div>
    </body>
</html>
"""

send_smtp_email = brevo_python.SendSmtpEmail(
    to=[{"email": TO_EMAIL}],
    sender={"email": SENDER_EMAIL, "name": "StoryTracker Alerts"},
    subject=f"⚠️ Alert: StoryTracker Error from {source}",
    html_content=html_content
)

try:
    api_instance.send_transac_email(send_smtp_email)
    print(f"[{datetime.now()}] Sent error alert email.")
except Exception as e:
    print(f"Failed to send error email: {e}")
