#!/usr/bin/env python3
"""
WSGI konfiguracija za PythonAnywhere deployment
"""

import sys
import os

# Dodaj putanju do aplikacije
path = '/home/gostincar/ekgsignals'  # Zameniti sa stvarnom putanjom
if path not in sys.path:
    sys.path.append(path)

from app import create_app

# Kreiranje Flask aplikacije
application = create_app()

if __name__ == "__main__":
    application.run(debug=False)