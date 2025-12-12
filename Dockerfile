# ... (Previous steps for FROM, RUN apt-get, WORKDIR, COPY requirements.txt, RUN pip install, COPY .)

# 6. APPLICATION ENTRYPOINT (This is where the fix is needed)
# REPLACE 'your_project_name' with the actual name of your folder containing wsgi.py
# Example: If your folder is named 'web_for_audit', use 'web_for_audit.wsgi'

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "your_actual_project_name_here.wsgi"]
