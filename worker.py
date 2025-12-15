import os
import json
import logging
from redis import Redis
from rq import Worker, Connection
from flask import render_template
from weasyprint import HTML
from flask_mail import Message

# Import the application components from the app package
# Ensure these imports align with your app/app.py structure
try:
    from app.app import create_app, db, mail 
    from app.config import Config
    # Assuming AuditReport is the correct name for your SQLAlchemy model
    from app.models import AuditReport 
except ImportError as e:
    # This is critical for worker to function
    print(f"FATAL: Could not import application components: {e}")
    # Raise the error immediately if essential parts are missing
    raise

# --- Worker Setup and Configuration ---

# 1. Create the application instance (FACTORY PATTERN)
# The worker needs a full app context to access mail, db, and templates
app = create_app(os.getenv('FLASK_ENV', 'default')) 

# 2. Configure Redis connection using the centralized Config
redis_url = Config.REDIS_URL
# The queue name should also come from the centralized config
queue_name = Config.RQ_QUEUE_NAME 

conn = Redis.from_url(redis_url)

# Set up logging within the application context
with app.app_context():
    app.logger.setLevel(logging.INFO)
    app.logger.info(f"Worker connecting to Redis at {redis_url}")

# --- Background Task Functions ---

def generate_pdf_report(report_id: int) -> bytes | None:
    """
    Generates the PDF content for a given report ID.
    Must be run inside the Flask app context.
    """
    with app.app_context():
        report = AuditReport.query.get(report_id)
        if not report:
            app.logger.error(f"PDF generation failed: Report {report_id} not found.")
            return None
        
        try:
            # Safely load the JSON data
            metrics_data = json.loads(report.metrics_json)
        except json.JSONDecodeError:
            app.logger.error(f"Invalid metrics JSON for report {report_id}")
            metrics_data = {}

        try:
            # 1. Render the HTML template
            html_content = render_template(
                'report_pdf.html', 
                report=report, 
                data=metrics_data  # Pass the loaded dict directly
            )
            
            # 2. Convert HTML string to PDF bytes
            pdf_bytes = HTML(string=html_content).write_pdf()
            app.logger.info(f"PDF content successfully generated for report {report_id}.")
            return pdf_bytes
            
        except Exception as e:
            app.logger.error(f"PDF generation failed for report {report_id}: {e}", exc_info=True)
            return None


def send_report_email(report_id: int, recipient_email: str):
    """
    Retrieves the report, generates the PDF, and sends it via email.
    This is the primary function to be enqueued by the application.
    """
    with app.app_context():
        report = AuditReport.query.get(report_id)
        if not report:
            app.logger.error(f"Email task failed: Report {report_id} not found.")
            return

        app.logger.info(f"Starting email process for report {report_id} to {recipient_email}")
        
        # 1. Generate PDF content
        pdf_bytes = generate_pdf_report(report_id)
        
        # 2. Construct the email message
        msg = Message(
            subject=f"WebAudit Report: {report.website_url}",
            recipients=[recipient_email],
            body=f"Dear User,\n\nYour comprehensive audit report for {report.website_url} is attached. \n\nThank you.",
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        # 3. Attach the PDF
        if pdf_bytes:
            msg.attach(
                filename=f"WebAudit_Report_{report_id}.pdf", 
                content_type="application/pdf", 
                data=pdf_bytes
            )
        else:
            # Send a notification email if PDF failed
            msg.body = "Your audit report is ready, but PDF generation failed. Please check the website."
            
        # 4. Send the email
        try:
            mail.send(msg)
            app.logger.info(f"Email successfully sent for report {report_id} to {recipient_email}")
        except Exception as e:
            app.logger.error(f"Failed to send email for report {report_id}: {e}", exc_info=True)

# --- Worker Main Execution Block ---

if __name__ == "__main__":
    app.logger.info("Starting RQ Worker process...")
    
    # We pass the functions the worker needs to be aware of
    # The worker listens to the queue name defined in config.py
    with Connection(conn):
        worker = Worker(
            [queue_name], 
            connection=conn, 
            default_timeout=Config.MAX_AUDIT_TIMEOUT # Use the timeout from config
        )
        # Start consuming jobs from the queue
        worker.work(logging=True)
