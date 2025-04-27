from django.conf import settings


DEFAULT_QUEUE = settings.DEFAULT_QUEUE if hasattr(settings, "DEFAULT_QUEUE") else "default"
MAX_RESTARTS = settings.MAX_RESTARTS if hasattr(settings, "MAX_RESTARTS") else 0
RESTART_DELAY = settings.RESTART_DELAY if hasattr(settings, "RESTART_DELAY") else 120
FAIL_SILENTLY = settings.FAIL_SILENTLY if hasattr(settings, "FAIL_SILENTLY") else True
CONSUMER_NAP_TIME = settings.CONSUMER_NAP_TIME if hasattr(settings, "CONSUMER_NAP_TIME") else 0.1
