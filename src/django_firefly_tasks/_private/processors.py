from asgiref.sync import async_to_sync
from django.db import transaction
from django.utils.module_loading import import_string

from ..models import TaskModel
from .consts import FAIL_SILENTLY
from .utils import is_async, logger, serialize_object


def task_processor(task: TaskModel | None):
    if not task:
        return

    logger.info(f"[Task #{task.pk}] Processing")

    if task.is_postponed():
        logger.info(f"[Task #{task.pk}] It's postponed to {task.not_before}")
        return

    func = import_string(task.func_name)
    params = task.params

    # creates savepoint/subtransaction to isolate function from task logic
    sid = transaction.savepoint()
    try:
        if is_async(func):
            returned = async_to_sync(func)(*params["args"], **params["kwargs"])
        else:
            returned = func(*params["args"], **params["kwargs"])
    except Exception as error:
        # if something in function fails rollback to state before calling it
        transaction.savepoint_rollback(sid)

        logger.info(f"[Task #{task.pk}] Error raised: {str(error)}")

        if task.can_be_restarted():
            task.setup_for_restart()
            task.save()
        if task.retry_attempts == task.max_retries:
            task.set_as_failed()
            task.save()

            logger.info(f"[Task #{task.pk}] Changed status to {task.status}")

            if not FAIL_SILENTLY:
                raise
    else:
        transaction.savepoint_commit(sid)

        task.raw_returned = serialize_object(returned) if returned else None
        task.set_as_completed()
        task.save()

        logger.info(f"[Task #{task.pk}] Changed status to {task.status}")
