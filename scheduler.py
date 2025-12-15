import os
import sys
from datetime import datetime
from redis import Redis
from rq_scheduler import Scheduler

# Add the application directory to the path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Configuration & Imports ---
# We need to explicitly import the configuration to get the REDIS_URL and queue name
try:
    from app.config import Config # Assuming you use the Config class from app/config.py
    # Also import the function you want to schedule (assuming it's in audit_service)
    # from app.audit_service import AuditService 
except ImportError:
    print("FATAL: Could not import configuration. Ensure scheduler.py is run from the project root or configure paths correctly.")
    sys.exit(1)

# --- Define the Scheduled Task ---

# Placeholder function that will be scheduled. 
# In a real app, this would enqueue a job to run an audit.
def scheduled_daily_task(target_url="https://example.com/"):
    """
    The function that gets executed by the scheduler at the specified interval.
    This should enqueue the actual audit job to the worker queue.
    """
    print(f"[{datetime.utcnow()}] SCHEDULED TASK FIRED: Enqueueing daily audit for {target_url}...")
    
    # Example: Replace this with your actual job enqueuing logic
    # from rq import Queue
    # from app.audit_service import AuditService
    # q = Queue(Config.RQ_QUEUE_NAME, connection=redis_conn)
    # q.enqueue(AuditService.run_audit, target_url)


def main():
    """
    Initializes and starts the RQ Scheduler.
    """
    print(f"[{datetime.utcnow()}] Scheduler initializing...")
    
    # 1. Connect to Redis using the URL from Config
    try:
        redis_conn = Redis.from_url(Config.REDIS_URL)
        redis_conn.ping()
        print(f"[{datetime.utcnow()}] Successfully connected to Redis at {Config.REDIS_URL}")
    except Exception as e:
        print(f"FATAL: Could not connect to Redis: {e}")
        sys.exit(1)

    # 2. Initialize the Scheduler
    scheduler = Scheduler(
        connection=redis_conn,
        # Scheduler targets the same queue the worker is listening to
        queue_name=Config.RQ_QUEUE_NAME 
    )

    # 3. Schedule the recurring job
    # Jobs are scheduled by their Python path (e.g., 'scheduler.scheduled_daily_task')
    
    # Clear any previously scheduled jobs to prevent duplicates on restart
    for job in scheduler.get_jobs():
        scheduler.cancel(job)
    print(f"[{datetime.utcnow()}] Cleared {len(scheduler.get_jobs())} old jobs.")


    # --- Schedule Jobs Here ---
    
    # Example: Schedule a task to run every 24 hours (1 day)
    scheduler.schedule(
        scheduled_at=datetime.utcnow(),      # Time to run the job next
        func=scheduled_daily_task,           # Function to call (defined above)
        args=('https://my-production-site.com/',), # Arguments passed to the function
        interval=86400,                      # Time in seconds (24 hours)
        repeat=None,                         # Run forever
        timeout=Config.MAX_AUDIT_TIMEOUT     # Use the timeout from config
    )
    
    print(f"[{datetime.utcnow()}] 1 task successfully scheduled for daily execution.")


    # 4. The main process loop (RQ-Scheduler doesn't require an infinite loop like the old file)
    # Since we are running this script directly on Railway, we just need to confirm it scheduled the jobs.
    # We will rely on the Railway deployment hook to run this script once.
    print(f"[{datetime.utcnow()}] Scheduler setup complete. Jobs are persisted in Redis.")


if __name__ == '__main__':
    # When this file is run via `python scheduler.py` on Railway, 
    # it initializes the jobs in Redis.
    main()
