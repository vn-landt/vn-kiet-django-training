import os
import sys
import types
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
# ---- fix sandbox modules ----
fake_subprocess = types.ModuleType("subprocess")
sys.modules["subprocess"] = fake_subprocess


# ---- fake django file locks ----
fake_locks = types.ModuleType("locks")

def lock(f, flags):
    return True

def unlock(f):
    return True

fake_locks.lock = lock
fake_locks.unlock = unlock

sys.modules["django.core.files.locks"] = fake_locks

import django.core.files
django.core.files.locks = fake_locks


# ---- set Django settings ----
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "img2xl_project.settings")


# ---- setup Django ----
import django
django.setup()


# ---- start WSGI ----
from django.core.handlers.wsgi import WSGIHandler
application = django.core.handlers.wsgi.WSGIHandler()