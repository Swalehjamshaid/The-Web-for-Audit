import os
import json
from flask import render_template
from redis import Redis
from rq import Queue, Worker, Connection
from weasyprint import HTML
from flask_mail import Message
from app import app, mail, AuditReport

app.app_context().push()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
conn = Redis.from_url(redis_url)
queue_name = os.getenv("RQ_QUEUE", "default")
queue = Queue(queue_name, connection=conn)

def get_pdf_content(report_id):
    report = AuditReport.query.get(report_id)
    if not report:
        app.logger.error(f"Report {report_id} not found.")
        return None
    try:
        metrics = json.loads(report.metrics_json)
    except json.JSONDecodeError:
        app.logger.error(f"Invalid JSON for report {report_id}")
        metrics = {}
    try:
        html = render_template('report_pdf.html', report=report, data={"metrics": metrics})
        return HTML(string=html).write_pdf()
    except Exception as e:
        app.logger.error(f"PDF generation failed for report {report_id}: {e}")
        return None

def send_report_email(report_id, email):
    report = AuditReport.query.get(report_id)
    if not report:
        app.logger.error(f"Report {report_id} not found for email.")
        return
    pdf = get_pdf_content(report_id)
    msg = Message(
        subject=f"WebAudit Report: {report.website_url}",
        recipients=[email],
        body="Your audit report is attached."
    )
    if pdf:
        msg.attach(f"report_{report_id}.pdf", "application/pdf", pdf)
    try:
        mail.send(msg)
        app.logger.info(f"Email sent for report {report_id} to {email}")
    except Exception as e:
        app.logger.error(f"Failed to send email for report {report_id} to {email}: {e}")

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker([queue])
        worker.work(logging=True)
