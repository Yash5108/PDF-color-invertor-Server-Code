# $HOME/pdf_inverter/wsgi.py
import sys
import os

# The absolute path to your application folder in Termux
app_dir = '/data/data/com.termux/files/home/pdf_inverter' 

# Add the application directory to the system path
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import the application instance from app.py
from app import app as application
