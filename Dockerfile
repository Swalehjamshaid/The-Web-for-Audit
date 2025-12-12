# 6. APPLICATION ENTRYPOINT (This is the final, confirmed fix)
# The format is <file_name>:<callable_name>
# Your file is 'app.py' and your callable is 'application = create_app()'
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:application"]
