import asyncio
import base64
import inspect
import logging
import pickle
from datetime import datetime

from django.conf import settings
from django.db.models import Case, IntegerField, Value, When

logger = logging.getLogger("django_firefly_tasks")


def serialize_object(any) -> str:
    """
    Takes object, pickles it to bytes and then hash it using base64.
    It's recommend to keep obj as small as possible,
    because base64 is memory expensive.
    """
    message_bytes = pickle.dumps(any)
    base64_bytes = base64.b64encode(message_bytes)
    txt = base64_bytes.decode("ascii")
    return txt


def deserialize_object(any: str):
    """
    Takes string, depickles it.
    """
    base64_bytes = any.encode("ascii")
    message_bytes = base64.b64decode(base64_bytes)
    obj = pickle.loads(message_bytes)
    return obj


def get_func_path(func):
    """
    Gets function path in dot notation relative to project aka myapp.myview.myfunction
    """
    module = inspect.getmodule(func)
    base_dir = str(settings.BASE_DIR).replace("/", ".")

    module_name = module.__file__.replace("/", ".").rstrip(".py")
    module_name = module_name.replace(base_dir, "")[1:]

    qualname = func.__qualname__
    return f"{module_name}.{qualname}"


def is_async(func):
    return asyncio.iscoroutinefunction(func)


def get_latest_task(queue: str):
    """
    Get latest task. Sorts by not_before; first null rows, than asc.
    Select for update is used to create database lock for task to prevent race conditions
    """
    from django_firefly_tasks.models import Status, TaskModel

    return (
        TaskModel.objects.select_for_update()
        .annotate(
            not_before_null=Case(
                When(not_before=None, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .filter(queue=queue, status=Status.CREATED)
        .order_by("not_before_null", "not_before", "pk")
        .first()
    )


def get_eta(kwargs: dict) -> datetime | None:
    eta = kwargs.pop("eta", None)

    if eta and not isinstance(eta, datetime):
        raise TypeError("'eta' have should be datetime")

    return eta
