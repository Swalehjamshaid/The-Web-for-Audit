# scheduler.py

import time
import sys

# This process simply keeps the scheduler process alive on Railway without crashing.
# Actual scheduling logic is handled by external tools (or manually in this setup).

print("INFO: Scheduler process started. It is currently in passive mode.")

# Keep the process alive indefinitely (sleeps for 24 hours per loop)
try:
    while True:
        time.sleep(86400) 
except KeyboardInterrupt:
    print("Scheduler process shut down.")
    sys.exit(0)
