import functools

from ._private.consts import DEFAULT_QUEUE, MAX_RESTARTS, RESTART_DELAY
from ._private.utils import serialize_object, get_func_path

from .models import Status, TaskModel


def task(queue = DEFAULT_QUEUE, max_restarts = MAX_RESTARTS, restart_delay = RESTART_DELAY):
    def decorator(func):
        def schedule(*args, **kwargs):
            func_name = get_func_path(func)
            serialized_params = serialize_object({"args": args, "kwargs": kwargs})

            return TaskModel.objects.create(
                func_name=func_name,
                raw_params=serialized_params,
                queue=queue,
                status=Status.CREATED,
                restart_delay=restart_delay,
                max_restarts=max_restarts
            )
        func.schedule = schedule

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def atask(queue = DEFAULT_QUEUE, max_restarts = MAX_RESTARTS, restart_delay = RESTART_DELAY):
    def decorator(func):
        def schedule(*args, **kwargs):
            func_name = get_func_path(func)
            serialized_params = serialize_object({"args": args, "kwargs": kwargs})

            return TaskModel.objects.create(
                func_name=func_name,
                raw_params=serialized_params,
                queue=queue,
                status=Status.CREATED,
                restart_delay=restart_delay,
                max_restarts=max_restarts
            )
        func.schedule = schedule

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator
