import time

from django.db import transaction

from .consts import CONSUMER_NAP_TIME, FAIL_SILENTLY
from .processors import task_processor
from .utils import get_latest_task


def task_consumer(queue: str):
    """
    Task consumer, it's consuming tasks :) Supports both sync and async function.
    """

    while True:
        time.sleep(CONSUMER_NAP_TIME)

        error = None

        with transaction.atomic():
            task = get_latest_task(queue)
            try:
                task_processor(task)
            except Exception as err:
                error = err

        if not FAIL_SILENTLY and error:
            raise error
