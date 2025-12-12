# worker.py

import os
import json
from datetime import datetime
from flask import render_template
from flask_mail import Message
# Ensure these imports match your app.py structure
from app import app, db, AuditReport, User, AuditService, mail 
from redis import Redis
from rq import Worker, Connection

# --- Worker Functions (Used by both app.py and worker.py) ---

def get_pdf_content(report_id):
    """Generates the PDF binary content for attachment or download."""
    from weasyprint import HTML, CSS 
    
    with app.app_context():
        report = AuditReport.query.get(report_id)
        if not report:
            return None
        
        # Prepare data for report_pdf.html
        metrics_data = json.loads(report.metrics_json)
        scores_data = AuditService.calculate_score(metrics_data)
        scores_full = scores_data['all_scores']
        metrics_by_cat = {cat: {k: metrics_data.get(k, 'N/A') for k in items} 
                          for cat, items in AuditService.METRICS.items()}
        
        # Render the HTML template (ensure report_pdf.html exists!)
        html_content = render_template('report_pdf.html', 
                                       report=report, 
                                       metrics=metrics_by_cat, 
                                       scores=scores_full)
        
        try:
            # Generate the PDF binary data
            pdf_data = HTML(string=html_content).write_pdf(
                stylesheets=[CSS(string='@page { size: A4; margin: 2cm } body { font-family: sans-serif; }')]
            )
            return pdf_data
        except Exception as e:
            print(f"ERROR: Failed to generate PDF in worker for report {report_id}: {e}")
            return None


def send_report_email(report_id, recipient_email):
    """Sends a completed report (with PDF attached) immediately."""
    with app.app_context():
        report = AuditReport.query.get(report_id)
        if not report:
            print(f"Report {report_id} not found.")
            return

        pdf_attachment = get_pdf_content(report_id)
        
        msg = Message(
            subject=f"FF Tech WebAudit Report: {report.website_url}",
            recipients=[recipient_email],
            body=f"Your latest website audit for {report.website_url} is attached.\nPerformance: {report.performance_score}%, Security: {report.security_score}%, Accessibility: {report.accessibility_score}%.",
        )

        if pdf_attachment:
            msg.attach(f"audit_report_{report.id}.pdf", "application/pdf", pdf_attachment)
        else:
             print(f"Warning: PDF attachment failed for report {report_id}. Sending email without PDF.")

        try:
            mail.send(msg)
            print(f"Report {report_id} emailed successfully to {recipient_email}")
        except Exception as e:
            print(f"Failed to send email for report {report_id}: {e}")

def run_scheduled_report(user_id):
    """Runs a full audit, saves it, and then emails it (used for immediate test)."""
    with app.app_context():
        user = User.query.get(user_id)
        if not user or not user.scheduled_website or not user.scheduled_email:
            print(f"Skipping scheduled run for user {user_id}: missing schedule info.")
            return

        # 1. Run Audit
        url = user.scheduled_website
        result = AuditService.run_audit(url)
        detailed_metrics = result['metrics']
        
        # 2. Calculate Score
        scores_data = AuditService.calculate_score(detailed_metrics)
        
        # 3. Save Report
        report = AuditReport(
            website_url=url,
            performance_score=scores_data['performance'],
            security_score=scores_data['security'],
            accessibility_score=scores_data['accessibility'],
            metrics_json=json.dumps(scores_data['metrics']),
            user_id=user.id
        )
        db.session.add(report)
        db.session.commit()
        
        # 4. Email Report
        send_report_email(report.id, user.scheduled_email)
        print(f"Scheduled report processed for user {user.email}.")


# --- RQ Worker Entry Point ---

if __name__ == '__main__':
    # Ensure this points to your Railway Redis instance
    redis_conn = Redis.from_url(os.getenv('REDIS_URL') or os.getenv('REDIS_RAILWAY', 'redis://localhost:6379'))
    print("Starting RQ Worker...")
    with Connection(redis_conn):
        # The worker will listen to the 'default' queue
        worker = Worker(['default'], connection=redis_conn)
        worker.work()
