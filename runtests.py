from pathlib import Path
import sys

import django
from django.conf import settings
from django.test.utils import get_runner

def run_tests():
    settings.configure(
        BASE_DIR = Path(__file__).resolve().parent,

        DEFAULT_QUEUE = "default",
        MAX_RESTARTS = 5,
        RESTART_DELAY = 120,
        FAIL_SILENTLY = True,
        CONSUMER_NAP_TIME = 0.1,
        
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django_simple_tasks',
            'tests',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        SECRET_KEY='abc123',
        MIDDLEWARE=[],
    )
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests"])
    sys.exit(bool(failures))

if __name__ == "__main__":
    run_tests()
