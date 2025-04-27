from django.conf import settings

DEFAULT_QUEUE = settings.DEFAULT_QUEUE if hasattr(settings, "DEFAULT_QUEUE") else "default"
MAX_RETRIES = settings.MAX_RETRIES if hasattr(settings, "MAX_RETRIES") else 0
RETRY_DELAY = settings.RETRY_DELAY if hasattr(settings, "RETRY_DELAY") else 120
FAIL_SILENTLY = settings.FAIL_SILENTLY if hasattr(settings, "FAIL_SILENTLY") else True
CONSUMER_NAP_TIME = settings.CONSUMER_NAP_TIME if hasattr(settings, "CONSUMER_NAP_TIME") else 0.001
