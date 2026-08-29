"""
Vercel entrypoint for the Django app.

Vercel's Python runtime looks for a WSGI/ASGI callable inside /api. This file
just points at the existing Django WSGI application in config/wsgi.py, so
nothing about the Django project itself has to change to run on Vercel.
"""

import os
import sys
from pathlib import Path

# Make the project root (one level up from /api) importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
