# scheduler.py — Always-on process (Railway worker service)
import time
from datetime import datetime

print(f"[{datetime.utcnow()}] Scheduler started — running 24/7")

while True:
    print(f"[{datetime.utcnow()}] Scheduler heartbeat — alive")
    time.sleep(86400)  # 24 hours
