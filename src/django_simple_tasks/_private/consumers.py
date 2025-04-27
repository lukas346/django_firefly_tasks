import time

from django.db import transaction
from django.db.models import BooleanField, ExpressionWrapper, Q

from ..models import TaskModel, Status

from .consts import FAIL_SILENTLY, CONSUMER_NAP_TIME
from .processors import task_processor


def task_consumer(queue: str):
    """
    Task consumer, it's consuming tasks :) Supports both sync and async function.
    """

    while True:
        time.sleep(CONSUMER_NAP_TIME)

        error = None

        with transaction.atomic():
            # select_for_update => creates database lock for task to prevent race conditions
            # sorts by not_before; first null rows, than asc
            task = (TaskModel.objects.select_for_update()
                    .annotate(is_null=ExpressionWrapper(Q(not_before__isnull=True), output_field=BooleanField()))
                    .filter(queue=queue, status=Status.CREATED).order_by('is_null', 'not_before')
                    .first()
            )
            try:
                task_processor(task)
            except Exception as err:
                error = err

        if not FAIL_SILENTLY and error:
            raise error
