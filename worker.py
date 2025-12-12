# worker.py — RQ Worker + Email + Scheduled Audits
from app import app, db, mail, AuditReport, User, AuditService
from weasyprint import HTML, CSS
from flask import render_template
from redis import Redis
from rq import Queue, Worker, Connection
import os
import json
from datetime import datetime

app.app_context().push()
redis_url = os.getenv("REDIS_URL")
conn = Redis.from_url(redis_url)
queue = Queue("default", connection=conn)

def get_pdf_content(report_id):
    report = AuditReport.query.get(report_id)
    if not report: return None
    metrics = json.loads(report.metrics_json)
    scores = AuditService.calculate_score(metrics)['all_scores']
    html = render_template('report_pdf.html', report=report, metrics=metrics, scores=scores)
    return HTML(string=html).write_pdf()

def send_report_email(report_id, email):
    report = AuditReport.query.get(report_id)
    pdf = get_pdf_content(report_id)
    msg = Message(f"WebAudit Report: {report.website_url}", recipients=[email])
    msg.body = "Your audit report is attached."
    if pdf:
        msg.attach(f"report_{report_id}.pdf", "application/pdf", pdf)
    mail.send(msg)

def run_scheduled_report(user_id):
    user = User.query.get(user_id)
    if not user or not user.scheduled_website: return
    # Run audit + save + email (same logic as run_audit route)
    ...

if __name__ == "__main__":
    print("RQ Worker starting...")
    with Connection(conn):
        worker = Worker([queue])
        worker.work()
