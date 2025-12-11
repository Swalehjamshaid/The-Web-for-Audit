web: sh -c "PYTHONPATH=. gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 180 --log-level info"
worker: sh -c "PYTHONPATH=. python worker.py"
scheduler: python scheduler.py
