# worker.py — RQ Worker + PDF generation + Email
from app import app, db, mail, AuditReport, User
from weasyprint import HTML
from flask import render_template
from redis import Redis
from rq import Queue, Worker, Connection
import os, json

app.app_context().push()
redis_url = os.getenv("REDIS_URL")
conn = Redis.from_url(redis_url)
queue = Queue("default", connection=conn)

def get_pdf_content(report_id):
    report = AuditReport.query.get(report_id)
    if not report: return None
    metrics = json.loads(report.metrics_json)
    html = render_template('report_pdf.html', report=report, data={"metrics": metrics})
    return HTML(string=html).write_pdf()

def send_report_email(report_id, email):
    report = AuditReport.query.get(report_id)
    pdf = get_pdf_content(report_id)
    from flask_mail import Message
    msg = Message(f"WebAudit Report: {report.website_url}", recipients=[email])
    msg.body = "Your audit report is attached."
    if pdf:
        msg.attach(f"report_{report_id}.pdf", "application/pdf", pdf)
    mail.send(msg)

if __name__=="__main__":
    with Connection(conn):
        worker = Worker([queue])
        worker.work()
