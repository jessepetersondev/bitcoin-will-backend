import os
import sys
# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

# This is the WSGI callable that Gunicorn will use
application = app

if __name__ == "__main__":
    app.run()

